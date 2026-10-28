"""HUN-79 (T006): install / uninstall of the two hooks in user-level Claude Code settings.

Safety (AC9): every test sets a temp CLAUDE_CONFIG_DIR and a temp EASY_MEMORY_HOME and
patches Path.home to a temp folder, so neither the real ~/.claude*, any real Claude settings
file nor the real ~/.easy-memory is ever read or written. setUp asserts this before each test.
"""
import difflib
import io
import json
import os
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import easy_memory  # noqa: E402
from tests import fake_claude  # noqa: E402

MODULE = os.path.abspath(easy_memory.__file__)
STOP_COMMAND = f"{sys.executable} {MODULE} hook-stop"
PROMPT_COMMAND = f"{sys.executable} {MODULE} hook-prompt"
STOP_ENTRY = {"type": "command", "command": STOP_COMMAND, "timeout": 10}
PROMPT_ENTRY = {"type": "command", "command": PROMPT_COMMAND, "timeout": 5}
OTHER_STOP = {"type": "command", "command": "notify-send done"}
FIXTURE = {
    "model": "opus",
    "permissions": {"allow": ["Bash(git status)"]},
    "hooks": {
        "Stop": [{"hooks": [OTHER_STOP]}],
        "PreToolUse": [{"matcher": "Bash", "hooks": [{"type": "command", "command": "guard.sh"}]}],
    },
    "env": {"NAME": "café"},
}
BACKUP_NAME = re.compile(r"settings\.json\.easy-memory\.bak\.\d{8}T\d{6}Z(-\d+)?$")


def mode(path):
    return stat.S_IMODE(os.stat(path).st_mode)


def listing(folder):
    return sorted(os.listdir(folder))


class InstallTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="t006-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.config = self.tmp / "claude-config"
        self.config.mkdir()
        self.settings = self.config / "settings.json"
        self.home = self.tmp / ".easy-memory"
        self.fake_home = self.tmp / "home"
        self.fake_home.mkdir()
        # HUN-81: install also runs `claude mcp add`; only a FAKE claude may be reachable.
        self.bin = self.tmp / "bin"
        fake = fake_claude.install_fake_claude(self.bin)
        self.env = {**os.environ, **fake, "PATH": fake_claude.fake_path(self.bin),
                    "CLAUDE_CONFIG_DIR": str(self.config),
                    "EASY_MEMORY_HOME": str(self.home), "HOME": str(self.fake_home)}
        for patcher in (mock.patch.dict(os.environ, self.env, clear=True),
                        mock.patch.object(easy_memory.Path, "home", return_value=self.fake_home)):
            patcher.start()
            self.addCleanup(patcher.stop)
        # AC9 guard: the file under test is inside this test's temp folder.
        self.assertEqual(easy_memory.settings_path(), self.settings)
        self.assertEqual(Path(shutil.which("claude")).parent, self.bin)
        self.assertEqual(os.path.commonpath([self.tmp, easy_memory.store_home()]), str(self.tmp))

    def write_settings(self, data, indent=2):
        self.settings.write_text(json.dumps(data, indent=indent, ensure_ascii=False) + "\n",
                                 encoding="utf-8")

    def read_settings(self):
        return json.loads(self.settings.read_text(encoding="utf-8"))

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "stdin", io.StringIO("")), \
                redirect_stdout(out), redirect_stderr(err):
            code = easy_memory.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def backups(self):
        return [name for name in listing(self.config) if ".easy-memory.bak." in name]


class DryRunTest(InstallTestCase):
    def test_dry_run_prints_a_diff_and_writes_nothing(self):  # AC1, SC3
        self.write_settings(FIXTURE)
        before_bytes, before_list = self.settings.read_bytes(), listing(self.config)
        code, out, err = self.run_main("install", "--dry-run")
        self.assertEqual((code, err), (0, ""))
        self.assertIn(f"--- {self.settings}", out)
        self.assertIn(f"+++ {self.settings}", out)
        self.assertRegex(out, r"(?m)^\+.*" + re.escape(json.dumps(STOP_COMMAND)))
        self.assertRegex(out, r"(?m)^\+.*" + re.escape(json.dumps(PROMPT_COMMAND)))
        self.assertEqual(self.settings.read_bytes(), before_bytes)
        self.assertEqual(listing(self.config), before_list)  # not even a backup
        self.assertFalse(self.home.exists())

    def test_dry_run_diff_is_exactly_what_install_writes(self):  # AC1 "exact changes"
        self.write_settings(FIXTURE)
        _, out, _ = self.run_main("install", "--dry-run")
        before = self.settings.read_text(encoding="utf-8")
        self.assertEqual(self.run_main("install")[0], 0)
        after = self.settings.read_text(encoding="utf-8")
        want = "".join(difflib.unified_diff(before.splitlines(True), after.splitlines(True),
                                            str(self.settings), str(self.settings)))
        self.assertIn(want, out)

    def test_dry_run_on_a_missing_file_creates_nothing(self):  # AC1, edge: file missing
        code, out, _ = self.run_main("install", "--dry-run")
        self.assertEqual(code, 0)
        self.assertIn(json.dumps(STOP_COMMAND), out)
        self.assertEqual(listing(self.config), [])


class InstallTest(InstallTestCase):
    def test_install_backs_up_first_then_adds_both_hooks(self):  # AC2
        self.write_settings(FIXTURE)
        original = self.settings.read_bytes()
        code, out, err = self.run_main("install")
        self.assertEqual((code, err), (0, ""))
        [backup] = self.backups()
        self.assertRegex(backup, BACKUP_NAME)
        self.assertEqual((self.config / backup).read_bytes(), original)
        hooks = self.read_settings()["hooks"]
        self.assertEqual(hooks["Stop"][-1], {"hooks": [STOP_ENTRY]})
        self.assertEqual(hooks["UserPromptSubmit"], [{"hooks": [PROMPT_ENTRY]}])
        self.assertIn(str(self.settings), out)  # which file was changed
        self.assertIn(sys.executable, out)      # which python the hooks use
        self.assertIn(backup, out)

    def test_settings_dir_is_claude_config_dir_else_dot_claude(self):  # AC3
        self.assertEqual(easy_memory.settings_path(), self.config / "settings.json")
        with mock.patch.dict(os.environ, {"CLAUDE_CONFIG_DIR": ""}):
            self.assertEqual(easy_memory.settings_path(), self.fake_home / ".claude" / "settings.json")
        env = {k: v for k, v in os.environ.items() if k != "CLAUDE_CONFIG_DIR"}
        with mock.patch.dict(os.environ, env, clear=True):
            self.assertEqual(easy_memory.settings_path(), self.fake_home / ".claude" / "settings.json")

    def test_second_install_leaves_the_file_unchanged(self):  # AC4
        self.write_settings(FIXTURE)
        self.run_main("install")
        first, stamp, backups = self.settings.read_bytes(), os.stat(self.settings).st_mtime_ns, self.backups()
        code, out, _ = self.run_main("install")
        self.assertEqual(code, 0)
        self.assertEqual(self.settings.read_bytes(), first)
        self.assertEqual(os.stat(self.settings).st_mtime_ns, stamp)  # not rewritten
        self.assertEqual(self.backups(), backups)                    # no new backup
        self.assertIn("already installed", out)

    def test_other_keys_and_hooks_are_preserved(self):  # AC5, SC1
        self.write_settings(FIXTURE)
        self.run_main("install")
        data = self.read_settings()
        self.assertEqual(list(data), list(FIXTURE))  # key order kept
        self.assertEqual(data["hooks"]["Stop"][0], {"hooks": [OTHER_STOP]})  # appended, not replaced
        data["hooks"]["Stop"].pop()
        del data["hooks"]["UserPromptSubmit"]
        data["permissions"]["allow"].remove("mcp__easy-memory")  # HUN-81: the MCP allow rule
        self.assertEqual(data, FIXTURE)

    def test_moved_module_path_replaces_our_entries(self):  # no duplicates after a move
        old = {"type": "command", "command": "/usr/bin/python3 /old/place/easy_memory.py hook-stop",
               "timeout": 10}
        self.write_settings({"hooks": {"Stop": [{"hooks": [OTHER_STOP]}, {"hooks": [old]}]}})
        self.run_main("install")
        stop = self.read_settings()["hooks"]["Stop"]
        self.assertEqual(stop, [{"hooks": [OTHER_STOP]}, {"hooks": [STOP_ENTRY]}])

    def test_duplicate_entries_collapse_to_one(self):
        self.write_settings({"hooks": {"Stop": [{"hooks": [STOP_ENTRY]}, {"hooks": [STOP_ENTRY]}]}})
        self.run_main("install")
        self.assertEqual(self.read_settings()["hooks"]["Stop"], [{"hooks": [STOP_ENTRY]}])

    def test_missing_settings_file_is_created_with_only_our_entries(self):  # edge
        code, _, _ = self.run_main("install")
        self.assertEqual(code, 0)
        self.assertEqual(self.read_settings(), {"hooks": {"Stop": [{"hooks": [STOP_ENTRY]}],
                                                          "UserPromptSubmit": [{"hooks": [PROMPT_ENTRY]}]},
                                                "permissions": {"allow": ["mcp__easy-memory"]}})  # HUN-81
        self.assertEqual(self.backups(), [])  # nothing to back up
        self.assertEqual(mode(self.settings), 0o600)

    def test_missing_config_dir_is_an_error(self):
        shutil.rmtree(self.config)
        code, _, err = self.run_main("install")
        self.assertEqual(code, 1)
        self.assertIn("does not exist", err)
        self.assertFalse(self.config.exists())

    def test_file_mode_indentation_and_newline_are_kept(self):  # safety rule 3
        self.write_settings(FIXTURE, indent=4)
        self.settings.chmod(0o644)
        self.run_main("install")
        text = self.settings.read_text(encoding="utf-8")
        self.assertEqual(mode(self.settings), 0o644)
        self.assertTrue(text.startswith('{\n    "model": "opus",'))
        self.assertTrue(text.endswith("}\n"))
        self.assertIn("café", text)  # non-ASCII is not escaped

    def test_tab_indent_and_no_final_newline_are_kept(self):
        self.settings.write_text(json.dumps(FIXTURE, indent="\t"), encoding="utf-8")
        self.run_main("install")
        text = self.settings.read_text(encoding="utf-8")
        self.assertTrue(text.startswith('{\n\t"model": "opus",'))
        self.assertTrue(text.endswith("}"))

    def test_symlinked_settings_file_stays_a_symlink(self):
        target = self.tmp / "dotfiles-settings.json"
        target.write_text(json.dumps(FIXTURE, indent=2) + "\n", encoding="utf-8")
        self.settings.symlink_to(target)
        self.run_main("install")
        self.assertTrue(self.settings.is_symlink())
        self.assertIn("UserPromptSubmit", json.loads(target.read_text())["hooks"])

    def test_no_temp_file_is_left_behind(self):
        self.write_settings(FIXTURE)
        self.run_main("install")
        self.assertEqual([n for n in listing(self.config) if n.endswith(".tmp")], [])

    def test_module_path_with_spaces_is_quoted(self):  # edge
        with mock.patch.object(easy_memory, "__file__", "/a dir/easy_memory.py"), \
                mock.patch.object(sys, "executable", "/usr/bin/python3"):
            commands = easy_memory.hook_entries()
        self.assertEqual(commands["Stop"]["command"], "/usr/bin/python3 '/a dir/easy_memory.py' hook-stop")

    def test_installed_commands_run_and_exit_zero(self):  # the written command is valid
        self.run_main("install")
        hooks = self.read_settings()["hooks"]
        for event in ("Stop", "UserPromptSubmit"):
            command = hooks[event][0]["hooks"][0]["command"]
            res = subprocess.run(command, shell=True, input="{}", capture_output=True, text=True,
                                 env=self.env, cwd=self.tmp, timeout=30)
            self.assertEqual((res.returncode, res.stdout), (0, ""), event)


class InvalidSettingsTest(InstallTestCase):
    def assert_aborts(self, *argv):
        before_bytes, before_list = self.settings.read_bytes(), listing(self.config)
        code, out, err = self.run_main(*argv)
        self.assertNotEqual(code, 0)
        self.assertIn(str(self.settings), err)
        self.assertEqual(self.settings.read_bytes(), before_bytes)
        self.assertEqual(listing(self.config), before_list)  # no backup, no temp file
        return err

    def test_invalid_json_aborts_and_writes_nothing(self):  # AC6, SC2
        self.settings.write_text('{"model": "opus",,}\n', encoding="utf-8")
        self.assertIn("not valid JSON", self.assert_aborts("install"))
        self.assert_aborts("install", "--dry-run")
        self.assert_aborts("uninstall")

    def test_unexpected_shapes_abort(self):  # edge: hooks of an unexpected type
        for data in ([1, 2], {"hooks": []}, {"hooks": {"Stop": {"x": 1}}},
                     {"hooks": {"UserPromptSubmit": "echo"}}):
            self.write_settings(data)
            self.assert_aborts("install")
            self.assert_aborts("uninstall")

    def test_purge_does_not_run_when_settings_are_invalid(self):
        self.settings.write_text("nope", encoding="utf-8")
        (self.home / "k").mkdir(parents=True)
        self.assert_aborts("uninstall", "--purge")
        self.assertTrue(self.home.exists())


class UninstallTest(InstallTestCase):
    def test_uninstall_removes_only_our_entries_and_keeps_the_store(self):  # AC7, SC1
        self.write_settings(FIXTURE)
        self.run_main("install")
        (self.home / "abc" / "notes").mkdir(parents=True)
        (self.home / "abc" / "notes" / "n.json").write_text("{}")
        code, out, err = self.run_main("uninstall")
        self.assertEqual((code, err), (0, ""))
        self.assertEqual(self.read_settings()["hooks"]["Stop"], [{"hooks": [OTHER_STOP]}])
        self.assertTrue((self.home / "abc" / "notes" / "n.json").exists())
        self.assertIn(str(self.settings), out)

    def test_uninstall_keeps_a_user_hook_added_to_our_group(self):
        self.write_settings({"hooks": {"Stop": [{"hooks": [STOP_ENTRY, OTHER_STOP]}]}})
        self.run_main("uninstall")
        self.assertEqual(self.read_settings(), {"hooks": {"Stop": [{"hooks": [OTHER_STOP]}]}})

    def test_install_then_uninstall_restores_the_original_json(self):  # AC8
        for data in (FIXTURE, {"model": "opus"}, {}):
            self.write_settings(data)
            original = self.settings.read_bytes()
            self.run_main("install")
            self.run_main("uninstall")
            self.assertEqual(self.read_settings(), data)
            # a file in Claude Code's own style (2-space indent) comes back byte for byte
            self.assertEqual(self.settings.read_bytes(), original)

    def test_uninstall_backs_up_and_is_a_no_op_when_nothing_is_ours(self):
        self.write_settings(FIXTURE)
        before = self.settings.read_bytes()
        code, out, _ = self.run_main("uninstall")
        self.assertEqual(code, 0)
        self.assertEqual(self.settings.read_bytes(), before)
        self.assertEqual(self.backups(), [])
        self.assertIn("not installed", out)
        self.write_settings({"hooks": {"Stop": [{"hooks": [STOP_ENTRY]}]}})
        self.run_main("uninstall")
        self.assertEqual(len(self.backups()), 1)

    def test_uninstall_with_no_settings_file_writes_nothing(self):
        code, _, _ = self.run_main("uninstall")
        self.assertEqual(code, 0)
        self.assertEqual(listing(self.config), [])

    def test_purge_prints_the_size_then_deletes_the_store(self):  # AC7
        self.write_settings(FIXTURE)
        self.run_main("install")
        (self.home / "abc").mkdir(parents=True)
        (self.home / "abc" / "n.json").write_text("x" * 1500)
        (self.home / "hook.log").write_text("y" * 500)
        code, out, err = self.run_main("uninstall", "--purge")
        self.assertEqual((code, err), (0, ""))
        self.assertIn(str(self.home), out)
        self.assertIn("2000 bytes", out)
        self.assertLess(out.index("2000 bytes"), out.index("deleted"))
        self.assertFalse(self.home.exists())
        self.assertEqual(self.read_settings()["hooks"]["Stop"], [{"hooks": [OTHER_STOP]}])

    def test_purge_with_no_store_is_fine(self):
        code, out, _ = self.run_main("uninstall", "--purge")
        self.assertEqual(code, 0)
        self.assertIn("no store", out)

    def test_purge_refuses_unsafe_store_paths(self):  # safety rule 4
        victim = self.tmp / "data"
        victim.mkdir()
        (victim / "keep.txt").write_text("keep")
        repo_like = self.tmp / "easy-memory-mcp"  # a repo whose name contains easy-memory
        repo_like.mkdir()
        link = self.tmp / ".easy-memory-link"
        link.symlink_to(victim)
        self.write_settings({"hooks": {"Stop": [{"hooks": [STOP_ENTRY]}]}})
        before = self.settings.read_bytes()
        for unsafe in ("/", str(self.fake_home), str(self.tmp.parent), str(victim),
                       str(repo_like), str(link)):
            with mock.patch.dict(os.environ, {"EASY_MEMORY_HOME": unsafe}):
                code, _, err = self.run_main("uninstall", "--purge")
            self.assertEqual(code, 1, unsafe)
            self.assertIn("refusing", err)
        self.assertTrue((victim / "keep.txt").exists())
        self.assertTrue(repo_like.exists())
        self.assertTrue(self.fake_home.exists())
        self.assertEqual(self.settings.read_bytes(), before)  # refused before any edit
        self.assertEqual(self.backups(), [])


class ConcurrencyAndOutputTest(InstallTestCase):
    def test_a_change_between_read_and_write_aborts(self):
        self.write_settings(FIXTURE)
        real_load = easy_memory._load_settings

        def load_then_someone_edits(path):
            loaded = real_load(path)
            self.write_settings({**FIXTURE, "model": "sonnet"})
            return loaded
        with mock.patch.object(easy_memory, "_load_settings", load_then_someone_edits):
            code, _, err = self.run_main("install")
        self.assertEqual(code, 1)
        self.assertIn("changed while", err)
        self.assertEqual(self.read_settings()["model"], "sonnet")  # their edit survives
        self.assertEqual(self.backups(), [])

    def test_one_line_file_stays_one_line_and_diff_lines_do_not_merge(self):
        self.settings.write_text(json.dumps({"model": "opus"}), encoding="utf-8")
        _, out, _ = self.run_main("install", "--dry-run")
        self.assertRegex(out, r'(?m)^-\{"model": "opus"\}$')
        self.run_main("install")
        self.assertNotIn("\n", self.settings.read_text(encoding="utf-8"))


class ScriptTest(InstallTestCase):
    def test_runs_as_a_script_with_the_temp_config_dir(self):  # AC9: subprocess env is temp too
        self.write_settings(FIXTURE)
        res = subprocess.run([sys.executable, MODULE, "install", "--dry-run"], env=self.env,
                             capture_output=True, text=True, timeout=30)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertIn(str(self.settings), res.stdout)
        self.assertEqual(self.backups(), [])


if __name__ == "__main__":
    unittest.main()
