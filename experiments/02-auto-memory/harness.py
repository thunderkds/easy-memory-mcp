"""Experiment 02: automatic save + pick + hook delivery of session memory.

For each repo and rep, two sequences run side by side on their own copies:
  cold — the hook is installed but injects nothing (mode off);
  auto — after each session its final answer is saved; the hook picks
         memories for the next prompt and flags files changed since saving.
Between the b- and c-sessions the code changes in changes.py are applied.
On the changed topics' c-sessions a third run, noflag, uses the auto store
without the changed-file note.

Usage: harness.py run [reps]   |   harness.py copy <repo> <dest>
"""
import json
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import changes  # noqa: E402
import memstore  # noqa: E402
import tasks  # noqa: E402

HERE = Path(__file__).resolve().parent
WORK = HERE / "work"          # repo copies + stores (gitignored via results/)
RESULTS = HERE / "results"
SOURCES = {
    "tapchat": Path.home() / "workspace/project/beautifly/github/tapchat-apis",
    "orderly": Path.home() / "workspace/project/phanpy/orderly",
}
MODEL, EFFORT = "sonnet", "medium"
SLOTS = threading.Semaphore(8)  # concurrent agent runs


def _excluded(path):
    """Agent instruction files would steer both conditions; leave them out."""
    parts = Path(path).parts
    name = parts[-1]
    return (bool({".claude", ".agents"} & set(parts)) or name == "AGENTS.md"
            or name == ".mcp.json" or (name.startswith("CLAUDE") and name.endswith(".md")))


def copy(repo, dest):
    """Copy the git-tracked files only (what a teammate's checkout holds)."""
    listed = subprocess.run(["git", "ls-files", "-z"], cwd=SOURCES[repo],
                            capture_output=True, check=True).stdout.split(b"\0")
    keep = [f for f in listed if f and not _excluded(f.decode())]
    Path(dest).mkdir(parents=True, exist_ok=True)
    subprocess.run(["rsync", "-a", "--from0", "--files-from=-", f"{SOURCES[repo]}/",
                    f"{dest}/"], input=b"\0".join(keep), check=True)


def settings(store, mode, log, seq):
    cmd = (f"python3 -I {HERE / 'memory_hook.py'} --store {store} --mode {mode} "
           f"--log {log} --seq {seq} --idf {Path(store).parent / 'idf.json'}")
    return json.dumps({"hooks": {"UserPromptSubmit": [
        {"hooks": [{"type": "command", "command": cmd}]}]}})


def run(label, cwd, prompt, store, mode, seq):
    out = RESULTS / f"{label}.json"
    if out.exists():
        data = json.loads(out.read_text())
        if not data.get("is_error"):  # rerun failed runs (e.g. usage limit)
            return data
    log = RESULTS / f"{label}.hook.jsonl"
    log.unlink(missing_ok=True)
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--model", MODEL,
           "--effort", EFFORT, "--setting-sources", "project",
           "--settings", settings(store, mode, log, seq), "--strict-mcp-config",
           "--tools", "Read,Grep,Glob", "--permission-prompts", "none",
           "--no-session-persistence", "--max-budget-usd", "3"]
    t0 = time.time()
    with SLOTS:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=1800)
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = {"is_error": True, "raw": proc.stdout[-2000:], "stderr": proc.stderr[-2000:]}
    data.update(_label=label, _wall_s=round(time.time() - t0, 1), _cwd=str(cwd),
                _mode=mode, _seq=seq)
    out.write_text(json.dumps(data, indent=1))
    u = data.get("usage") or {}
    print(f"done {label}: in={sum(u.get(k, 0) for k in ('input_tokens', 'cache_creation_input_tokens', 'cache_read_input_tokens'))} "
          f"out={u.get('output_tokens')} turns={data.get('num_turns')} err={data.get('is_error')}",
          flush=True)
    return data


def _failed(label):
    out = RESULTS / f"{label}.json"
    return not out.exists() or json.loads(out.read_text()).get("is_error")


def repair(repo, rep, base, roots, store):
    """Before a resume: drop memories saved from failed runs, and give back
    unchanged code to any sequence that still has pre-change sessions to run."""
    labels = tasks.sequence(repo)
    for seq, sid in enumerate(labels, 1):
        rec = store / f"{seq:03d}_{sid}.json"
        if rec.exists() and _failed(f"{repo}_r{rep}_auto_{seq:02d}_{sid}"):
            rec.unlink()
            print(f"repair: dropped memory {rec.name} ({repo}_r{rep})", flush=True)
    pre = [(seq, sid) for seq, sid in enumerate(labels, 1) if not sid.endswith("_c")]
    if any(_failed(f"{repo}_r{rep}_{c}_{s:02d}_{sid}") for s, sid in pre for c in ("cold", "auto")):
        for root in roots.values():
            if (root / ".changed").exists():
                subprocess.run(["rm", "-rf", str(root)], check=True)
                print(f"repair: recopied unchanged {root.name} ({repo}_r{rep})", flush=True)


def sequence(repo, rep):
    """One rep: cold and auto sequences in lockstep, noflag at changed c-sessions."""
    base = WORK / f"{repo}_r{rep}"
    roots = {m: base / f"repo_{m}" for m in ("cold", "auto")}
    store = base / "store_auto"
    if store.exists():
        repair(repo, rep, base, roots, store)
    for root in roots.values():
        if not root.exists():
            copy(repo, root)
    if not (base / "idf.json").exists():
        memstore.build_idf(roots["auto"], base / "idf.json")
    store = base / "store_auto"
    changed = False
    for seq, sid in enumerate(tasks.sequence(repo), 1):
        if sid.endswith("_c") and not changed:
            for root in roots.values():
                if not (root / ".changed").exists():
                    changes.__dict__[repo](root)
                    (root / ".changed").touch()
            changed = True
        prompt = tasks.PROMPTS[repo][sid] + tasks.SUFFIX
        jobs = [("cold", roots["cold"], "off"), ("auto", roots["auto"], "auto")]
        if sid.endswith("_c") and tasks.CHANGED[repo][sid[0]]:
            jobs.append(("noflag", roots["auto"], "noflag"))
        with ThreadPoolExecutor(len(jobs)) as ex:
            res = dict(zip([j[0] for j in jobs], ex.map(
                lambda j: run(f"{repo}_r{rep}_{j[0]}_{seq:02d}_{sid}", j[1], prompt,
                              store, j[2], seq), jobs)))
        ans = "" if res["auto"].get("is_error") else res["auto"].get("result") or ""
        if ans and not any(store.glob(f"{seq:03d}_*.json")):
            memstore.save(store, seq, sid, prompt, ans, roots["auto"])


def main():
    if sys.argv[1] == "copy":
        copy(sys.argv[2], Path(sys.argv[3]))
        return
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    RESULTS.mkdir(exist_ok=True)
    WORK.mkdir(exist_ok=True)
    plan = [(repo, rep) for rep in range(1, reps + 1) for repo in ("tapchat", "orderly")]
    with ThreadPoolExecutor(len(plan)) as ex:
        [f.result() for f in [ex.submit(sequence, *p) for p in plan]]


if __name__ == "__main__":
    main()
