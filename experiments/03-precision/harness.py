"""Experiment 03: precision variants of memory injection.

Reuses experiment 02: its tasks, code changes, round-a memories (saved before
any change, so their file hashes match unchanged code) and its cold runs as
the baseline. Each variant runs rounds b and c only.

Usage: harness.py run [reps]
"""
import json
import shutil
import subprocess
import sys
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

HERE = Path(__file__).resolve().parent
E2 = HERE.parent / "02-auto-memory"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(E2))
import changes  # noqa: E402
import harness as h2  # noqa: E402
import memstore  # noqa: E402
import precision  # noqa: E402
import tasks  # noqa: E402

WORK, RESULTS = HERE / "work", HERE / "results"
VARIANTS = ("facts", "judge", "index")
SLOTS = threading.Semaphore(8)


def settings(store, log, idf, variant):
    cmd = (f"python3 -I {HERE / 'hook.py'} --store {store} --log {log} "
           f"--idf {idf} --variant {variant}")
    return json.dumps({"hooks": {"UserPromptSubmit": [
        {"hooks": [{"type": "command", "command": cmd, "timeout": 150}]}]}})


def run(label, cwd, prompt, store, idf, variant, seq):
    out = RESULTS / f"{label}.json"
    if out.exists() and not json.loads(out.read_text()).get("is_error"):
        return json.loads(out.read_text())
    log = RESULTS / f"{label}.hook.jsonl"
    log.unlink(missing_ok=True)
    cmd = ["claude", "-p", prompt, "--output-format", "json", "--model", h2.MODEL,
           "--effort", h2.EFFORT, "--setting-sources", "project",
           "--settings", settings(store, log, idf, variant), "--strict-mcp-config",
           "--tools", "Read,Grep,Glob", "--permission-prompts", "none",
           "--no-session-persistence", "--max-budget-usd", "3"]
    t0 = time.time()
    with SLOTS:
        proc = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=1800)
    try:
        data = json.loads(proc.stdout)
    except json.JSONDecodeError:
        data = {"is_error": True, "raw": proc.stdout[-2000:], "stderr": proc.stderr[-2000:]}
    data.update(_label=label, _wall_s=round(time.time() - t0, 1), _variant=variant, _seq=seq)
    out.write_text(json.dumps(data, indent=1))
    print(f"done {label}: err={data.get('is_error')} turns={data.get('num_turns')}", flush=True)
    return data


def sequence(repo, rep, variant):
    base = WORK / f"{repo}_r{rep}_{variant}"
    root, store = base / "repo", base / "store"
    labels = tasks.sequence(repo)
    if not root.exists():
        h2.copy(repo, root)
        store.mkdir(parents=True)
        src = E2 / f"work/{repo}_r{rep}"
        shutil.copy(src / "idf.json", base / "idf.json")
        for seq, sid in enumerate(labels, 1):
            if sid.endswith("_a"):
                rec = src / f"store_auto/{seq:03d}_{sid}.json"
                shutil.copy(rec, store / rec.name)
                if variant == "index":
                    precision.write_memory_file(root, json.loads(rec.read_text()))
    for seq, sid in enumerate(labels, 1):
        if sid.endswith("_a"):
            continue
        if sid.endswith("_c") and not (root / ".changed").exists():
            changes.__dict__[repo](root)
            (root / ".changed").touch()
        d = run(f"{repo}_r{rep}_{variant}_{seq:02d}_{sid}", root,
                tasks.PROMPTS[repo][sid] + tasks.SUFFIX, store, base / "idf.json", variant, seq)
        ans = "" if d.get("is_error") else d.get("result") or ""
        if ans and not (store / f"{seq:03d}_{sid}.json").exists():
            rec = memstore.save(store, seq, sid, tasks.PROMPTS[repo][sid] + tasks.SUFFIX, ans, root)
            if variant == "index":
                precision.write_memory_file(root, rec)


def main():
    reps = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    RESULTS.mkdir(exist_ok=True)
    WORK.mkdir(exist_ok=True)
    plan = [(r, rep, v) for rep in range(1, reps + 1) for r in ("tapchat", "orderly") for v in VARIANTS]
    with ThreadPoolExecutor(len(plan)) as ex:
        [f.result() for f in [ex.submit(sequence, *p) for p in plan]]


if __name__ == "__main__":
    main()
