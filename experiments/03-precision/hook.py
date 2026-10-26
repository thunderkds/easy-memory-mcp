"""UserPromptSubmit hook for experiment 03: --variant facts|judge|index."""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import precision  # noqa: E402


def main():
    ap = argparse.ArgumentParser()
    for a in ("--store", "--log", "--idf", "--variant"):
        ap.add_argument(a, required=True)
    a = ap.parse_args()
    event = json.load(sys.stdin)
    prompt, root = event.get("prompt", ""), event.get("cwd", ".")
    fn = {"facts": precision.pick_facts, "judge": precision.pick_judge,
          "index": precision.pick_index}[a.variant]
    ctx, log = fn(a.store, prompt, root, a.idf)
    log.update(variant=a.variant, chars=len(ctx or ""))
    with open(a.log, "a") as fh:
        fh.write(json.dumps(log) + "\n")
    if ctx:
        print(json.dumps({"hookSpecificOutput": {
            "hookEventName": "UserPromptSubmit", "additionalContext": ctx}}))


if __name__ == "__main__":
    main()
