"""HUN-136 (M7, kit K-R4): a note saved by the Stop hook is found by memory_search within 1 s.

Scripted run, all subprocesses: `easy_memory.py hook-stop` with a fixture Stop input, then at
once `easy_memory.py serve` (JSON-RPC over stdio) and `memory_search`. The clock starts when
the hook process has exited, so spawning the server, the handshake and the search all count.

Safety: every subprocess gets a temp HOME, CLAUDE_CONFIG_DIR and EASY_MEMORY_HOME; the real
~/.claude* and ~/.easy-memory are never read or written.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from tests.test_t008_mcp import McpClient, PROTOCOL  # noqa: E402

PLUGIN = ROOT / "plugin"
ROOT_SCRIPT = ROOT / "easy_memory.py"
PLUGIN_SCRIPT = PLUGIN / "easy_memory.py"
LIMIT_SECONDS = 1.0
PROMPT = "how does the invoice exporter pick the csv delimiter"
ANSWER = ("The invoice exporter in src/export.py picks the csv delimiter from the locale table: "
          "a comma for most locales and a semicolon where the comma is the decimal mark. "
          "The helper in src/locale_table.py holds that table, so a new locale needs one row "
          "there and no change to the exporter itself. See src/export.py:3 for the choice.")
QUERY = "invoice exporter csv delimiter locale"


class SaveSearchTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="hun136-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.config = self.tmp / "claude-config"
        self.config.mkdir()
        (self.tmp / "home").mkdir()
        self.store = self.tmp / "store"
        self.env = {**os.environ, "HOME": str(self.tmp / "home"),
                    "CLAUDE_CONFIG_DIR": str(self.config), "EASY_MEMORY_HOME": str(self.store)}
        self.env.pop("CLAUDE_PLUGIN_ROOT", None)
        for name in ("HOME", "CLAUDE_CONFIG_DIR", "EASY_MEMORY_HOME"):  # safety guard
            self.assertEqual(os.path.commonpath([self.tmp, self.env[name]]), str(self.tmp))
        self.repo = self.make_repo(self.tmp / "repo")
        self.script = ROOT_SCRIPT

    def make_repo(self, repo):
        (repo / "src").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(repo)], check=True, env=self.env)
        (repo / "src" / "export.py").write_text(
            "from locale_table import delimiter\n\ndef export(rows, locale):\n"
            "    return delimiter(locale).join(rows)\n", encoding="utf-8")
        (repo / "src" / "locale_table.py").write_text(
            "TABLE = {'en': ',', 'de': ';'}\n\ndef delimiter(locale):\n    return TABLE[locale]\n",
            encoding="utf-8")
        for index in range(4):  # a few more files, so word weights have a corpus
            (repo / "src" / f"mod{index}.py").write_text(
                f"def helper_{index}():\n    return {index}\n", encoding="utf-8")
        return repo

    def run_tool(self, *args, stdin=None, timeout=30):
        return subprocess.run([sys.executable, str(self.script), *args], input=stdin,
                              capture_output=True, text=True, cwd=str(self.repo), env=self.env,
                              timeout=timeout)

    def switch_on(self):
        res = self.run_tool("switch", "--repo", str(self.repo), "on")
        self.assertEqual(res.returncode, 0, res.stderr)

    def build_weights(self):
        code = ("import sys; sys.path.insert(0, sys.argv[1]); import easy_memory; "
                "easy_memory.build_weights(sys.argv[2])")
        subprocess.run([sys.executable, "-c", code, str(self.script.parent), str(self.repo)],
                       check=True, env=self.env, timeout=60)
        self.assertTrue(list(self.store.glob("*/weights.json")))

    def stop_input(self):
        transcript = self.tmp / "transcript.jsonl"
        transcript.write_text(json.dumps({"type": "user", "message": {
            "role": "user", "content": PROMPT}}) + "\n", encoding="utf-8")
        return json.dumps({"cwd": str(self.repo), "session_id": "s1",
                           "transcript_path": str(transcript),
                           "last_assistant_message": ANSWER})

    def save_then_search(self):
        """Run hook-stop, then at once serve + memory_search. Returns (note id, text, seconds)."""
        hook = self.run_tool("hook-stop", stdin=self.stop_input())
        done = time.monotonic()  # the hook process has exited
        self.assertEqual((hook.returncode, hook.stdout, hook.stderr), (0, "", ""))
        client = McpClient(self.repo, self.env)
        self.addCleanup(client.proc.kill)
        client.request("initialize", {"protocolVersion": PROTOCOL, "capabilities": {},
                                      "clientInfo": {"name": "t", "version": "0"}})
        client.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        text, is_error = client.text("memory_search", {"query": QUERY})
        elapsed = time.monotonic() - done
        client.close()
        self.assertFalse(is_error, text)
        notes = sorted(self.store.glob("*/notes/*.json"))
        self.assertEqual(len(notes), 1)
        self.last_elapsed = elapsed
        print(f"\n{self.id().split('.')[-1]}: save->search {elapsed:.3f} s", file=sys.stderr)
        return notes[0].stem, text, elapsed

    def assert_found_at_once(self):
        note_id, text, elapsed = self.save_then_search()
        self.assertIn(note_id, text)
        self.assertLess(elapsed, LIMIT_SECONDS)


class SaveSearchTest(SaveSearchTestCase):  # AC1
    def test_note_is_found_at_once_with_word_weights(self):
        self.switch_on()
        self.build_weights()
        self.assert_found_at_once()

    def test_note_is_found_at_once_without_word_weights(self):
        self.switch_on()
        self.assertFalse(list(self.store.glob("*/weights.json")))
        self.assert_found_at_once()

    def test_a_query_with_no_shared_word_does_not_find_the_note(self):
        # The floor is the one way a saved note can stay hidden: prove the test can fail.
        self.switch_on()
        self.build_weights()
        self.run_tool("hook-stop", stdin=self.stop_input())
        client = McpClient(self.repo, self.env)
        self.addCleanup(client.proc.kill)
        client.request("initialize", {"protocolVersion": PROTOCOL, "capabilities": {},
                                      "clientInfo": {"name": "t", "version": "0"}})
        text, _ = client.text("memory_search", {"query": "kubernetes ingress certificate rotation"})
        client.close()
        self.assertEqual(text, "No matching notes.")


class PluginSaveSearchTest(SaveSearchTestCase):  # AC2
    def setUp(self):
        super().setUp()
        self.script = PLUGIN_SCRIPT
        self.env["CLAUDE_PLUGIN_ROOT"] = str(PLUGIN)
        # Throwaway settings with no easy-memory hooks, so the plugin does not defer.
        (self.config / "settings.json").write_text(json.dumps({"enabledPlugins": {
            "easy-memory@easy-memory": True}}), encoding="utf-8")

    def test_plugin_note_is_found_at_once_with_word_weights(self):
        self.switch_on()
        self.build_weights()
        self.assert_found_at_once()

    def test_plugin_note_is_found_at_once_without_word_weights(self):
        self.switch_on()
        self.assert_found_at_once()

    def test_plugin_with_old_hooks_in_settings_saves_nothing(self):
        # The third likely cause of a "missing" note: the plugin hook defers to the old hooks.
        cmd = f"{sys.executable} {ROOT_SCRIPT}"
        (self.config / "settings.json").write_text(json.dumps({"hooks": {"Stop": [
            {"hooks": [{"type": "command", "command": f"{cmd} hook-stop"}]}]}}))
        hook = self.run_tool("hook-stop", stdin=self.stop_input())
        self.assertEqual((hook.returncode, hook.stdout, hook.stderr), (0, "", ""))
        self.assertEqual(list(self.store.glob("*/notes/*.json")), [])


if __name__ == "__main__":
    unittest.main()
