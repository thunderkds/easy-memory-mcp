"""HUN-78 (T005): per-repo switch (on/off/auto) and the prompt log. Standard library only.

Every test uses temp folders and EASY_MEMORY_HOME and feeds stdin; nothing touches the
real home, the real Claude settings or the real ~/.easy-memory. The date is injected by
patching easy_memory._today.
"""
import io
import json
import os
import stat
import subprocess
import sys
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from unittest import mock

import test_t004_hook_prompt as t004  # the tests dir is on sys.path under discover
from test_t004_hook_prompt import PROMPT, SCRIPT

easy_memory = t004.easy_memory

EVEN_DAY = date(2026, 10, 28)  # days since 1970-01-01: 20754
ODD_DAY = date(2026, 10, 29)   # 20755


def mode(path):
    return stat.S_IMODE(os.stat(path).st_mode)


class SwitchTestCase(t004.PromptHookTestCase):
    def set_day(self, day):
        patcher = mock.patch.object(easy_memory, "_today", return_value=day)
        patcher.start()
        self.addCleanup(patcher.stop)

    def store(self, repo):
        return self.home / easy_memory.repo_key(repo)

    def run_switch(self, repo, *words):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "stdin", io.StringIO("")), \
                redirect_stdout(out), redirect_stderr(err):
            code = easy_memory.main(["switch", "--repo", str(repo), *words])
        return code, out.getvalue(), err.getvalue()

    def config(self, repo):
        return json.loads((self.store(repo) / "config.json").read_text())

    def prompt_log(self, repo):
        path = self.store(repo) / "prompts.log"
        return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []

    def ready_repo(self):
        """A repo with weights and one note that matches PROMPT."""
        repo = self.make_repo()
        self.write_weights(repo)
        self.note(repo, "alpha bravo question", "Alpha bravo charlie delta echo in src/a.py.")
        return repo


class SwitchCommandTest(SwitchTestCase):
    def test_no_config_means_auto(self):  # AC2
        repo = self.make_repo()
        self.set_day(EVEN_DAY)
        code, out, err = self.run_switch(repo)
        self.assertEqual((code, err), (0, ""))
        self.assertIn("auto", out)
        self.assertFalse((self.store(repo) / "config.json").exists())  # reading writes nothing

    def test_no_argument_prints_state_and_what_it_means_today(self):  # AC1, AC3
        repo = self.make_repo()
        self.set_day(EVEN_DAY)
        _, out, _ = self.run_switch(repo)
        self.assertRegex(out, r"(?m)^switch: auto$")
        self.assertRegex(out, r"(?m)^today: on \(day 20754 is even\)$")
        self.set_day(ODD_DAY)
        _, out, _ = self.run_switch(repo)
        self.assertRegex(out, r"(?m)^today: off \(day 20755 is odd\)$")

    def test_set_each_state_is_stored_private(self):  # AC1
        repo = self.make_repo()
        self.set_day(EVEN_DAY)
        for state in ("on", "off", "auto", "off"):
            code, out, err = self.run_switch(repo, state)
            self.assertEqual((code, err), (0, ""))
            self.assertRegex(out, rf"(?m)^switch: {state}$")
            self.assertEqual(self.config(repo)["state"], state)
            self.assertEqual(mode(self.store(repo) / "config.json"), 0o600)
        self.assertEqual(mode(self.store(repo)), 0o700)
        _, out, _ = self.run_switch(repo)  # no argument now reads it back
        self.assertRegex(out, r"(?m)^switch: off$")
        self.assertRegex(out, r"(?m)^today: off \(set to off\)$")

    def test_on_means_on_today_whatever_the_day(self):  # AC1
        repo = self.make_repo()
        self.set_day(ODD_DAY)
        _, out, _ = self.run_switch(repo, "on")
        self.assertRegex(out, r"(?m)^today: on \(set to on\)$")

    def test_bad_state_word_is_refused(self):  # AC1
        repo = self.make_repo()
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as raised:
            self.run_switch(repo, "maybe")
        self.assertNotEqual(raised.exception.code, 0)
        self.assertFalse((self.store(repo) / "config.json").exists())

    def test_worktrees_share_the_config(self):  # edge: worktrees share the store
        repo = self.make_repo()
        worktree = self.tmp / "wt"
        t004.run_git(repo, "worktree", "add", "-q", "-b", "other", str(worktree))
        self.run_switch(repo, "off")
        _, out, _ = self.run_switch(worktree)
        self.assertRegex(out, r"(?m)^switch: off$")

    def test_unwritable_store_is_an_error_not_a_traceback(self):  # AC1
        repo = self.make_repo()
        self.home.mkdir(mode=0o700)
        self.store(repo).write_text("a file where the store folder should be")
        code, out, err = self.run_switch(repo, "off")
        self.assertEqual(code, 1)
        self.assertEqual(out, "")
        self.assertIn("easy-memory switch:", err)
        self.assertNotIn("Traceback", err)

    def test_runs_as_a_subprocess_in_the_repo_folder(self):  # AC1
        repo = self.make_repo()
        env = {**os.environ, "EASY_MEMORY_HOME": str(self.home)}
        res = subprocess.run([sys.executable, SCRIPT, "switch", "off"], cwd=repo, input="",
                             capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual((res.returncode, res.stderr), (0, ""))
        self.assertEqual(self.config(repo)["state"], "off")


class EffectiveStateTest(SwitchTestCase):
    def test_auto_follows_the_parity_of_days_since_1970(self):  # AC3
        self.assertEqual(easy_memory.effective_state({"state": "auto"}, date(1970, 1, 1)), "on")
        self.assertEqual(easy_memory.effective_state({"state": "auto"}, date(1970, 1, 2)), "off")
        self.assertEqual(easy_memory.effective_state({}, EVEN_DAY), "on")
        self.assertEqual(easy_memory.effective_state({}, ODD_DAY), "off")

    def test_on_and_off_ignore_the_date(self):  # AC1
        for day in (EVEN_DAY, ODD_DAY):
            self.assertEqual(easy_memory.effective_state({"state": "on"}, day), "on")
            self.assertEqual(easy_memory.effective_state({"state": "off"}, day), "off")

    def test_unknown_value_counts_as_auto(self):  # edge: unknown value in config.json
        for config in ({"state": "sometimes"}, {"state": 1}, {"state": None}, {"x": 1}):
            self.assertEqual(easy_memory.configured_state(config), "auto")
            self.assertEqual(easy_memory.effective_state(config, ODD_DAY), "off")

    def test_unknown_or_corrupt_config_file_is_read_as_auto_and_logged(self):  # edge
        repo = self.make_repo()
        self.set_day(ODD_DAY)
        easy_memory._private_dir(self.store(repo))
        (self.store(repo) / "config.json").write_text('{"v": 1, "state": "sometimes"}')
        _, out, _ = self.run_switch(repo)
        self.assertRegex(out, r"(?m)^switch: auto$")
        self.assertEqual(len(self.log_lines()), 1, self.log_lines())
        self.assertIn("sometimes", self.log_lines()[0])
        (self.store(repo) / "config.json").write_text("{not json")
        _, out, _ = self.run_switch(repo)
        self.assertRegex(out, r"(?m)^switch: auto$")

    def test_setting_a_state_replaces_a_corrupt_config(self):  # edge
        repo = self.make_repo()
        easy_memory._private_dir(self.store(repo))
        (self.store(repo) / "config.json").write_text("{not json")
        self.run_switch(repo, "on")
        self.assertEqual(self.config(repo)["state"], "on")


class PromptGateTest(SwitchTestCase):
    def test_auto_on_day_injects_and_logs(self):  # SC1, AC3, AC5
        repo = self.ready_repo()
        self.set_day(EVEN_DAY)
        text = self.context(self.hook_input(repo))
        self.assertEqual(len(self.note_lines(text)), 1)
        (entry,) = self.prompt_log(repo)
        self.assertEqual((entry["session_id"], entry["configured"], entry["effective"],
                          entry["injected"]), ("s", "auto", "on", True))

    def test_auto_off_day_prints_nothing_logs_off_and_does_not_score(self):  # SC2, AC4, AC5
        repo = self.ready_repo()
        self.set_day(ODD_DAY)
        with mock.patch.object(easy_memory, "prompt_index") as scoring:
            code, out, err = self.run_hook(self.hook_input(repo))
        self.assertEqual((code, out, err), (0, "", ""))
        scoring.assert_not_called()
        (entry,) = self.prompt_log(repo)
        self.assertEqual((entry["configured"], entry["effective"], entry["injected"]),
                         ("auto", "off", False))
        self.assertEqual(self.log_lines(), [])  # hook.log stays empty: off is not an error

    def test_off_prints_nothing_on_an_even_day(self):  # AC4
        repo = self.ready_repo()
        self.set_day(EVEN_DAY)
        self.run_switch(repo, "off")
        self.assertEqual(self.run_hook(self.hook_input(repo)), (0, "", ""))
        (entry,) = self.prompt_log(repo)
        self.assertEqual((entry["configured"], entry["effective"], entry["injected"]),
                         ("off", "off", False))

    def test_on_injects_on_an_odd_day(self):  # AC1, AC4
        repo = self.ready_repo()
        self.set_day(ODD_DAY)
        self.run_switch(repo, "on")
        self.context(self.hook_input(repo))
        (entry,) = self.prompt_log(repo)
        self.assertEqual((entry["configured"], entry["effective"], entry["injected"]),
                         ("on", "on", True))

    def test_each_prompt_uses_the_date_at_prompt_time(self):  # edge: session crosses midnight
        repo = self.ready_repo()
        with mock.patch.object(easy_memory, "_today", side_effect=[EVEN_DAY, ODD_DAY]):
            first = self.run_hook(self.hook_input(repo))
            second = self.run_hook(self.hook_input(repo))
        self.assertIn("additionalContext", first[1])
        self.assertEqual(second, (0, "", ""))
        self.assertEqual([e["effective"] for e in self.prompt_log(repo)], ["on", "off"])

    def test_hook_stop_still_saves_when_off(self):  # SC3, AC4
        repo = self.make_repo()
        self.set_day(ODD_DAY)
        self.run_switch(repo, "off")
        transcript = self.tmp / "transcript.jsonl"
        transcript.write_text(json.dumps({"type": "user", "message": {
            "role": "user", "content": "why is alpha bravo slow"}}) + "\n")
        stop_input = json.dumps({
            "session_id": "s", "cwd": str(repo), "transcript_path": str(transcript),
            "last_assistant_message": "Alpha bravo is slow because of src/a.py. " * 10})
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "stdin", io.StringIO(stop_input)), \
                redirect_stdout(out), redirect_stderr(err):
            code = easy_memory.main(["hook-stop"])
        self.assertEqual((code, out.getvalue(), err.getvalue()), (0, "", ""))
        self.assertEqual(len(easy_memory.read_notes(str(repo))), 1)
        self.assertEqual(self.log_lines(), [])


class PromptLogTest(SwitchTestCase):
    def test_one_json_line_per_run_with_the_five_fields(self):  # AC5
        repo = self.ready_repo()
        self.set_day(EVEN_DAY)
        self.run_hook(self.hook_input(repo))                     # injects
        self.run_hook(self.hook_input(repo, "zulu yankee xray"))  # nothing matches
        self.run_hook(self.hook_input(repo, "/compact"))          # slash command
        lines = (self.store(repo) / "prompts.log").read_text().splitlines()
        self.assertEqual(len(lines), 3)
        entries = [json.loads(line) for line in lines]
        for entry in entries:
            self.assertEqual(set(entry), {"time", "session_id", "configured", "effective",
                                          "injected"})
            self.assertRegex(entry["time"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
            self.assertEqual(entry["session_id"], "s")
        self.assertEqual([e["injected"] for e in entries], [True, False, False])
        self.assertEqual([e["effective"] for e in entries], ["on", "on", "on"])

    def test_log_file_is_private(self):  # AC5, NFR-003
        repo = self.ready_repo()
        self.set_day(ODD_DAY)
        old = os.umask(0)
        try:
            self.run_hook(self.hook_input(repo))
        finally:
            os.umask(old)
        self.assertEqual(mode(self.store(repo) / "prompts.log"), 0o600)
        self.assertEqual(mode(self.store(repo)), 0o700)

    def test_session_id_missing_or_not_text_is_logged_as_empty(self):  # AC5
        repo = self.ready_repo()
        self.set_day(ODD_DAY)
        for session in (None, 7, ["x"]):
            self.run_hook(json.dumps({"session_id": session, "cwd": str(repo), "prompt": PROMPT}))
        self.run_hook(json.dumps({"cwd": str(repo), "prompt": PROMPT}))
        self.assertEqual({e["session_id"] for e in self.prompt_log(repo)}, {""})
        self.assertEqual(len(self.prompt_log(repo)), 4)

    def test_log_write_failure_changes_neither_output_nor_exit_code(self):  # SC AC6, NFR-004
        repo = self.ready_repo()
        self.set_day(EVEN_DAY)
        expected = self.run_hook(self.hook_input(repo))
        self.assertIn("additionalContext", expected[1])
        (self.store(repo) / "prompts.log").unlink()
        (self.store(repo) / "prompts.log").mkdir()  # appending to a folder fails
        self.assertEqual(self.run_hook(self.hook_input(repo)), expected)
        self.set_day(ODD_DAY)
        self.assertEqual(self.run_hook(self.hook_input(repo)), (0, "", ""))

    def test_log_write_failure_is_noted_in_hook_log(self):  # AC6
        repo = self.ready_repo()
        self.set_day(ODD_DAY)
        (self.store(repo) / "prompts.log").mkdir()
        self.run_hook(self.hook_input(repo))
        self.assertEqual(len(self.log_lines()), 1, self.log_lines())
        self.assertIn("hook-prompt error:", self.log_lines()[0])

    def test_log_write_failure_with_unexpected_error_type(self):  # AC6
        repo = self.ready_repo()
        self.set_day(EVEN_DAY)
        with mock.patch.object(easy_memory, "_append_prompt_log", side_effect=RuntimeError("x")):
            code, out, _ = self.run_hook(self.hook_input(repo))
        self.assertEqual(code, 0)
        self.assertIn("additionalContext", out)

    def test_hook_error_still_leaves_one_prompt_log_line(self):  # AC5: every run
        repo = self.ready_repo()
        self.set_day(EVEN_DAY)
        with mock.patch.object(easy_memory, "_score_with", side_effect=RuntimeError("boom")):
            self.assertEqual(self.run_hook(self.hook_input(repo))[:2], (0, ""))
        (entry,) = self.prompt_log(repo)
        self.assertEqual((entry["effective"], entry["injected"]), ("on", False))
        self.assertEqual(len(self.log_lines()), 1)

    def test_unreadable_input_leaves_no_prompt_log_line(self):  # NFR-004: no repo to name
        for stdin_text in ("{not json", "[1, 2]"):
            self.assertEqual(self.run_hook(stdin_text)[:2], (0, ""))
        self.assertFalse(list(self.home.glob("*/prompts.log")))

    def test_subprocess_off_prints_nothing_and_logs(self):  # E12, AC4, AC5
        repo = self.ready_repo()
        env = {**os.environ, "EASY_MEMORY_HOME": str(self.home)}
        self.run_switch(repo, "off")
        res = subprocess.run([sys.executable, SCRIPT, "hook-prompt"], input=self.hook_input(repo),
                             capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual((res.returncode, res.stdout, res.stderr), (0, "", ""))
        (entry,) = self.prompt_log(repo)
        self.assertEqual((entry["configured"], entry["effective"]), ("off", "off"))
        self.run_switch(repo, "on")
        res = subprocess.run([sys.executable, SCRIPT, "hook-prompt"], input=self.hook_input(repo),
                             capture_output=True, text=True, env=env, timeout=30)
        self.assertEqual((res.returncode, res.stderr), (0, ""))
        self.assertEqual(res.stdout.count("\n"), 1)
        self.assertIn("additionalContext", json.loads(res.stdout)["hookSpecificOutput"])
        self.assertEqual([e["injected"] for e in self.prompt_log(repo)], [False, True])


if __name__ == "__main__":
    unittest.main()
