"""HUN-76 (T003) AC6: do compact word weights rank notes like the full weights?

Reads experiment 03's saved stores (work/<repo>_r<n>_<variant>/store/*.json holding
each session's prompt and answer, and idf.json holding the full word weights).
Those files quote private source code and are not in the repo, so this script
prints counts only, never text.

Usage: python3 tests/parity_t003.py [DATA_DIR] [--min-df N]
  DATA_DIR  experiment 03 folder (the one with work/). Default: $EASY_MEMORY_EXP03_DIR,
            else experiments/03-precision in this repo.
  --min-df  drop words found in fewer than N files from the full weights (default 2,
            the rule in easy_memory.MIN_FILES_PER_WORD).

For each store and each prompt it scores every other note with the full weights
(experiments/02-auto-memory/memstore.score) and with the compact weights
(easy_memory.score), as the hook does: score(prompt, note.prompt + "\\n" + note.answer).
Two candidate sets: "other" (all notes but the prompt's own) and "earlier" (only
notes saved before the prompt, as the hook would see them).

Pass: the set of notes scoring >= 0.12 is identical for >= 95% of (prompt, note)
pairs, and the top-5 order is identical for >= 90% of prompts, in both sets.
Exit 0 pass, 1 fail, 2 data missing.
"""
import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.dont_write_bytecode = True  # experiments/ is read-only evidence: no __pycache__ there
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "experiments" / "02-auto-memory"))

import easy_memory  # noqa: E402
import memstore  # noqa: E402

FLOOR = 0.12
TOP = 5
MIN_PAIR_AGREEMENT = 0.95
MIN_ORDER_AGREEMENT = 0.90


def load_stores(data_dir):
    """[(idf path, [note dict, ...] in seq order)] for every store with an idf.json."""
    stores = []
    for base in sorted((Path(data_dir) / "work").glob("*")):
        idf, folder = base / "idf.json", base / "store"
        if not idf.is_file() or not folder.is_dir():
            continue
        notes = [json.loads(p.read_text()) for p in sorted(folder.glob("*.json"))]
        if notes:
            stores.append((idf, notes))
    return stores


def ranked(scores):
    """Note positions, best score first; equal scores keep their order."""
    return sorted(range(len(scores)), key=lambda i: -scores[i])


def compare(stores, min_df):
    """Counts per candidate set: pairs, pairs agreeing on the floor, prompts, order and pick agreement."""
    sets = {name: dict(pairs=0, pair_ok=0, prompts=0, order_ok=0, pick_ok=0)
            for name in ("other", "earlier")}
    for idf, notes in stores:
        full_weights = json.loads(Path(idf).read_text())
        compact = {"n": full_weights["n"],
                   "df": {w: c for w, c in full_weights["df"].items() if c >= min_df}}
        docs = [note["prompt"] + "\n" + note["answer"] for note in notes]
        for j, note in enumerate(notes):
            full = memstore.score(note["prompt"], docs, idf)
            small = [easy_memory.score(note["prompt"], doc, compact) for doc in docs]
            for name, keep in (("other", [i for i in range(len(notes)) if i != j]),
                               ("earlier", list(range(j)))):
                if not keep:
                    continue
                tally = sets[name]
                for i in keep:
                    tally["pairs"] += 1
                    tally["pair_ok"] += (full[i] >= FLOOR) == (small[i] >= FLOOR)
                full_sub, small_sub = [full[i] for i in keep], [small[i] for i in keep]
                top_full, top_small = ranked(full_sub)[:TOP], ranked(small_sub)[:TOP]
                tally["prompts"] += 1
                tally["order_ok"] += top_full == top_small
                pick = lambda sub, top: [p for p in top if sub[p] >= FLOOR]  # noqa: E731
                tally["pick_ok"] += pick(full_sub, top_full) == pick(small_sub, top_small)
    return sets


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("data_dir", nargs="?",
                        default=os.environ.get("EASY_MEMORY_EXP03_DIR")
                        or str(ROOT / "experiments" / "03-precision"))
    parser.add_argument("--min-df", type=int, default=easy_memory.MIN_FILES_PER_WORD)
    args = parser.parse_args(argv)

    stores = load_stores(args.data_dir) if Path(args.data_dir).is_dir() else []
    if not stores:
        print(f"parity_t003: data missing: no experiment 03 stores (work/*/store + idf.json) "
              f"under {args.data_dir}. Pass the folder as an argument or set "
              f"EASY_MEMORY_EXP03_DIR (see the header of this script).", file=sys.stderr)
        return 2

    sets = compare(stores, args.min_df)
    passed = True
    print(f"stores: {len(stores)}, min-df: {args.min_df}, floor: {FLOOR}")
    for name, t in sets.items():
        pair_rate = t["pair_ok"] / t["pairs"]
        order_rate = t["order_ok"] / t["prompts"]
        ok = pair_rate >= MIN_PAIR_AGREEMENT and order_rate >= MIN_ORDER_AGREEMENT
        passed = passed and ok
        print(f"{name}: floor-set identical for {t['pair_ok']}/{t['pairs']} pairs "
              f"({pair_rate:.1%}, need {MIN_PAIR_AGREEMENT:.0%}); "
              f"top-{TOP} order identical for {t['order_ok']}/{t['prompts']} prompts "
              f"({order_rate:.1%}, need {MIN_ORDER_AGREEMENT:.0%}); "
              f"index pick identical for {t['pick_ok']}/{t['prompts']} prompts; "
              f"{'PASS' if ok else 'FAIL'}")
    print("PARITY " + ("PASS" if passed else "FAIL"))
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
