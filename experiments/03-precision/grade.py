"""Grade experiment 03 against experiment 02's cold and auto runs (rounds b+c)."""
import json
import re
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
E2 = HERE.parent / "02-auto-memory"
sys.path.insert(0, str(E2))
import tasks  # noqa: E402

KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens", "output_tokens")
PRICE = (2e-6, 4e-6, 1e-7, 1e-5)
LABEL = re.compile(r"(\w+?)_r(\d)_(\w+?)_(\d\d)_(\w_\w)$")


def tok(u):
    return sum((u or {}).get(k, 0) for k in KEYS)


def load(results, conds):
    out = {}
    for f in results.glob("*.json"):
        d = json.loads(f.read_text())
        m = LABEL.match(d.get("_label", ""))
        if not m or m.group(3) not in conds or m.group(5).endswith("_a") or d.get("is_error"):
            continue
        repo, rep, cond, seq, sid = m.groups()
        hook = results / f"{d['_label']}.hook.jsonl"
        h = json.loads(hook.read_text().splitlines()[0]) if hook.exists() else {}
        sc, misled = tasks.score(repo, sid, d.get("result"))
        out[(repo, int(rep), cond, sid)] = dict(
            tok=tok(d.get("usage")), cost=sum((d.get("usage") or {}).get(k, 0) * p for k, p in zip(KEYS, PRICE)),
            score=sc, misled=misled, chosen=h.get("chosen", []), chars=h.get("chars", 0),
            judge=sum(tok(u) for u in h.get("judge_usage", [])))
    return out


def main():
    data = {**load(E2 / "results", {"cold", "auto"}), **load(HERE / "results", {"facts", "judge", "index"})}
    conds = ("cold", "auto", "facts", "judge", "index")
    print("Rounds b+c (6 sessions) per sequence, median over reps; change vs cold\n")
    for repo in ("project-a", "project-b"):
        base = None
        for cond in conds:
            seqs = defaultdict(lambda: [0, 0.0, 0.0, 0, 0, 0])
            for (r, rep, c, sid), v in data.items():
                if r == repo and c == cond:
                    s = seqs[rep]
                    s[0] += v["tok"]; s[1] += v["cost"]; s[2] += v["score"]
                    s[3] += 1; s[4] += v["judge"]; s[5] += bool(v["misled"])
            full = [s for s in seqs.values() if s[3] == 6]
            if not full:
                continue
            m = lambda i: st.median(s[i] for s in full)
            base = m(0) if cond == "cold" else base
            print(f"{repo:8} {cond:6} reps={len(full)} tokens={m(0):>9,.0f} ({100 * (m(0) - base) / base:+.0f}%) "
                  f"cost=${m(1):.2f} score={m(2):.1f}/6 misled={sum(s[5] for s in full)}"
                  + (f" judge(haiku) tokens={m(4):,.0f}" if cond == "judge" else ""))
        print()
    print("Per session, median tokens (score sum over reps)")
    for repo in ("project-a", "project-b"):
        for sid in tasks.sequence(repo):
            if sid.endswith("_a"):
                continue
            cells = []
            for cond in conds:
                vs = [v for (r, _, c, s), v in data.items() if r == repo and c == cond and s == sid]
                if vs:
                    cells.append(f"{cond} {st.median(v['tok'] for v in vs):>7,.0f} ({sum(v['score'] for v in vs):.1f})")
            print(f"{repo:8} {sid}: " + " | ".join(cells))
    print("\nInjection: how often memory was injected, and median chars when injected")
    for repo in ("project-a", "project-b"):
        for cond in ("auto", "facts", "judge", "index"):
            vs = [v for (r, _, c, _), v in data.items() if r == repo and c == cond]
            inj = [v for v in vs if v["chosen"]]
            wrong = sum(1 for (r, _, c, sid), v in data.items() if r == repo and c == cond
                        for x in v["chosen"] if x[0] != sid[0])
            ch = [v["chars"] for v in inj if v["chars"]]
            print(f"{repo:8} {cond:6} injected {len(inj)}/{len(vs)} runs, wrong-topic items {wrong}"
                  + (f", median {st.median(ch):,.0f} chars" if ch else ""))


if __name__ == "__main__":
    main()
