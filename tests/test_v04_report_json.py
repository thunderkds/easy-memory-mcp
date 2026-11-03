"""HUN-197 (v0.4 FR-015): report --json writes <store>/report.json; the Stop hook refreshes it.

Every test uses a temp EASY_MEMORY_HOME and a temp CLAUDE_CONFIG_DIR (the t007 fixtures). The
Stop hook tests mock subprocess.Popen, so no real process starts.
"""
import io
import json
import os
import re
import stat
import sys
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parent))  # t007 imports its sibling by name

import test_t002_hook_stop as t002  # noqa: E402
import test_t007_report as t007  # noqa: E402

easy_memory = t007.easy_memory
FIELDS = {"v", "generated", "min_sessions", "sessions_logged", "no_data", "no_claude_log",
          "forced", "groups", "note_opened", "too_few", "on_vs_off_pct", "store"}
GROUP_FIELDS = {"sessions", "tokens_all_median", "tokens_io_median", "turns_median"}
HOUR = 3600
REAL_POPEN = easy_memory.subprocess.Popen
GOLDEN = (  # the text report on main (4679635) for golden_fixture, before this change
    'easy-memory report for {root}\n'
    'sessions logged: 8 | no data: 0 (log file, no prompts.log line) | no Claude log: 0 (prompts.log line, no log file) | forced switch: 1 (left out of the comparison)\n'
    'state  sessions   tokens incl. cache (headline)  tokens in+out  median turns  note opened\n'
    'on            4                             434            134             3  1/1 (100%)  too few sessions to compare\n'
    'off           3                             540            240             3  -  too few sessions to compare\n'
    "Tokens are per session: median over sessions. Headline = tokens including cache (input + cache creation + cache read + output), as experiments 01 to 03 counted them; 'in+out' is input + output only (PRD FR-007 wording). Sub-agent work counts with its session. Note opened = share of on sessions that got an index and then ran memory_read or Read on a note. Only sessions where the switch was auto (the day decided the state) are compared; forced on/off sessions are not.\n"
    'too few sessions to compare (fewer than 10 sessions in a group): do not read a result into these numbers yet.\n'
    'store: 1 notes, {size} bytes (notes folder of this repo)\n'
)


def number(cell):
    return int(cell.replace(",", ""))


class JsonReportCase(t007.ReportTestCase):
    def report_json(self):
        code, out, err = self.run_report("--json")
        self.assertEqual((code, err), (0, ""))
        return json.loads(out), out

    def golden_fixture(self):
        self.fill([100, 110, 120], [200, 210, 220])
        self.add_session("a", "on", 90, injected=True, opened="mcp")
        self.log_prompt("f", "on", configured="on")
        self.note(self.repo, "p1", "answer one " * 30)

    @property
    def report_file(self):
        return self.store / "report.json"


class JsonFieldsTest(JsonReportCase):
    def test_numbers_equal_the_text_report(self):  # AC1, SC1
        self.fill([100 + 10 * i for i in range(4)], [300 + 20 * i for i in range(3)])
        self.add_session("o1", "on", 90, injected=True, opened="mcp")
        self.add_session("o2", "on", 91, injected=True)
        self.log_prompt("gone", "off")                       # no Claude log
        self.log_prompt("f1", "on", configured="on")         # forced
        self.write_log("stray", [self.turn("stray", "m1", 5, 5)])  # no data
        self.note(self.repo, "p1", "answer one " * 30)
        _, text, _ = self.run_report()
        data, _ = self.report_json()
        rows = self.rows(text)
        self.assertEqual(set(data), FIELDS)
        self.assertEqual(data["v"], 1)
        self.assertEqual(data["min_sessions"], 10)
        self.assertRegex(data["generated"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        for state in ("on", "off"):
            group = data["groups"][state]
            self.assertEqual(set(group), GROUP_FIELDS)
            self.assertEqual(group["sessions"], int(rows[state][1]))
            self.assertEqual(group["tokens_all_median"], number(rows[state][2]))
            self.assertEqual(group["tokens_io_median"], number(rows[state][3]))
            self.assertEqual(group["turns_median"], number(rows[state][4]))
        self.assertEqual(data["note_opened"], {"opened": 1, "indexed": 2})
        for key, label in (("sessions_logged", "sessions logged"), ("no_data", "no data"),
                           ("no_claude_log", "no Claude log"), ("forced", "forced switch")):
            self.assertEqual(data[key], int(re.search(rf"{label}: (\d+)", text).group(1)), key)
        match = re.search(r"store: (\d+) notes, ([\d,]+) bytes", text)
        self.assertEqual(data["store"], {"notes": int(match.group(1)),
                                         "bytes": number(match.group(2))})
        self.assertEqual(data["store"]["notes"], 1)

    def test_numbers_are_numbers(self):  # edge: medians stay numbers
        self.fill([100, 111], [200, 222])
        data, _ = self.report_json()
        for state in ("on", "off"):
            for key in ("tokens_all_median", "tokens_io_median", "turns_median"):
                value = data["groups"][state][key]
                self.assertIs(type(value), int, (state, key, value))

    def test_file_is_private_and_equal_to_the_printed_object(self):  # AC2, SC1
        self.fill([100, 110], [200, 210])
        data, out = self.report_json()
        self.assertEqual(stat.S_IMODE(os.stat(self.report_file).st_mode), 0o600)
        self.assertEqual(json.loads(self.report_file.read_text()), data)
        self.assertEqual(self.report_file.read_text(), out)
        self.assertEqual(sorted(p.name for p in self.store.iterdir() if p.name.endswith(".tmp")), [])

    def test_too_few_has_no_percentage(self):  # AC3
        self.fill([100 + i for i in range(9)], [200 + i for i in range(10)])
        data, _ = self.report_json()
        self.assertTrue(data["too_few"])
        self.assertIsNone(data["on_vs_off_pct"])

    def test_ten_per_group_has_the_text_percentage(self):  # AC3, SC2
        self.fill([100 + 7 * i for i in range(10)], [200 + 9 * i for i in range(10)])
        _, text, _ = self.run_report()
        data, _ = self.report_json()
        self.assertFalse(data["too_few"])
        shown = re.search(r"on vs off, median headline tokens: ([+-]\d+)%", text).group(1)
        self.assertIs(type(data["on_vs_off_pct"]), int)
        self.assertEqual(data["on_vs_off_pct"], int(shown))
        self.assertLess(data["on_vs_off_pct"], 0)

    def test_off_median_zero_has_no_percentage(self):  # FR-015: null when the off median is 0
        for i in range(10):
            self.add_session(f"on-{i}", "on", 90)
            self.log_prompt(f"off-{i}", "off")
            self.write_log(f"off-{i}", [self.turn(f"off-{i}", f"m{i}", 0, 0)])
        data, _ = self.report_json()
        self.assertFalse(data["too_few"])
        self.assertEqual(data["groups"]["off"]["tokens_all_median"], 0)
        self.assertIsNone(data["on_vs_off_pct"])

    def test_empty_store_writes_a_valid_object(self):  # AC7, SC1
        code, out, err = self.run_report("--json")
        self.assertEqual((code, err), (0, ""))
        data = json.loads(out)
        self.assertEqual(json.loads(self.report_file.read_text()), data)
        self.assertEqual((data["sessions_logged"], data["no_data"], data["no_claude_log"],
                          data["forced"]), (0, 0, 0, 0))
        for state in ("on", "off"):
            self.assertEqual(data["groups"][state], {
                "sessions": 0, "tokens_all_median": None, "tokens_io_median": None,
                "turns_median": None})
        self.assertEqual(data["note_opened"], {"opened": 0, "indexed": 0})
        self.assertTrue(data["too_few"])
        self.assertIsNone(data["on_vs_off_pct"])
        self.assertEqual(data["store"], {"notes": 0, "bytes": 0})

    def test_prompts_log_without_claude_logs_still_writes(self):  # AC7
        self.log_prompt("s1", "on")
        data, _ = self.report_json()
        self.assertEqual((data["sessions_logged"], data["no_claude_log"]), (1, 1))
        self.assertTrue(self.report_file.is_file())

    def test_plain_report_writes_nothing_and_json_prints_no_table(self):  # AC5
        self.fill([100, 110], [200, 210])
        _, text, _ = self.run_report()
        self.assertFalse(self.report_file.exists())
        _, out, _ = self.run_report("--json")
        self.assertNotIn("easy-memory report for", out)

    def test_old_report_text_is_unchanged(self):  # AC5: text captured from main before the change
        self.golden_fixture()
        _, text, _ = self.run_report()
        size = sum(p.stat().st_size for p in (self.store / "notes").glob("*.json"))
        self.assertEqual(text, GOLDEN.format(root=os.path.realpath(self.repo), size=f"{size:,}"))

    def test_json_run_does_not_change_the_text_report(self):  # AC5
        self.golden_fixture()
        _, before, _ = self.run_report()
        self.run_report("--json")
        _, after, _ = self.run_report()
        self.assertEqual(after, before)


class MetadataOnlyTest(JsonReportCase):
    def test_no_prompt_answer_session_id_or_path_in_the_file(self):  # AC4, SC3
        marks = {"prompt": "PROMPTMARK-zq81", "answer": "ANSWERMARK-zq82",
                 "sid": "SESSIONMARK-zq83"}
        self.note(self.repo, marks["prompt"], marks["answer"] * 30)
        self.add_session(marks["sid"], "on", 90, injected=True, opened="read")
        self.log_prompt("OTHERMARK-zq84", "off")
        data, out = self.report_json()
        text = self.report_file.read_text()
        self.assertEqual(data["groups"]["on"]["sessions"], 1)
        for found in (text, out):
            for mark in (*marks.values(), "OTHERMARK", "zq8", "/"):
                self.assertNotIn(mark, found)
            for path in (str(self.repo), str(self.tmp), str(self.store), str(self.claude),
                         os.path.realpath(self.repo)):
                self.assertNotIn(path, found)


def stale_by(path, seconds):
    then = time.time() - seconds
    os.utime(path, (then, then))


class RefreshTestCase(t002.HookTestCase):
    def setUp(self):
        super().setUp()
        self.popen = mock.MagicMock()

        def spy(argv, *args, **kwargs):  # fake only the report spawn; other commands still run
            if "--release-lock" in argv:
                return self.popen(argv, *args, **kwargs)
            return REAL_POPEN(argv, *args, **kwargs)
        patcher = mock.patch.object(easy_memory.subprocess, "Popen", spy)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.repo = self.make_repo()
        self.store = self.home / easy_memory.repo_key(self.repo)

    def stop(self, **extra):
        return self.run_hook(self.stop_input(self.repo, t002.long_answer("src/a.py"), **extra))

    def report_spawns(self):
        return self.popen.call_args_list


class HookRefreshTest(RefreshTestCase):
    def test_missing_report_json_starts_a_detached_report(self):  # AC6, SC4
        code, out, err = self.stop()
        self.assertEqual((code, out, err), (0, "", ""))
        (call,) = self.report_spawns()
        argv = call.args[0]
        self.assertEqual(argv[0], sys.executable)
        self.assertEqual(argv[2:], ["report", "--json", "--repo", os.path.realpath(self.repo),
                                    "--release-lock"])
        self.assertTrue(argv[1].endswith("easy_memory.py"))
        self.assertIs(call.kwargs["start_new_session"], True)
        for name in ("stdin", "stdout", "stderr"):
            self.assertIs(call.kwargs[name], easy_memory.subprocess.DEVNULL)
        self.assertEqual(stat.S_IMODE(os.stat(self.store / "report.lock").st_mode), 0o600)
        self.assertEqual(len(self.notes(self.repo)), 1)

    def test_fresh_report_json_starts_nothing(self):  # AC6, SC4
        self.stop()
        self.popen.reset_mock()
        (self.store / "report.lock").unlink()
        (self.store / "report.json").write_text("{}")
        self.stop()
        self.assertEqual(self.report_spawns(), [])

    def test_report_json_older_than_an_hour_starts_one(self):  # AC6
        self.stop()
        self.popen.reset_mock()
        (self.store / "report.lock").unlink()
        path = self.store / "report.json"
        path.write_text("{}")
        stale_by(path, HOUR - 60)
        self.stop()
        self.assertEqual(self.report_spawns(), [])
        stale_by(path, HOUR + 60)
        self.stop()
        self.assertEqual(len(self.report_spawns()), 1)

    def test_future_mtime_counts_as_fresh(self):  # edge: no spawn loop
        self.stop()
        self.popen.reset_mock()
        (self.store / "report.lock").unlink()
        path = self.store / "report.json"
        path.write_text("{}")
        stale_by(path, -5 * HOUR)
        self.stop()
        self.assertEqual(self.report_spawns(), [])

    def test_held_lock_starts_nothing_and_a_dead_lock_is_replaced(self):  # AC6, edge
        self.stop()
        self.popen.reset_mock()
        lock = self.store / "report.lock"
        self.assertTrue(lock.exists())
        self.stop()
        self.assertEqual(self.report_spawns(), [])
        stale_by(lock, 11 * 60)
        self.stop()
        self.assertEqual(len(self.report_spawns()), 1)

    def test_weights_lock_does_not_block_a_report(self):  # the two locks are separate
        easy_memory._private_dir(self.store)
        (self.store / "weights.lock").write_text("")
        self.stop()
        self.assertEqual(len(self.report_spawns()), 1)

    def test_spawn_failure_exits_0_prints_nothing_and_frees_the_lock(self):  # AC6, NFR-004
        self.popen.side_effect = OSError("no fork")
        code, out, err = self.stop()
        self.assertEqual((code, out, err), (0, "", ""))
        self.assertFalse((self.store / "report.lock").exists())
        self.assertEqual(len(self.notes(self.repo)), 1)

    def test_spawn_blowing_up_with_another_error_still_exits_0(self):  # NFR-004
        self.popen.side_effect = RuntimeError("boom")
        code, out, err = self.stop()
        self.assertEqual((code, out, err), (0, "", ""))
        self.assertFalse((self.store / "report.lock").exists())

    def test_no_note_saved_starts_nothing(self):  # refresh follows a saved note
        self.run_hook(self.stop_input(self.repo, "short"))
        self.run_hook(self.stop_input(self.repo, t002.long_answer(), stop_hook_active=True))
        self.assertEqual(self.report_spawns(), [])

    def test_the_hook_never_waits_for_the_child(self):  # AC6
        child = mock.MagicMock()
        self.popen.return_value = child
        self.stop()
        child.wait.assert_not_called()
        child.communicate.assert_not_called()

    def test_the_check_costs_one_stat_and_stays_fast(self):  # edge: 2 s budget
        self.stop()
        (self.store / "report.lock").unlink()
        (self.store / "report.json").write_text("{}")
        self.popen.reset_mock()
        start = time.perf_counter()
        for _ in range(200):
            easy_memory._refresh_report(self.repo, self.store)
        self.assertLess((time.perf_counter() - start) / 200, 0.005)
        self.assertEqual(self.report_spawns(), [])


class ChildReleasesLockTest(JsonReportCase):
    def test_release_lock_flag_removes_report_lock_after_the_run(self):  # AC6
        easy_memory._private_dir(self.store)
        (self.store / "report.lock").write_text("")
        code, _, _ = self.run_report("--json", "--release-lock")
        self.assertEqual(code, 0)
        self.assertFalse((self.store / "report.lock").exists())
        self.assertTrue(self.report_file.is_file())

    def test_lock_is_released_when_the_write_fails(self):  # AC6, edge: dead child
        easy_memory._private_dir(self.store)
        (self.store / "report.lock").write_text("")
        with mock.patch.object(easy_memory, "_atomic_write", side_effect=OSError("disk full")):
            code, out, err = self.run_report("--json", "--release-lock")
        self.assertEqual(code, 1)
        self.assertIn("disk full", err)
        self.assertFalse((self.store / "report.lock").exists())



class MissingRepoTest(JsonReportCase):
    def test_missing_repo_path_writes_nothing_and_returns_1(self):  # HUN-199
        missing = self.tmp / "no-such-repo"
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "stdin", io.StringIO("")), \
                redirect_stdout(out), redirect_stderr(err):
            code = easy_memory.main(["report", "--json", "--repo", str(missing)])
        self.assertEqual(code, 1)
        self.assertEqual(out.getvalue(), "")
        self.assertIn("no such folder", err.getvalue())
        self.assertFalse((self.home / easy_memory.repo_key(missing)).exists())


if __name__ == "__main__":
    unittest.main()
