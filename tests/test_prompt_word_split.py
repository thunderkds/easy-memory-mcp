"""HUN-208: the prompt hook splits the prompt once per _index_lines call and each distinct word once.

Ranking must not change. OLD_* below are frozen copies of tokens, score and _index_lines as they
were on main at 0bbf1cb; the new code must agree with them. Every test uses a temp
EASY_MEMORY_HOME; nothing touches the real ~/.easy-memory.
"""
import hashlib
import json
import os
import random
import re
import subprocess
import sys
import tempfile
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock
import math

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import easy_memory  # noqa: E402


def old_tokens(text):
    out = []
    for word in re.findall(r"[A-Za-z][A-Za-z0-9_]*", text):
        parts = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", word).replace("_", " ")
        for part in {word.lower(), *parts.lower().split()}:
            if len(part) >= 3 and part not in easy_memory.STOP_WORDS:
                out.append(part)
    return out


def old_score(prompt, text, weights, k1=1.2):
    n, df = weights["n"], weights["df"]
    weight = {t: math.log((n + 1) / (df.get(t, 0) + 1)) + 1 for t in set(old_tokens(prompt))}
    best = sum(weight.values()) * (k1 + 1)
    tf = Counter(old_tokens(text))
    got = sum(w * tf[t] * (k1 + 1) / (tf[t] + k1) for t, w in weight.items() if tf[t])
    return got / best if best else 0.0


def old_index_lines(prompt, cwd, weights):
    ranked = []
    for note in easy_memory.read_notes(cwd):
        if not (isinstance(note.get("id"), str) and easy_memory.NOTE_ID.fullmatch(note["id"])
                and isinstance(note.get("prompt"), str) and isinstance(note.get("answer"), str)):
            continue
        value = old_score(prompt, note["prompt"] + "\n" + note["answer"], weights)
        if value >= easy_memory.INDEX_FLOOR:
            ranked.append((value, note))
    if not ranked:
        return []
    ranked.sort(key=lambda pair: -pair[0])
    root_real = os.path.realpath(easy_memory._repo_root(cwd))
    return [easy_memory._index_line(note, root_real) for _, note in ranked[:easy_memory.INDEX_MAX_NOTES]]


WORDS = ["authService", "parse_http_response", "HTTPServer", "loader", "config", "snake_case_name",
         "Foo2Bar", "AUTH", "Auth", "auth", "retryPolicy", "x1", "ab", "the", "and", "zebra",
         "database", "cacheKey", "userId", "render_view", "token", "session", "Ünïcode", "api2"]
PROMPTS = ["how does the authService retry work",
           "parse_http_response and HTTPServer config",
           "snake_case_name loader cacheKey",
           "Why is AUTH token session handled by auth and Auth?",
           "database render_view userId zebra"]


def fake_weights():
    df = {w: i % 7 + 1 for i, w in enumerate(
        ["auth", "service", "retry", "http", "response", "config", "loader", "cache", "key", "token"])}
    return {"n": 40, "df": df}


class FixtureStore(unittest.TestCase):
    NOTES = 60

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hun208-")).resolve()
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(self.tmp)]))
        self.home = self.tmp / "store-home"
        patcher = mock.patch.dict(os.environ, {"EASY_MEMORY_HOME": str(self.home)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        folder = self.home / easy_memory.repo_key(self.repo) / "notes"
        easy_memory._private_dir(folder)
        rng = random.Random(208)
        for i in range(self.NOTES):
            note_id = f"20261001T0000{i:05d}-{i:08x}"
            body = {"v": 1, "id": note_id,
                    "prompt": " ".join(rng.choices(WORDS, k=rng.randint(2, 9))),
                    "answer": " ".join(rng.choices(WORDS, k=rng.randint(10, 80))),
                    "time": "2026-10-01T00:00:00Z", "session_id": "s", "files": {}}
            (folder / f"{note_id}.json").write_text(json.dumps(body), encoding="utf-8")

    def store_tree(self):
        return sorted(str(p.relative_to(self.home)) for p in self.home.rglob("*"))


class TokensTest(unittest.TestCase):
    TEXTS = ["parseHTTPResponse snake_case_name X1 ab The and Foo2Bar",
             "Auth auth AUTH authService auth_service auth auth auth",
             "a1 b2c3 99bottles abc ABC aBc __init__ _private x_y_z camelCaseWord2Go",
             "Ünïcode naïve café über_cool 123 456abc", "", "!!! ??? ...",
             "for the and are but not you all any can had her was one our out"]

    def test_same_multiset_as_old_tokens(self):  # AC1
        for text in self.TEXTS:
            self.assertEqual(sorted(easy_memory.tokens(text)), sorted(old_tokens(text)), text)

    def test_repeated_word_still_repeats(self):  # AC1
        self.assertEqual(Counter(easy_memory.tokens("auth auth AUTH")), Counter(old_tokens("auth auth AUTH")))
        self.assertEqual(easy_memory.tokens("auth auth AUTH").count("auth"), 3)


class ScoreParityTest(unittest.TestCase):
    def test_score_equals_old_score(self):  # AC2
        weights = fake_weights()
        rng = random.Random(3)
        for prompt in PROMPTS + ["", "!!"]:
            for _ in range(10):
                text = " ".join(rng.choices(WORDS, k=rng.randint(0, 40)))
                self.assertAlmostEqual(easy_memory.score(prompt, text, weights),
                                       old_score(prompt, text, weights), places=12)

    def test_unknown_word_gets_rarest_weight(self):
        weights = {"n": 10, "df": {}}
        self.assertAlmostEqual(easy_memory.score("zebra", "zebra", weights), 1 / 2.2, places=12)


class IndexLinesTest(FixtureStore):
    # sha256 of the "\n".join of the 5 prompts' lines from the pre-change code (main 0bbf1cb)
    GOLDEN_SHA256 = "ddd6af7376b21710ae33c45bc1dd8eed83f172e1ff8b54012f5f11399e0c3c98"

    def lines(self, fn):
        weights = fake_weights()
        return [fn(prompt, self.repo, weights) for prompt in PROMPTS]

    def test_lines_equal_pre_change_lines(self):  # AC3
        got, want = self.lines(easy_memory._index_lines), self.lines(old_index_lines)
        self.assertEqual(got, want)
        self.assertGreaterEqual(sum(len(x) for x in got), 5, "fixture must produce lines")
        self.assertGreaterEqual(len(easy_memory.read_notes(self.repo)), 50)

    def test_lines_match_golden_captured_from_main(self):  # AC3
        flat = "\n".join("\n".join(lines) + "|" for lines in self.lines(easy_memory._index_lines))
        self.assertEqual(hashlib.sha256(flat.encode()).hexdigest(), self.GOLDEN_SHA256)

    def test_prompt_is_split_once_per_call(self):  # AC4
        real = easy_memory.tokens
        prompt = PROMPTS[0]
        calls = []

        def spy(text):
            calls.append(text)
            return real(text)

        with mock.patch.object(easy_memory, "tokens", spy):
            easy_memory._index_lines(prompt, self.repo, fake_weights())
        self.assertEqual(calls.count(prompt), 1)
        self.assertGreaterEqual(len(calls), self.NOTES)  # each note is still split

    def test_memory_search_uses_same_path(self):  # AC4, memory_search
        real = easy_memory.tokens
        calls = []
        with mock.patch.object(easy_memory, "tokens", lambda t: calls.append(t) or real(t)):
            easy_memory._tool_search(self.repo, {"query": PROMPTS[1]})
        self.assertEqual(calls.count(PROMPTS[1]), 1)

    def test_prompt_hook_and_search_write_no_new_store_file(self):  # AC6
        easy_memory.write_config(self.repo, "on")
        weights = self.home / easy_memory.repo_key(self.repo) / "weights.json"
        weights.write_text(json.dumps({"v": 1, "n": 40, "head": None, "built_at": 9e9,
                                       "df": fake_weights()["df"]}))
        before = self.store_tree()
        data = {"cwd": str(self.repo), "prompt": PROMPTS[0]}
        real_popen = subprocess.Popen
        with mock.patch.object(easy_memory.subprocess, "Popen", wraps=real_popen) as popen:
            self.assertTrue(easy_memory.prompt_index(data))
        self.assertFalse([c for c in popen.call_args_list if "build-weights" in c.args[0]])
        easy_memory._tool_search(self.repo, {"query": PROMPTS[1]})
        self.assertEqual(self.store_tree(), before)


class WordCacheBoundTest(unittest.TestCase):
    def test_word_cache_has_a_maxsize(self):  # AC8
        info = easy_memory._word_parts.cache_info()
        self.assertIsNotNone(info.maxsize)
        self.assertLessEqual(info.maxsize, 1 << 17)

    def test_cache_does_not_outgrow_maxsize(self):  # AC8
        easy_memory._word_parts.cache_clear()
        size = easy_memory._word_parts.cache_info().maxsize
        easy_memory.tokens(" ".join(f"word{chr(97 + i % 26)}{i}x" for i in range(size + 500)))
        self.assertEqual(easy_memory._word_parts.cache_info().currsize, size)


if __name__ == "__main__":
    unittest.main()
