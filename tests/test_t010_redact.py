"""HUN-85 (T010): the Stop hook redacts secrets before a note is saved. Standard library only.

Every test uses temp folders and EASY_MEMORY_HOME. All secrets here are fake and
built from obvious filler (0123456789abcdef...); they are split in the source so
a secret scanner does not flag this file.
"""
import json
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import easy_memory  # noqa: E402
import test_t002_hook_stop as t002  # noqa: E402  (the tests dir is on sys.path under discover)

FILLER = "0123456789abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ"
GITHUB = "gh" + "p_" + FILLER[:36]
GITHUB_OAUTH = "gh" + "o_" + FILLER[:36]
GITHUB_PAT = "github" + "_pat_" + FILLER[:30]
SLACK = "xo" + "xb-" + "0123456789-0123456789-" + FILLER[:24]
AWS = "AK" + "IA" + "0123456789ABCDEF"
ANTHROPIC = "sk" + "-ant-" + "api03-" + FILLER[:40]
OPENAI = "sk" + "-" + FILLER[:40]
JWT = ("ey" + "JhbGciOiJIUzI1NiJ9." + "ey" + "JzdWIiOiIxMjM0NTY3ODkwIn0." + "dBjftJeZ4CVPmB92K27uhbUJU1p1r")
PEM_BODY = "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7\nZm9vYmFyZmFrZWtleQ==\n"
PEM = "-----BEGIN RSA PRIVATE KEY-----\n" + PEM_BODY + "-----END RSA PRIVATE KEY-----"

# kind -> (fixture text, the secret part that must be gone)
PER_KIND = {
    "github_token": ("token ", GITHUB),
    "slack_token": ("slack ", SLACK),
    "aws_access_key": ("aws ", AWS),
    "anthropic_key": ("key ", ANTHROPIC),
    "api_key": ("key ", OPENAI),
    "jwt": ("jwt ", JWT),
    "bearer_token": ("Authorization: Bearer ", "abc123.def456-ghi789"),
    "secret_assignment": ("DB_PASSWORD=", "hunter2hunter2"),
}


class RedactTextTest(unittest.TestCase):
    def test_each_kind_is_replaced_and_secret_is_gone(self):  # AC1
        for kind, (lead, secret) in PER_KIND.items():
            with self.subTest(kind=kind):
                out, hits = easy_memory.redact_text(f"before {lead}{secret} after")
                self.assertNotIn(secret, out)
                self.assertIn(f"[REDACTED:{kind}]", out)
                self.assertEqual(hits, {kind: 1})

    def test_other_github_prefixes(self):
        for secret in (GITHUB_OAUTH, GITHUB_PAT):
            with self.subTest(secret=secret[:6]):
                out, hits = easy_memory.redact_text(f"x {secret} y")
                self.assertEqual((out, hits), ("x [REDACTED:github_token] y", {"github_token": 1}))

    def test_private_key_block_multi_line(self):
        out, hits = easy_memory.redact_text(f"keep1\n{PEM}\nkeep2")
        self.assertEqual((out, hits), ("keep1\n[REDACTED:private_key]\nkeep2", {"private_key": 1}))

    def test_two_private_key_blocks_keep_text_between(self):
        out, hits = easy_memory.redact_text(f"{PEM}\nmiddle\n{PEM}")
        self.assertEqual(out, "[REDACTED:private_key]\nmiddle\n[REDACTED:private_key]")
        self.assertEqual(hits, {"private_key": 2})

    def test_private_key_without_end_is_redacted_to_end_of_text(self):  # AC4
        text = "keep\n-----BEGIN OPENSSH PRIVATE KEY-----\n" + PEM_BODY + "more text, no end line"
        out, hits = easy_memory.redact_text(text)
        self.assertEqual(out, "keep\n[REDACTED:private_key]")
        self.assertEqual(hits, {"private_key": 1})

    def test_fallback_is_dot_star_not_backslash_z(self):  # AC4
        pattern = easy_memory._PRIVATE_KEY.pattern
        self.assertTrue(pattern.endswith("|-----BEGIN [A-Z ]{0,40}PRIVATE KEY.*"))
        self.assertNotIn("\\Z", pattern)

    def test_no_secret_text_is_byte_identical(self):  # AC2
        text = ("Plain note about risk-assessment and task-runner.\r\n"
                "token: string\r\nconst x = {a: 1};\n  indent\tTab\n\n"
                "Ünïcödé text 日本語 — ok. See src/a.py:12 and sk-short\n"
                "if (token == null) {} ; tokens => 1; Authorization header is set\n")
        out, hits = easy_memory.redact_text(text)
        self.assertEqual((out, hits), (text, {}))

    def test_empty_text(self):
        self.assertEqual(easy_memory.redact_text(""), ("", {}))

    def test_risk_and_task_words_are_not_sk_keys(self):  # AC5
        text = "risk-" + FILLER[:30] + " task-" + FILLER[:30] + " my-sk-" + FILLER[:30]
        self.assertEqual(easy_memory.redact_text(text), (text, {}))

    def test_sk_ant_is_one_kind_only(self):  # edge
        out, hits = easy_memory.redact_text(f"k={ANTHROPIC}")
        self.assertEqual(hits, {"anthropic_key": 1})
        self.assertNotIn("api_key", out)

    def test_token_assignment_rules(self):  # AC5
        self.assertEqual(easy_memory.redact_text("token: string"), ("token: string", {}))
        self.assertEqual(easy_memory.redact_text("TOKEN=abc"),
                         ("TOKEN=[REDACTED:secret_assignment]", {"secret_assignment": 1}))
        self.assertEqual(easy_memory.redact_text("token: abcdefgh"),
                         ("token: [REDACTED:secret_assignment]", {"secret_assignment": 1}))
        self.assertEqual(easy_memory.redact_text("token: abcdefg"), ("token: abcdefg", {}))

    def test_assignment_name_forms(self):
        cases = {
            'API_KEY = "my key value"': 'API_KEY = [REDACTED:secret_assignment]',
            "client_secret='abc'": "client_secret=[REDACTED:secret_assignment]",
            '"password": "correct horse battery"': '"password": [REDACTED:secret_assignment]',
            "DB_PASSWD=pw": "DB_PASSWD=[REDACTED:secret_assignment]",
            "export GITHUB_TOKEN=abcdef": "export GITHUB_TOKEN=[REDACTED:secret_assignment]",
        }
        for text, want in cases.items():
            with self.subTest(text=text):
                self.assertEqual(easy_memory.redact_text(text)[0], want)

    def test_wide_alignment_before_and_after_the_separator(self):  # review 1
        cases = {
            "DB_PASSWORD" + " " * 11 + "= hunter2FAKE": "DB_PASSWORD" + " " * 11 + "= [REDACTED:secret_assignment]",
            "DB_PASSWORD=" + " " * 10 + "hunter2FAKE": "DB_PASSWORD=" + " " * 10 + "[REDACTED:secret_assignment]",
            "  password:" + " " * 10 + "hunter2FAKE": "  password:" + " " * 10 + "[REDACTED:secret_assignment]",
        }
        for text, want in cases.items():
            with self.subTest(text=text):
                self.assertEqual(easy_memory.redact_text(text)[0], want)

    def test_bearer_shapes_in_code(self):  # review 2
        cases = {
            'conn.setRequestProperty("Authorization", "Bearer FAKEtoken123");':
                'conn.setRequestProperty("Authorization", "Bearer [REDACTED:bearer_token]");',
            "res.setHeader('Authorization', 'Bearer FAKEtoken123')":
                "res.setHeader('Authorization', 'Bearer [REDACTED:bearer_token]')",
            'headers["Authorization"] = "Bearer FAKEtoken123"':
                'headers["Authorization"] = "Bearer [REDACTED:bearer_token]"',
            'Authorization: Bearer "FAKEtoken123"': 'Authorization: Bearer "[REDACTED:bearer_token]"',
        }
        for text, want in cases.items():
            with self.subTest(text=text):
                out, hits = easy_memory.redact_text(text)
                self.assertEqual(out, want)
                self.assertEqual(easy_memory.redact_text(out), (out, {}))  # idempotent

    def test_no_partial_leak_in_assignment_values(self):  # review 4
        cases = {
            r'password = "FAKE\"esc"': "password = [REDACTED:secret_assignment]",
            r'{"password": "ab\"cdFAKEtail"}': '{"password": [REDACTED:secret_assignment]}',
            'password="hunter2 FAKE': "password=[REDACTED:secret_assignment]",
            "password='hunter2 FAKE": "password=[REDACTED:secret_assignment]",
            "PASSWORD=" + OPENAI[:23] + ".FAKEtail": "PASSWORD=[REDACTED:secret_assignment]",
        }
        for text, want in cases.items():
            with self.subTest(text=text):
                out, _ = easy_memory.redact_text(text)
                self.assertEqual(out, want)
                self.assertEqual(easy_memory.redact_text(out), (out, {}))

    def test_unterminated_quote_stops_at_end_of_line(self):
        out, _ = easy_memory.redact_text('password="hunter2 FAKE\r\nnext line\n')
        self.assertEqual(out, "password=[REDACTED:secret_assignment]\r\nnext line\n")

    def test_second_pass_changes_nothing_after_a_quoted_value(self):
        for text in ('password="abc"/x', 'x = {"password": "abc"}', "PASSWORD=" + OPENAI[:23] + '.tail"'):
            once, _ = easy_memory.redact_text(text)
            self.assertEqual(easy_memory.redact_text(once), (once, {}), text)

    def test_empty_quoted_value_is_not_redacted(self):
        self.assertEqual(easy_memory.redact_text('token = ""'), ('token = ""', {}))

    def test_go_short_assignment(self):  # review 5
        self.assertEqual(easy_memory.redact_text('password := "hunter2FAKE"')[0],
                         "password := [REDACTED:secret_assignment]")

    def test_assignment_value_already_redacted_is_left_alone(self):
        out, hits = easy_memory.redact_text(f"api_key: {ANTHROPIC}")
        self.assertEqual((out, hits), ("api_key: [REDACTED:anthropic_key]", {"anthropic_key": 1}))

    def test_bearer_header_keeps_the_header_name(self):
        out, hits = easy_memory.redact_text('curl -H "Authorization: Bearer abc.def-123"')
        self.assertEqual(out, 'curl -H "Authorization: Bearer [REDACTED:bearer_token]"')
        self.assertEqual(hits, {"bearer_token": 1})

    def test_two_secrets_on_one_line(self):  # edge
        out, hits = easy_memory.redact_text(f"{GITHUB} and {AWS}")
        self.assertEqual(out, "[REDACTED:github_token] and [REDACTED:aws_access_key]")
        self.assertEqual(hits, {"github_token": 1, "aws_access_key": 1})

    def test_secret_at_start_and_end_of_text(self):  # edge
        self.assertEqual(easy_memory.redact_text(GITHUB)[0], "[REDACTED:github_token]")
        self.assertEqual(easy_memory.redact_text(f"a\n{AWS}")[0], "a\n[REDACTED:aws_access_key]")

    def test_windows_line_endings(self):  # edge
        out, hits = easy_memory.redact_text(f"one\r\nTOKEN=abc\r\nkey {OPENAI}\r\nend\r\n")
        self.assertEqual(out, "one\r\nTOKEN=[REDACTED:secret_assignment]\r\n"
                              "key [REDACTED:api_key]\r\nend\r\n")
        pem_out, _ = easy_memory.redact_text(PEM.replace("\n", "\r\n") + "\r\nafter")
        self.assertEqual(pem_out, "[REDACTED:private_key]\r\nafter")

    def test_jwt_inside_a_url(self):  # edge
        out, hits = easy_memory.redact_text(f"https://x.example/cb?token={JWT}&a=1")
        self.assertNotIn(JWT, out)
        self.assertIn("[REDACTED:", out)

    def test_jwt_as_url_path(self):
        out, hits = easy_memory.redact_text(f"https://x.example/{JWT}/end")
        self.assertEqual((out, hits), ("https://x.example/[REDACTED:jwt]/end", {"jwt": 1}))

    def test_non_ascii_around_secret(self):  # edge
        out, _ = easy_memory.redact_text(f"日本語{GITHUB}日本語 ü {AWS}ü")
        self.assertEqual(out, "日本語[REDACTED:github_token]日本語 ü [REDACTED:aws_access_key]ü")

    def test_redaction_is_idempotent(self):
        text = f"{PEM}\n{GITHUB} TOKEN=abc Authorization: Bearer xyz {ANTHROPIC} {JWT} {OPENAI}"
        once, _ = easy_memory.redact_text(text)
        twice, hits = easy_memory.redact_text(once)
        self.assertEqual((twice, hits), (once, {}))


class RedactTimingTest(unittest.TestCase):
    """NFR-008: a 1 MB adversarial input redacts well under the 2 s hook limit."""

    LIMIT = 1.0

    def time_it(self, label, text):
        start = time.perf_counter()
        easy_memory.redact_text(text)
        seconds = time.perf_counter() - start
        print(f"redact 1MB {label}: {seconds:.3f}s", file=sys.stderr)
        self.assertLess(seconds, self.LIMIT, label)

    def test_one_megabyte_adversarial_inputs(self):  # AC6, SC3
        mb = 1024 * 1024
        begin = "-----BEGIN RSA PRIVATE KEY-----"
        cases = {
            "repeated BEGIN": begin * (mb // len(begin)),
            "repeated BEGIN lines": (begin + "\n") * (mb // (len(begin) + 1)),
            "BEGIN then PRIVATE KEY text": "PRIVATE KEY " * (mb // 12),
            "BEGIN/END pairs": (begin + "\nabc\n-----END RSA PRIVATE KEY-----\n") * (mb // 70),
            "long TOKEN run": "TOKEN" * (mb // 5),
            "TOKEN then spaces": "TOKEN" + " " * mb,
            "TOKEN= repeated": "TOKEN=" * (mb // 6),
            "TOKEN: repeated": "TOKEN: " * (mb // 7),
            "one long name line": "A" * mb,
            "name chars then TOKEN": ("A" * 60 + "TOKEN") * (mb // 65),
            "long value": "TOKEN=" + "x" * mb,
            "SECRET runs": "SECRET" * (mb // 6),
            "escaped quote runs": 'password="' + '\\"' * (mb // 2),
            "password then spaces": "password=" + " " * mb,
            "placeholder tails": "password=[REDACTED:api_key].x " * (mb // 29),
            "long colon value": "token: " + "x" * mb,
            "quote runs": 'TOKEN="' + 'a "' * (mb // 3),
            "sk- runs": "sk-" * (mb // 3),
            "eyJ runs": "eyJ" * (mb // 3),
            "eyJ dotted": "eyJabcdef." * (mb // 10),
            "ghp_ runs": "ghp_" * (mb // 4),
            "Authorization runs": "Authorization" * (mb // 13),
            "Authorization: Bearer runs": "Authorization: Bearer " * (mb // 22),
            "AKIA runs": "AKIA" * (mb // 4),
            "xox runs": "xoxb-" * (mb // 5),
            "many short lines": "a\n" * (mb // 2),
        }
        for label, text in cases.items():
            self.time_it(label, text)

    def test_one_megabyte_of_repeated_begin_is_fully_redacted(self):  # SC3
        begin = "-----BEGIN RSA PRIVATE KEY-----"
        text = begin * (1024 * 1024 // len(begin))
        start = time.perf_counter()
        out, hits = easy_memory.redact_text(text)
        seconds = time.perf_counter() - start
        print(f"redact 1MB repeated BEGIN (asserted): {seconds:.3f}s", file=sys.stderr)
        self.assertEqual((out, hits), ("[REDACTED:private_key]", {"private_key": 1}))
        self.assertLess(seconds, 2.0)


class HookStopRedactionTest(t002.HookTestCase):
    def secret_answer(self, size=500):
        return t002.long_answer("src/a.py", size=size) + f" key {GITHUB} end"

    def test_prompt_and_answer_are_redacted_in_the_saved_note(self):  # AC1, SC1
        repo = self.make_repo()
        answer = self.secret_answer()
        transcript = self.write_transcript([
            t002.user_entry(f"my token is {AWS} and TOKEN=abc"), t002.assistant_entry(answer)])
        code, out, _ = self.run_hook(self.stop_input(repo, answer, transcript))
        self.assertEqual((code, out), (0, ""))
        (note,) = self.notes(repo)
        self.assertNotIn(GITHUB, note["answer"])
        self.assertIn("[REDACTED:github_token]", note["answer"])
        self.assertEqual(note["prompt"],
                         "my token is [REDACTED:aws_access_key] and TOKEN=[REDACTED:secret_assignment]")
        self.assertEqual(self.log_lines(), [])

    def test_every_kind_end_to_end(self):  # AC1
        repo = self.make_repo()
        for kind, (lead, secret) in PER_KIND.items():
            with self.subTest(kind=kind):
                answer = t002.long_answer("src/a.py") + f"\n{lead}{secret}\n"
                self.run_hook(self.stop_input(repo, answer))
        notes = self.notes(repo)
        self.assertEqual(len(notes), len(PER_KIND))
        for note in notes:
            for _, secret in PER_KIND.values():
                self.assertNotIn(secret, note["answer"])
        found = {kind for note in notes for kind in PER_KIND if f"[REDACTED:{kind}]" in note["answer"]}
        self.assertEqual(found, set(PER_KIND))

    def test_no_secret_note_is_byte_identical(self):  # AC2, SC2
        repo = self.make_repo()
        answer = t002.long_answer("src/a.py") + "\ntoken: string\nrisk-management task-list\n"
        transcript = self.write_transcript([
            t002.user_entry("what is in a.py? 日本語"), t002.assistant_entry(answer)])
        self.run_hook(self.stop_input(repo, answer, transcript))
        (note,) = self.notes(repo)
        self.assertEqual(note["prompt"], "what is in a.py? 日本語")
        self.assertEqual(note["answer"], answer)

    def test_cited_file_hashes_do_not_change(self):  # AC3
        repo = self.make_repo()
        plain = t002.long_answer("src/a.py")
        self.run_hook(self.stop_input(repo, plain))
        self.run_hook(self.stop_input(repo, plain + f" {GITHUB}"))
        files = [note["files"] for note in self.notes(repo)]
        self.assertEqual(len(files), 2)
        self.assertEqual(files[0], files[1])
        self.assertEqual(files[0], {"src/a.py": t002.sha(b"x = 1\n")})

    def test_cited_file_inside_a_secret_still_counts_raw(self):  # AC3
        repo = self.make_repo()
        answer = t002.long_answer(size=300) + "\nTOKEN=src/a.py\n"
        self.run_hook(self.stop_input(repo, answer))
        (note,) = self.notes(repo)
        self.assertNotIn("src/a.py", note["answer"])
        self.assertEqual(note["files"], {"src/a.py": t002.sha(b"x = 1\n")})

    def test_min_answer_chars_uses_the_raw_answer(self):  # AC3
        repo = self.make_repo()
        answer = "TOKEN=" + "a" * (easy_memory.MIN_ANSWER_CHARS + 10)  # long raw, short once redacted
        redacted, _ = easy_memory.redact_text(answer)
        self.assertLess(len(redacted), easy_memory.MIN_ANSWER_CHARS)
        self.run_hook(self.stop_input(repo, answer))
        (note,) = self.notes(repo)
        self.assertEqual(note["answer"], "TOKEN=[REDACTED:secret_assignment]")

    def test_a_raising_redactor_saves_no_note_and_logs_one_line(self):  # AC7, SC4
        repo = self.make_repo()
        with mock.patch.object(easy_memory, "redact_text", side_effect=RuntimeError("boom")):
            code, out, err = self.run_hook(self.stop_input(repo, t002.long_answer("src/a.py")))
        self.assertEqual((code, out, err), (0, "", ""))
        self.assertEqual(self.notes(repo), [])
        lines = self.log_lines()
        self.assertEqual(len(lines), 1)
        self.assertIn("hook-stop error: RuntimeError: boom", lines[0])

    def test_hook_log_never_holds_matched_text(self):
        repo = self.make_repo()
        with mock.patch.object(easy_memory, "redact_text", side_effect=RuntimeError("bad")):
            self.run_hook(self.stop_input(repo, self.secret_answer()))
        self.assertNotIn(GITHUB, "\n".join(self.log_lines()))

    def test_one_megabyte_answer_through_the_hook_is_fast(self):  # NFR-001, NFR-008
        repo = self.make_repo()
        begin = "-----BEGIN RSA PRIVATE KEY-----"
        answer = t002.long_answer("src/a.py") + begin * (1024 * 1024 // len(begin))
        start = time.perf_counter()
        self.run_hook(self.stop_input(repo, answer))
        seconds = time.perf_counter() - start
        print(f"hook-stop with 1MB repeated BEGIN: {seconds:.3f}s", file=sys.stderr)
        (note,) = self.notes(repo)
        self.assertTrue(note["answer"].endswith("[REDACTED:private_key]"))
        self.assertLess(seconds, 2.0)


if __name__ == "__main__":
    unittest.main()
