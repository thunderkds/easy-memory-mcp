"""Grade experiment 02: tokens, accuracy, pick quality and stale traps."""
import json
import re
import statistics as st
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tasks  # noqa: E402

RESULTS = Path(__file__).resolve().parent / "results"
WORK = Path(__file__).resolve().parent / "work"
PRICE = (2e-6, 4e-6, 1e-7, 1e-5)  # Sonnet $/token, fitted in experiment 01
KEYS = ("input_tokens", "cache_creation_input_tokens", "cache_read_input_tokens",
        "output_tokens")
LABEL = re.compile(r"(\w+)_r(\d)_(cold|auto|noflag)_(\d\d)_(\w_\w)$")


def rows():
    for f in sorted(RESULTS.glob("*.json")):
        if f.name.endswith(".hook.jsonl"):
            continue
        d = json.loads(f.read_text())
        # Failed Claude invocations have no comparable token or accuracy
        # result. Keep them out of the metrics and report their count below.
        if d.get("is_error"):
            continue
        repo, rep, cond, seq, sid = LABEL.match(d["_label"]).groups()
        u = d.get("usage") or {}
        tok_in = sum(u.get(k, 0) for k in KEYS[:3])
        sc, misled = tasks.score(repo, sid, d.get("result"))
        hook = RESULTS / f"{d['_label']}.hook.jsonl"
        h = json.loads(hook.read_text().splitlines()[0]) if hook.exists() else {}
        yield dict(repo=repo, rep=int(rep), cond=cond, seq=int(seq), sid=sid,
                   tin=tok_in, tout=u.get("output_tokens", 0),
                   cost=sum(u.get(k, 0) * p for k, p in zip(KEYS, PRICE)),
                   turns=d.get("num_turns"), score=sc, misled=misled,
                   err=d.get("is_error"), chosen=h.get("chosen", []),
                   changed=h.get("changed", {}))


def main():
    data = list(rows())
    total = sum(1 for f in RESULTS.glob("*.json") if not f.name.endswith(".hook.jsonl"))
    errors = total - len(data)
    print(f"valid runs: {len(data)}/{total}, excluded errors: {errors}, "
          f"spend ${sum(r['cost'] for r in data):.2f} (valid runs only)\n")

    print("== Per sequence (9 sessions), median over reps ==")
    for repo in ("tapchat", "orderly"):
        for cond in ("cold", "auto"):
            reps = defaultdict(lambda: [0, 0, 0.0, 0.0])
            for r in data:
                if r["repo"] == repo and r["cond"] == cond:
                    a = reps[r["rep"]]
                    a[0] += r["tin"] + r["tout"]; a[1] += r["turns"] or 0
                    a[2] += r["cost"]; a[3] += r["score"]
            if not reps:
                continue
            m = lambda i: st.median(v[i] for v in reps.values())
            print(f"{repo:8} {cond:5} reps={len(reps)} tokens={m(0):>9,.0f} "
                  f"turns={m(1):>4.0f} cost=${m(2):.2f} score={m(3):.1f}/9")

    print("\n== By session round (median tokens per session) ==")
    for repo in ("tapchat", "orderly"):
        for rnd in "abc":
            line = []
            for cond in ("cold", "auto"):
                v = [r["tin"] + r["tout"] for r in data if r["repo"] == repo
                     and r["cond"] == cond and r["sid"].endswith(rnd)]
                s = [r["score"] for r in data if r["repo"] == repo
                     and r["cond"] == cond and r["sid"].endswith(rnd)]
                if v:
                    line.append(f"{cond} {st.median(v):>8,.0f} tok, score {sum(s):.1f}/{len(s)}")
            print(f"{repo:8} round {rnd}: " + " | ".join(line))

    print("\n== Per session (median tokens cold -> auto, scores) ==")
    for repo in ("tapchat", "orderly"):
        for sid in tasks.sequence(repo):
            cell = {}
            for cond in ("cold", "auto", "noflag"):
                rs = [r for r in data if r["repo"] == repo and r["sid"] == sid and r["cond"] == cond]
                if rs:
                    mis = sum(bool(r["misled"]) for r in rs)
                    cell[cond] = (f"{st.median(r['tin'] + r['tout'] for r in rs):>7,.0f} "
                                  f"s={sum(r['score'] for r in rs):.1f}/{len(rs)}"
                                  + (f" misled={mis}" if rs[0]["misled"] is not None else ""))
            print(f"{repo:8} {sid}: " + " | ".join(f"{k} {v}" for k, v in cell.items()))

    print("\n== Picks (auto runs) ==")
    for repo in ("tapchat", "orderly"):
        same = cross = none_when_rel = none_ok = 0
        for r in data:
            if r["repo"] != repo or r["cond"] != "auto":
                continue
            topic = r["sid"][0]
            rel_avail = r["sid"][-1] != "a"
            picked_same = [c for c in r["chosen"] if c[0] == topic]
            same += len(picked_same)
            cross += len(r["chosen"]) - len(picked_same)
            if not r["chosen"]:
                none_ok += not rel_avail
                none_when_rel += rel_avail
        print(f"{repo:8} same-topic picks={same} cross-topic picks={cross} "
              f"no pick when related existed={none_when_rel} correct no-pick={none_ok}")
        flagged = [(r["sid"], r["rep"], r["changed"]) for r in data
                   if r["repo"] == repo and r["cond"] == "auto" and any(r["changed"].values())]
        for f in flagged:
            print("   flagged:", f)


if __name__ == "__main__":
    main()
