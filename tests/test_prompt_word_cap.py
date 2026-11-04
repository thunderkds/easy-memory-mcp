"""HUN-211: a prompt with more than PROMPT_MAX_WORDS distinct scorable words is scored on the
PROMPT_MAX_WORDS highest-weight words (ties: first appearance). At or under the cap nothing changes.

Every test uses a temp EASY_MEMORY_HOME; nothing touches the real ~/.easy-memory.
The 4,000-note probe is opt-in (HUN211_CAP_PROBE=1): it builds a big store and takes minutes
when the cap is missing.
"""
import filecmp
import json
import math
import os
import random
import statistics
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import easy_memory  # noqa: E402
from tests.test_t009_smoke import Sandbox  # noqa: E402

WEIGHTS = {"n": 40, "df": {"alpha": 1, "bravo": 2, "charlie": 5, "delta": 10, "echo": 20}}


def weight_of(word):
    return math.log((WEIGHTS["n"] + 1) / (WEIGHTS["df"].get(word, 0) + 1)) + 1


class PromptWeightCapTest(unittest.TestCase):
    def test_cap_is_a_positive_int(self):  # AC4
        self.assertIsInstance(easy_memory.PROMPT_MAX_WORDS, int)
        self.assertGreater(easy_memory.PROMPT_MAX_WORDS, 0)

    def test_under_or_at_cap_keeps_every_word(self):  # AC1
        prompt = "alpha bravo charlie delta echo zulu"
        full = easy_memory._prompt_weight(prompt, WEIGHTS)
        self.assertEqual(len(full), 6)
        for cap in (6, 7, 1000):
            with mock.patch.object(easy_memory, "PROMPT_MAX_WORDS", cap):
                self.assertEqual(easy_memory._prompt_weight(prompt, WEIGHTS), full)

    def test_over_cap_keeps_exactly_cap_highest_weights(self):  # AC2
        # weights: zulu/yankee/xray unknown (df 0, rarest), alpha 1, bravo 2, echo 20 (lowest)
        prompt = "echo alpha zulu bravo yankee xray"
        with mock.patch.object(easy_memory, "PROMPT_MAX_WORDS", 4):
            kept = easy_memory._prompt_weight(prompt, WEIGHTS)
        self.assertEqual(len(kept), 4)
        # df 0 words weigh most; alpha (df 1) and bravo (df 2) tie nothing; the lowest two go
        self.assertEqual(set(kept), {"zulu", "yankee", "xray", "alpha"})
        for word, value in kept.items():
            self.assertAlmostEqual(value, weight_of(word), places=12)

    def test_ties_go_to_first_appearance(self):  # AC2
        prompt = " ".join(["echo"] + [f"unseen{chr(97 + i)}" for i in range(10)])
        with mock.patch.object(easy_memory, "PROMPT_MAX_WORDS", 3):
            kept = easy_memory._prompt_weight(prompt, WEIGHTS)
        self.assertEqual(set(kept), {"unseena", "unseenb", "unseenc"})

    def test_repeat_does_not_count_as_a_new_word_or_move_first_appearance(self):  # AC2
        prompt = "zzzc zzzb zzza zzzb zzzc zzzd"
        with mock.patch.object(easy_memory, "PROMPT_MAX_WORDS", 3):
            kept = easy_memory._prompt_weight(prompt, WEIGHTS)
        self.assertEqual(set(kept), {"zzzc", "zzzb", "zzza"})

    def test_best_is_computed_over_kept_words_only(self):  # edge case
        prompt = "echo alpha zulu bravo yankee xray"
        with mock.patch.object(easy_memory, "PROMPT_MAX_WORDS", 4):
            # a note holding exactly the kept words scores a full 1.0 only if the denominator
            # counts the kept words and nothing else
            note = "zulu yankee xray alpha"
            self.assertAlmostEqual(easy_memory.score(prompt, note, WEIGHTS, k1=1e-9), 1.0, places=6)

    def test_kept_words_do_not_depend_on_hash_seed(self):  # AC2
        code = (
            "import sys; sys.path.insert(0, %r); import easy_memory as m; "
            "m.PROMPT_MAX_WORDS = 50; "
            "p = ' '.join('qq%%03d' %% i for i in range(300)) + ' alpha bravo'; "
            "w = m._prompt_weight(p, {'n': 40, 'df': {'alpha': 1, 'bravo': 2}}); "
            "print(sorted(w))") % str(ROOT)
        outs = set()
        for seed in ("0", "1", "12345"):
            env = {**os.environ, "PYTHONHASHSEED": seed}
            res = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True,
                                 env=env, check=True)
            outs.add(res.stdout)
        self.assertEqual(len(outs), 1)
        self.assertEqual(len(json.loads(outs.pop().replace("'", '"'))), 50)

    def test_plugin_copy_is_byte_identical(self):  # AC6
        self.assertTrue(filecmp.cmp(ROOT / "easy_memory.py", ROOT / "plugin" / "easy_memory.py",
                                    shallow=False))


class OverCapSearchTest(unittest.TestCase):
    """memory_search and the hook share _index_lines, so both get the cap (AC5)."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hun211-")).resolve()
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(self.tmp)]))
        self.home = self.tmp / "home"
        patcher = mock.patch.dict(os.environ, {"EASY_MEMORY_HOME": str(self.home)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        folder = self.home / easy_memory.repo_key(self.repo) / "notes"
        easy_memory._private_dir(folder)
        for i, text in enumerate(["alpha bravo rareword", "nothing relevant here at all"]):
            note_id = f"20261001T0000{i:05d}-{i:08x}"
            (folder / f"{note_id}.json").write_text(json.dumps({
                "v": 1, "id": note_id, "prompt": text, "answer": text,
                "time": "2026-10-01T00:00:00Z", "session_id": "s", "files": {}}), encoding="utf-8")

    def test_index_lines_scores_only_the_kept_words(self):  # AC5
        # 43 distinct words, cap 3: every score_with call gets a 3-word weight map.
        prompt = " ".join(f"fill{chr(97 + i // 26)}{chr(97 + i % 26)}" for i in range(40))
        prompt += " alpha bravo rareword"
        calls = []
        real = easy_memory._score_with

        def spy(weight, text, k1=1.2):
            calls.append(len(weight))
            return real(weight, text, k1)

        with mock.patch.object(easy_memory, "PROMPT_MAX_WORDS", 3), \
                mock.patch.object(easy_memory, "_score_with", spy):
            easy_memory._index_lines(prompt, self.repo, {"n": 40, "df": {}})
        self.assertTrue(calls)
        self.assertEqual(set(calls), {3})

    def test_tool_search_goes_through_the_cap(self):  # AC5
        prompt = " ".join(f"fill{chr(97 + i // 26)}{chr(97 + i % 26)}" for i in range(40))
        sizes = []
        real = easy_memory._score_with

        def spy(weight, text, k1=1.2):
            sizes.append(len(weight))
            return real(weight, text, k1)

        with mock.patch.object(easy_memory, "PROMPT_MAX_WORDS", 5), \
                mock.patch.object(easy_memory, "_score_with", spy):
            easy_memory._tool_search(self.repo, {"query": prompt})
        self.assertTrue(sizes)
        self.assertEqual(set(sizes), {5})


class OverCapProbeTest(Sandbox):
    """Opt-in: HUN211_CAP_PROBE=1. 4,000 notes, a 1.7 MB prompt of 150,000 distinct words."""

    NOTES = int(os.environ.get("HUN211_CAP_NOTES", "4000"))
    WORDS = 150_000
    RUNS = 3

    def make_store(self):
        self.switch_on()
        self.run_tool(["build-weights", "--repo", str(self.repo)])
        notes_dir = self.store_dir() / "notes"
        notes_dir.mkdir(mode=0o700)
        rng = random.Random(9)
        vocab = [f"word{i}" for i in range(3000)]
        for index in range(self.NOTES):
            note_id = f"20261001T000000{index % 1000:03d}-{index:08x}"
            answer = " ".join(rng.choice(vocab) for _ in range(250)) + " see src/auth.py"
            path = notes_dir / f"{note_id}.json"
            path.write_text(json.dumps({"v": 1, "id": note_id, "prompt": " ".join(rng.sample(vocab, 8)),
                                        "answer": answer, "time": "2026-10-01T00:00:00Z",
                                        "session_id": "s", "files": {"src/auth.py": "0" * 64}}),
                            encoding="utf-8")
            path.chmod(0o600)
        words = vocab + [f"pay{i:07d}" for i in range(self.WORDS - len(vocab))]
        rng.shuffle(words)
        return " ".join(words)

    def test_150k_word_prompt_finishes_under_1_second(self):  # AC3, AC5
        if not os.environ.get("HUN211_CAP_PROBE"):
            self.skipTest("probe: set HUN211_CAP_PROBE=1 to run (minutes without the cap)")
        prompt = self.make_store()
        self.assertGreater(len(prompt), 1_500_000)
        times = []
        for _ in range(self.RUNS):
            start = time.perf_counter()
            res = self.run_tool(["hook-prompt"], stdin=self.prompt_input(prompt=prompt), timeout=900)
            times.append(time.perf_counter() - start)
            self.assertEqual(res.returncode, 0, res.stderr)
        print(f"\n[HUN-211 cap probe] notes={self.NOTES} prompt={len(prompt):,} chars "
              f"words={self.WORDS:,} hook-prompt p50={statistics.median(times):.3f}s "
              f"max={max(times):.3f}s", file=sys.stderr)
        self.assertLess(max(times), 1.0, "NFR-001: hook-prompt must add at most 1 s")
        # AC5: memory_search with the same query, same bound
        start = time.perf_counter()
        replies = self.mcp_session([{"method": "tools/call", "params": {
            "name": "memory_search", "arguments": {"query": prompt}}}])
        took = time.perf_counter() - start
        print(f"[HUN-211 cap probe] memory_search serve session {took:.3f}s", file=sys.stderr)
        self.assertFalse(replies[2]["result"].get("isError"), replies[2])
        self.assertLess(took, 1.5)


if __name__ == "__main__":
    unittest.main()
