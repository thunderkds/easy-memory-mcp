"""HUN-134: easy-memory as a Claude Code plugin (marketplace, hooks, MCP, double-install guard).

Safety: every subprocess gets a temp CLAUDE_CONFIG_DIR, EASY_MEMORY_HOME and HOME, so the real
~/.claude*, any real settings file and the real ~/.easy-memory are never read or written.
"""
import io
import json
import os
import shutil
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

PLUGIN = ROOT / "plugin"
PLUGIN_SCRIPT = PLUGIN / "easy_memory.py"
ROOT_SCRIPT = ROOT / "easy_memory.py"
ANSWER = "The store writes notes by temp file and atomic rename. " * 10


def load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def plugin_command(name):
    return f'python3 "${{CLAUDE_PLUGIN_ROOT}}/easy_memory.py" {name}'


class ManifestTest(unittest.TestCase):
    def test_marketplace_lists_one_plugin_in_plugin_folder(self):
        market = load(ROOT / ".claude-plugin" / "marketplace.json")
        self.assertEqual(market["name"], "easy-memory")
        self.assertEqual([(p["name"], p["source"]) for p in market["plugins"]],
                         [("easy-memory", "./plugin")])

    def test_plugin_manifest_name_and_version(self):
        manifest = load(PLUGIN / ".claude-plugin" / "plugin.json")
        self.assertEqual(manifest["name"], "easy-memory")
        self.assertEqual(manifest["version"], "0.2.0")

    def test_hooks_match_hook_events(self):
        hooks = load(PLUGIN / "hooks" / "hooks.json")["hooks"]
        expected = {event: [{"hooks": [{"type": "command", "command": plugin_command(name),
                                        "timeout": timeout}]}]
                    for event, (name, timeout) in easy_memory.HOOK_EVENTS.items()}
        self.assertEqual(hooks, expected)

    def test_mcp_server_runs_serve(self):
        servers = load(PLUGIN / ".mcp.json")["mcpServers"]
        self.assertEqual(servers, {easy_memory.MCP_NAME: {
            "command": "python3", "args": ["${CLAUDE_PLUGIN_ROOT}/easy_memory.py", "serve"]}})

    def test_plugin_script_is_byte_identical_to_root(self):
        self.assertEqual(PLUGIN_SCRIPT.read_bytes(), ROOT_SCRIPT.read_bytes())

    def test_no_repo_dev_kit_inside_plugin(self):
        for name in ("agents", "skills", "commands"):
            self.assertFalse((PLUGIN / name).exists(), name)


class PluginRunTestCase(unittest.TestCase):
    """Runs the plugin's easy_memory.py the way Claude Code does, in temp folders."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hun134-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.config = self.tmp / "claude-config"
        self.config.mkdir()
        self.settings = self.config / "settings.json"
        self.home = self.tmp / "store"
        self.repo = self.tmp / "repo"
        self.repo.mkdir()
        (self.tmp / "home").mkdir()
        self.env = {**os.environ, "CLAUDE_CONFIG_DIR": str(self.config),
                    "EASY_MEMORY_HOME": str(self.home), "HOME": str(self.tmp / "home"),
                    "CLAUDE_PLUGIN_ROOT": str(PLUGIN)}

    def old_install(self):
        cmd = f"{sys.executable} {ROOT_SCRIPT}"
        self.settings.write_text(json.dumps({"hooks": {
            "Stop": [{"hooks": [{"type": "command", "command": f"{cmd} hook-stop"}]}],
            "UserPromptSubmit": [{"hooks": [{"type": "command",
                                             "command": f"{cmd} hook-prompt"}]}]}}))

    def run_hook(self, name, data, script=PLUGIN_SCRIPT):
        return subprocess.run([sys.executable, str(script), name], input=json.dumps(data),
                              capture_output=True, text=True, env=self.env, timeout=30)

    def stop(self, script=PLUGIN_SCRIPT):
        transcript = self.tmp / "t.jsonl"
        transcript.write_text(json.dumps({"type": "user", "message": {
            "role": "user", "content": "how does the store write notes"}}) + "\n")
        return self.run_hook("hook-stop", {"cwd": str(self.repo), "session_id": "s1",
                                           "transcript_path": str(transcript),
                                           "last_assistant_message": ANSWER}, script)

    def notes(self):
        return sorted(self.home.glob("*/notes/*.json"))

    def prompt_log(self):
        return sorted(self.home.glob("*/prompts.log"))


class DoubleInstallTest(PluginRunTestCase):
    def test_plugin_stop_hook_saves_nothing_when_old_hooks_installed(self):
        self.old_install()
        res = self.stop()
        self.assertEqual((res.returncode, res.stdout, res.stderr), (0, "", ""))
        self.assertEqual(self.notes(), [])

    def test_plugin_prompt_hook_does_nothing_when_old_hooks_installed(self):
        self.old_install()
        res = self.run_hook("hook-prompt", {"cwd": str(self.repo), "session_id": "s1",
                                            "prompt": "store notes"})
        self.assertEqual((res.returncode, res.stdout), (0, ""))
        self.assertEqual(self.prompt_log(), [])

    def test_one_note_per_turn_with_both_installed(self):
        self.old_install()
        self.stop()  # the plugin's hook
        self.stop(script=ROOT_SCRIPT)  # the old hook (CLAUDE_PLUGIN_ROOT may leak into it)
        self.assertEqual(len(self.notes()), 1)

    def test_plugin_stop_hook_saves_note_without_old_hooks(self):
        res = self.stop()
        self.assertEqual(res.returncode, 0)
        self.assertEqual(len(self.notes()), 1)

    def test_plugin_prompt_hook_runs_without_old_hooks(self):
        res = self.run_hook("hook-prompt", {"cwd": str(self.repo), "session_id": "s1",
                                            "prompt": "store notes"})
        self.assertEqual(res.returncode, 0)
        self.assertEqual(len(self.prompt_log()), 1)

    def test_invalid_settings_counts_as_no_old_hooks(self):
        self.settings.write_text("{not json")
        res = self.stop()
        self.assertEqual(res.returncode, 0)
        self.assertEqual(len(self.notes()), 1)

    def test_other_plugin_hooks_in_settings_do_not_count(self):
        self.settings.write_text(json.dumps({"hooks": {"Stop": [{"hooks": [
            {"type": "command", "command": "notify-send done"}]}]}}))
        self.stop()
        self.assertEqual(len(self.notes()), 1)


class BinWrapperTest(PluginRunTestCase):
    def test_switch_and_report_run_through_wrapper(self):
        wrapper = PLUGIN / "bin" / "easy-memory"
        self.assertTrue(os.access(wrapper, os.X_OK))
        env = {**self.env, "PATH": f"{PLUGIN / 'bin'}{os.pathsep}{os.environ['PATH']}"}
        switch = subprocess.run(["easy-memory", "switch", "on"], cwd=self.repo, env=env,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(switch.returncode, 0, switch.stderr)
        self.assertIn("switch: on", switch.stdout)
        report = subprocess.run(["easy-memory", "report"], cwd=self.repo, env=env,
                                capture_output=True, text=True, timeout=30)
        self.assertEqual(report.returncode, 0, report.stderr)


class InstallWarningTest(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hun134-install-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.config = self.tmp / "claude-config"
        self.config.mkdir()
        self.settings = self.config / "settings.json"
        self.bin = self.tmp / "bin"
        fake = fake_claude.install_fake_claude(self.bin)
        env = {**os.environ, **fake, "PATH": fake_claude.fake_path(self.bin),
               "CLAUDE_CONFIG_DIR": str(self.config),
               "EASY_MEMORY_HOME": str(self.tmp / "store"), "HOME": str(self.tmp)}
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)
        self.assertEqual(easy_memory.settings_path(), self.settings)

    def run_main(self, *argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = easy_memory.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def test_install_warns_and_changes_nothing_when_plugin_enabled(self):
        text = json.dumps({"enabledPlugins": {"easy-memory@easy-memory": True}}, indent=2) + "\n"
        self.settings.write_text(text)
        for argv in (["install"], ["install", "--dry-run"]):
            code, out, err = self.run_main(*argv)
            self.assertEqual(code, 0)
            self.assertEqual(out, "")
            self.assertEqual(len(err.splitlines()), 1, err)
            self.assertIn("plugin", err)
            self.assertEqual(self.settings.read_text(), text)
            self.assertEqual(sorted(os.listdir(self.config)), ["settings.json"])
            self.assertEqual(fake_claude.read_calls(self.bin), [])

    def test_install_proceeds_when_plugin_disabled(self):
        self.settings.write_text(json.dumps({"enabledPlugins": {"easy-memory@easy-memory": False}}))
        code, _, _ = self.run_main("install")
        self.assertEqual(code, 0)
        self.assertIn("hooks", json.loads(self.settings.read_text()))


if __name__ == "__main__":
    unittest.main()
