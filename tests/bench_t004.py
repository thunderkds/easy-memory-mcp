"""HUN-77 (T004) latency benchmark for hook-prompt (AC9, NFR-001). Prints numbers only.

    python3 tests/bench_t004.py --repo PATH [--notes 200] [--runs 50]

Uses a temp EASY_MEMORY_HOME (deleted at the end), builds the repo's word
weights once in the foreground, writes synthetic notes whose words and cited
files come from the repo, then times hook-prompt as a fresh process per prompt.
The repo is only read. No word, file name or source text is printed, so a
private repo can be the target.
"""
import argparse
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPT = str(ROOT / "easy_memory.py")
sys.path.insert(0, str(ROOT))


def percentile(values, share):
    ordered = sorted(values)
    return ordered[min(len(ordered) - 1, int(round(share * (len(ordered) - 1))))]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", required=True)
    parser.add_argument("--notes", type=int, default=200)
    parser.add_argument("--runs", type=int, default=50)
    args = parser.parse_args()
    home = tempfile.mkdtemp(prefix="bench-t004-")
    os.environ["EASY_MEMORY_HOME"] = home
    import easy_memory  # after EASY_MEMORY_HOME is set
    try:
        start = time.perf_counter()
        subprocess.run([sys.executable, SCRIPT, "build-weights", "--repo", args.repo],
                       check=True, timeout=600)
        build_seconds = time.perf_counter() - start
        store = Path(home) / easy_memory.repo_key(args.repo)
        weights = easy_memory.load_weights(store / "weights.json")
        rng = random.Random(77)
        vocab = sorted(word for word, count in weights["df"].items() if count < 50)
        tracked = easy_memory._tracked_files(args.repo)
        for _ in range(args.notes):
            topic = rng.sample(vocab, 12)
            cites = rng.sample(tracked, 4)
            answer = "\n".join(
                " ".join(rng.choice(topic) if rng.random() < 0.3 else rng.choice(vocab)
                         for _ in range(40))
                for _ in range(10)) + "\n" + " ".join(cites)
            easy_memory.write_note(args.repo, {
                "prompt": " ".join(rng.sample(topic, 6)), "answer": answer,
                "time": "2026-10-28T00:00:00Z", "session_id": "bench",
                "files": easy_memory.cited_files(" ".join(cites), args.repo)})
        notes = easy_memory.read_notes(args.repo)
        timings, line_counts, sizes = [], [], []
        for run in range(args.runs):
            note = notes[rng.randrange(len(notes))]
            words = note["prompt"].split()[:4] + rng.sample(vocab, 4)  # half match, half noise
            stdin = json.dumps({"hook_event_name": "UserPromptSubmit", "cwd": args.repo,
                                "session_id": "bench", "prompt": " ".join(words)})
            start = time.perf_counter()
            res = subprocess.run([sys.executable, SCRIPT, "hook-prompt"], input=stdin,
                                 capture_output=True, text=True, timeout=30)
            timings.append(time.perf_counter() - start)
            text = (json.loads(res.stdout)["hookSpecificOutput"]["additionalContext"]
                    if res.stdout else "")
            line_counts.append(sum(line.startswith("- id ") for line in text.splitlines()))
            sizes.append(len(text))
        log = Path(home) / "hook.log"
        print(f"tracked_files={len(tracked)} weights_files={weights['n']} "
              f"weights_bytes={(store / 'weights.json').stat().st_size} "
              f"build_seconds={build_seconds:.1f}")
        print(f"notes={len(notes)} runs={args.runs} "
              f"p50={percentile(timings, 0.5):.3f}s p95={percentile(timings, 0.95):.3f}s "
              f"max={max(timings):.3f}s mean={sum(timings) / len(timings):.3f}s")
        print(f"runs_with_index={sum(1 for n in line_counts if n)} "
              f"lines_max={max(line_counts)} chars_max={max(sizes)} "
              f"hook_log_lines={len(log.read_text().splitlines()) if log.exists() else 0} "
              f"build_lock_left={(store / 'weights.lock').exists()}")
    finally:
        shutil.rmtree(home, ignore_errors=True)


if __name__ == "__main__":
    main()
