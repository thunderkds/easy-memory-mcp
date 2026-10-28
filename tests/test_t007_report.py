"""HUN-80 (T007): the report subcommand. Standard library only.

Every test uses temp folders, a temp EASY_MEMORY_HOME and a temp CLAUDE_CONFIG_DIR (both set
explicitly, so a CLAUDE_CONFIG_DIR in the user's shell is never read). Claude session logs
are synthetic: tests/fixtures/report_session_static.jsonl and logs written by the helpers.
"""
import io
import json
import os
import re
import statistics
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

import test_t004_hook_prompt as t004  # the tests dir is on sys.path under discover

easy_memory = t004.easy_memory
FIXTURE = Path(__file__).resolve().parent / "fixtures" / "report_session_static.jsonl"
TOO_FEW = "too few sessions to compare"


def usage(inp, out, cache=0):
    return {"input_tokens": inp, "cache_creation_input_tokens": cache // 2,
            "cache_read_input_tokens": cache - cache // 2, "output_tokens": out}


class ReportTestCase(t004.PromptHookTestCase):
    def setUp(self):
        super().setUp()
        self.claude = self.tmp / "claude-config"
        patcher = mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": str(self.claude)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.repo = self.make_repo()
        self.store = self.home / easy_memory.repo_key(self.repo)

    # -- fixture writers ------------------------------------------------------------
    def project_dir(self, repo=None):
        # Claude Code names a project folder after the cwd, every non-alphanumeric as "-".
        name = re.sub(r"[^A-Za-z0-9]", "-", os.path.realpath(repo or self.repo))
        folder = self.claude / "projects" / name
        folder.mkdir(parents=True, exist_ok=True)
        return folder

    def log_prompt(self, sid, effective, injected=False, configured="auto"):
        easy_memory._append_prompt_log(self.repo, {
            "time": "2026-10-28T00:00:00Z", "session_id": sid, "configured": configured,
            "effective": effective, "injected": injected})

    def write_log(self, sid, entries, folder=None):
        path = (folder or self.project_dir()) / f"{sid}.jsonl"
        path.write_text("".join(json.dumps(e) + "\n" for e in entries))
        return path

    def turn(self, sid, msg_id, inp, out, cache=0, tools=(), sidechain=False):
        content = [{"type": "tool_use", "id": f"tu_{msg_id}", "name": name, "input": args}
                   for name, args in tools] or [{"type": "text", "text": "ok"}]
        return {"type": "assistant", "sessionId": sid, "isSidechain": sidechain,
                "message": {"id": msg_id, "role": "assistant", "content": content,
                            "usage": usage(inp, out, cache)}}

    def add_session(self, sid, effective, out_tokens, turns=3, injected=False, opened=None):
        """Log one prompt and write a Claude log with `turns` assistant messages that add up to
        out_tokens output tokens (input 10 and cache 100 per turn). opened: None, 'mcp' or 'read'."""
        self.log_prompt(sid, effective, injected)
        tools = {"mcp": [("mcp__easy-memory__memory_read", {"id": "n1"})],
                 "read": [("Read", {"file_path": str(self.store / "notes" / "n1.json")})],
                 }.get(opened, [])
        entries = [self.turn(sid, f"{sid}-m{i}", 10, out_tokens // turns, cache=100,
                             tools=tools if i == 0 else ()) for i in range(turns)]
        self.write_log(sid, entries)

    def fill(self, on_outs, off_outs):
        for i, out in enumerate(on_outs):
            self.add_session(f"on-{i:02d}", "on", out)
        for i, out in enumerate(off_outs):
            self.add_session(f"off-{i:02d}", "off", out)

    # -- runner / parser ------------------------------------------------------------
    def run_report(self, *extra):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "stdin", io.StringIO("")), \
                redirect_stdout(out), redirect_stderr(err):
            code = easy_memory.main(["report", "--repo", str(self.repo), *extra])
        return code, out.getvalue(), err.getvalue()

    def rows(self, text):
        """{'on': [...cells], 'off': [...cells]} from the table; cells split on whitespace."""
        found = {}
        for line in text.splitlines():
            cells = line.replace(",", "").split()
            if cells and cells[0] in ("on", "off") and len(cells) > 2 and cells[1].isdigit():
                found[cells[0]] = cells
        return found


class ReaderTest(ReportTestCase):
    def test_static_fixture_numbers(self):  # AC3, AC4, edge cases: dup ids, no usage, resumed
        notes = self.store / "notes"
        got = easy_memory.read_session_usage([FIXTURE], notes, "sess-static-1")
        # msg_1 appears twice (one API reply in two lines): the larger output count wins.
        # msg_3 has no usage: skipped. msg_4 is a sub-agent entry: counted with its parent.
        # msg_5 carries another session's id (history copied by a resume): skipped.
        self.assertEqual(got["tokens_all"], (10 + 100 + 1000 + 20) + (3 + 2000 + 30) + (1 + 500 + 10))
        self.assertEqual(got["tokens_io"], (10 + 20) + (3 + 30) + (1 + 10))
        self.assertEqual(got["turns"], 3)
        self.assertTrue(got["opened"])  # an mcp__...__memory_read call

    def test_read_of_a_note_path_counts_but_other_reads_do_not(self):  # AC3
        notes = self.store / "notes"
        mk = lambda path: self.turn("s", "m1", 1, 1, tools=[("Read", {"file_path": path})])
        for path, expected in ((str(notes / "n1.json"), True), (str(self.repo / "src/a.py"), False),
                               (str(notes / ".." / "weights.json"), False)):
            log = self.tmp / "one.jsonl"
            log.write_text(json.dumps(mk(path)) + "\n")
            self.assertEqual(easy_memory.read_session_usage([log], notes, "s")["opened"], expected, path)

    def test_garbage_lines_are_skipped(self):  # AC6
        log = self.tmp / "bad.jsonl"
        good = json.dumps(self.turn("s", "m1", 4, 6))
        log.write_bytes(b"\xff\xfe not utf8\n[1, 2]\n\"str\"\n{\"message\": 5}\n"
                        b"{\"type\": \"assistant\", \"message\": {\"id\": \"x\", \"usage\": {\"input_tokens\": \"7\"}}}\n"
                        + good.encode() + b"\n{\"cut off")
        got = easy_memory.read_session_usage([log], self.store / "notes", "s")
        self.assertEqual((got["tokens_io"], got["turns"]), (10, 1))


class ReportTest(ReportTestCase):
    def test_12_on_12_off_gives_two_groups_with_medians(self):  # SC1, AC1, AC3, AC4
        on_outs = [100 + 10 * i for i in range(12)]    # per session out tokens
        off_outs = [300 + 20 * i for i in range(12)]
        self.fill(on_outs, off_outs)
        code, out, _ = self.run_report()
        self.assertEqual(code, 0)
        rows = self.rows(out)
        # Each session adds 10 input + 100 cache per turn, 3 turns; out_tokens // 3 per turn.
        def expected(outs):
            io_ = [3 * 10 + 3 * (o // 3) for o in outs]
            allt = [v + 300 for v in io_]
            return statistics.median(allt), statistics.median(io_)
        for state, outs in (("on", on_outs), ("off", off_outs)):
            all_med, io_med = expected(outs)
            self.assertEqual(rows[state][1], "12")
            self.assertEqual(float(rows[state][2]), round(all_med))   # headline column
            self.assertEqual(float(rows[state][3]), round(io_med))
            self.assertEqual(float(rows[state][4]), 3.0)              # median turns
        self.assertNotIn(TOO_FEW, out)
        self.assertRegex(out, r"(?i)headline.*including cache")
        self.assertRegex(out, r"(?i)input \+ output")
        self.assertRegex(out, r"on vs off.*-\d+%")  # on uses fewer tokens in this fixture

    def test_3_per_group_warns_next_to_numbers(self):  # SC2, AC5
        self.fill([100, 110, 120], [200, 210, 220])
        code, out, _ = self.run_report()
        self.assertEqual(code, 0)
        self.assertEqual(self.rows(out)["on"][1], "3")
        for line in out.splitlines():
            if re.match(r"(on|off)\s+\d", line):
                self.assertIn(TOO_FEW, line)
        self.assertNotRegex(out, r"on vs off.*%")  # no percentage on thin data

    def test_one_group_under_10_is_enough_to_warn(self):  # AC5
        self.fill([100 + i for i in range(12)], [200, 210])
        _, out, _ = self.run_report()
        self.assertIn(TOO_FEW, out)

    def test_9_per_group_warns(self):  # AC5: the limit is 10
        self.fill([100 + i for i in range(9)], [200 + i for i in range(9)])
        _, out, _ = self.run_report()
        self.assertIn(TOO_FEW, out)

    def test_exactly_10_per_group_does_not_warn(self):  # AC5
        self.fill([100 + i for i in range(10)], [200 + i for i in range(10)])
        _, out, _ = self.run_report()
        self.assertNotIn(TOO_FEW, out)

    def test_missing_log_folder_exits_0_with_a_message(self):  # SC3, AC6
        self.log_prompt("s1", "on")
        self.assertFalse(self.claude.exists())
        code, out, err = self.run_report()
        self.assertEqual(code, 0)
        self.assertRegex(out, r"(?i)no claude session log")
        self.assertEqual(err, "")

    def test_no_data_at_all_exits_0_with_a_message(self):  # AC6
        code, out, _ = self.run_report()
        self.assertEqual(code, 0)
        self.assertRegex(out, r"(?i)no prompt log|no data")
        self.assertFalse(self.home.exists(), "report must not create the store")

    def test_corrupt_prompts_log_lines_are_skipped(self):  # AC6
        self.add_session("good", "on", 90)
        with open(self.store / "prompts.log", "a") as handle:
            handle.write("not json\n[1]\n{\"session_id\": 5, \"effective\": \"on\"}\n"
                         "{\"session_id\": \"x\", \"effective\": \"maybe\"}\n")
        code, out, _ = self.run_report()
        self.assertEqual(code, 0)
        self.assertEqual(self.rows(out)["on"][1], "1")

    def test_first_prompt_state_decides_the_group(self):  # AC2, G4, E11
        self.add_session("flip", "on", 90)
        self.log_prompt("flip", "off")  # the auto day flipped while the session was open
        _, out, _ = self.run_report()
        rows = self.rows(out)
        self.assertEqual(rows["on"][1], "1")
        self.assertEqual(rows["off"][1], "0")

    def test_session_without_log_line_is_no_data_and_excluded(self):  # AC2
        self.add_session("known", "on", 90)
        self.write_log("stray", [self.turn("stray", "m1", 5000, 5000)])  # in repo folder, no line
        _, out, _ = self.run_report()
        self.assertEqual(self.rows(out)["on"][1], "1")
        self.assertRegex(out, r"(?i)no data: 1")

    def test_logged_session_without_claude_log_is_counted_apart(self):  # AC1, AC6
        self.add_session("known", "on", 90)
        self.log_prompt("gone", "off")
        _, out, _ = self.run_report()
        self.assertEqual(self.rows(out)["off"][1], "0")
        self.assertRegex(out, r"(?i)no claude log: 1")

    def test_note_open_rate_counts_only_sessions_that_got_an_index(self):  # AC3
        self.add_session("a", "on", 90, injected=True, opened="mcp")
        self.add_session("b", "on", 90, injected=True, opened="read")
        self.add_session("c", "on", 90, injected=True)
        self.add_session("d", "on", 90, injected=True)
        self.add_session("e", "on", 90, injected=False, opened="mcp")  # no index: not counted
        self.add_session("f", "off", 90)
        _, out, _ = self.run_report()
        rows = self.rows(out)
        self.assertEqual(rows["on"][5], "2/4")
        self.assertIn("50%", " ".join(rows["on"]))
        self.assertEqual(rows["off"][5], "-")

    def test_subagent_log_counts_with_its_parent(self):  # edge: sidechain
        self.add_session("p", "on", 90)
        sub = self.project_dir() / "p" / "subagents"
        sub.mkdir(parents=True)
        (sub / "agent-1.jsonl").write_text(json.dumps(
            self.turn("p", "sub1", 1000, 1000, sidechain=True)) + "\n")
        _, out, _ = self.run_report()
        self.assertEqual(float(self.rows(out)["on"][3]), 30 + 90 + 2000)

    def test_session_found_in_another_project_folder(self):  # AC1, edge: worktree
        self.log_prompt("wt", "off")
        other = self.claude / "projects" / "-some-worktree-folder"
        other.mkdir(parents=True)
        self.write_log("wt", [self.turn("wt", "m1", 7, 8)], folder=other)
        _, out, _ = self.run_report()
        self.assertEqual(self.rows(out)["off"][1], "1")

    def test_session_id_cannot_escape_the_projects_folder(self):  # security
        (self.claude / "secret.jsonl").parent.mkdir(parents=True, exist_ok=True)
        (self.claude / "secret.jsonl").write_text(json.dumps(self.turn("../secret", "m1", 9, 9)) + "\n")
        self.log_prompt("../secret", "on")
        (self.claude / "projects").mkdir(exist_ok=True)
        _, out, _ = self.run_report()
        self.assertEqual(self.rows(out).get("on", [0, "0"])[1], "0")

    def test_store_size_is_printed(self):  # AC7, A4
        self.note(self.repo, "p1", "answer one " * 30)
        self.note(self.repo, "p2", "answer two " * 30)
        size = sum(p.stat().st_size for p in (self.store / "notes").glob("*.json"))
        _, out, _ = self.run_report()
        self.assertRegex(out, rf"(?i)store: 2 notes, {size:,} bytes")

    def test_store_size_zero_for_a_repo_without_notes(self):  # AC7
        _, out, _ = self.run_report()
        self.assertRegex(out, r"(?i)store: 0 notes, 0 bytes")

    def test_report_writes_nothing(self):  # read-only
        self.fill([100, 110], [200, 210])
        self.note(self.repo, "p1", "answer one " * 30)

        def snapshot():
            return {str(p): (p.stat().st_mtime_ns, p.stat().st_size)
                    for root in (self.home, self.claude, self.repo)
                    for p in root.rglob("*") if ".git" not in p.parts}
        before = snapshot()
        self.run_report()
        self.assertEqual(snapshot(), before)

    def test_command_line_exits_0(self):  # AC6: through a real process
        env = {**os.environ, "EASY_MEMORY_HOME": str(self.home),
               "CLAUDE_CONFIG_DIR": str(self.claude)}
        res = subprocess.run([sys.executable, t004.SCRIPT, "report", "--repo", str(self.repo)],
                             capture_output=True, text=True, env=env, stdin=subprocess.DEVNULL)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertNotIn("not implemented", res.stderr)

    def test_default_config_dir_is_dot_claude_in_home(self):  # AC1
        self.log_prompt("h", "on")
        fake_home = self.tmp / "fake-home"
        folder = fake_home / ".claude" / "projects" / "x"
        folder.mkdir(parents=True)
        self.write_log("h", [self.turn("h", "m1", 3, 4)], folder=folder)
        with mock.patch.dict(os.environ, {"HOME": str(fake_home)}):
            os.environ.pop("CLAUDE_CONFIG_DIR")
            _, out, _ = self.run_report()
        self.assertEqual(self.rows(out)["on"][1], "1")


if __name__ == "__main__":
    unittest.main()
