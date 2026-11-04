"""HUN-210: words longer than WORD_CACHE_MAX_CHARS skip the word cache, so its memory has a byte bound.

tokens() output must not change. old_tokens is the frozen copy from the HUN-208 test.
"""
import sys
import unittest
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import easy_memory  # noqa: E402
from tests import test_prompt_word_split as hun208  # noqa: E402


class SameTokensTest(unittest.TestCase):
    def test_ac1_fixtures_unchanged(self):  # AC1
        for text in hun208.TokensTest.TEXTS:
            self.assertEqual(Counter(easy_memory.tokens(text)), Counter(hun208.old_tokens(text)), text)

    def test_words_around_the_limit_unchanged(self):  # AC1
        limit = easy_memory.WORD_CACHE_MAX_CHARS
        for size in (limit - 1, limit, limit + 1, 100_000):
            for text in ("a" * size, "Ab" * (size // 2) + "cD", "parse_" * (size // 6 + 1) + "xYz",
                         "x" + "camelCase" * (size // 9 + 1), "AUTH " + "q" * size + " auth"):
                self.assertEqual(Counter(easy_memory.tokens(text)),
                                 Counter(hun208.old_tokens(text)), (size, text[:20]))

    def test_long_camel_case_word_still_yields_short_parts(self):  # edge case
        got = easy_memory.tokens("loader" + "Parser" * 40)
        self.assertIn("loader", got)
        self.assertIn("parser", got)
        self.assertEqual(Counter(got), Counter(hun208.old_tokens("loader" + "Parser" * 40)))


class ByteBoundTest(unittest.TestCase):
    def test_limit_is_about_64(self):
        self.assertTrue(32 <= easy_memory.WORD_CACHE_MAX_CHARS <= 128)

    def test_long_words_do_not_grow_the_cache(self):  # AC2
        easy_memory._word_parts.cache_clear()
        text = " ".join("w" + format(i, "05d") + "x" * 9_994 for i in range(1_000))
        easy_memory.tokens(text)
        self.assertEqual(easy_memory._word_parts.cache_info().currsize, 0)

    def test_short_words_are_still_cached(self):
        easy_memory._word_parts.cache_clear()
        easy_memory.tokens("loader " * 5 + "x" * easy_memory.WORD_CACHE_MAX_CHARS)
        info = easy_memory._word_parts.cache_info()
        self.assertEqual((info.currsize, info.hits), (2, 4))

    def test_plugin_copy_is_identical(self):  # AC4
        self.assertEqual((ROOT / "plugin" / "easy_memory.py").read_bytes(),
                         (ROOT / "easy_memory.py").read_bytes())


if __name__ == "__main__":
    unittest.main()
