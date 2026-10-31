"""HUN-81 (T008): the `serve` MCP server (AC1-AC4, AC7) and the install/uninstall MCP step (AC5).

Safety: every test uses a temp EASY_MEMORY_HOME, HOME and CLAUDE_CONFIG_DIR (also in every
subprocess), and a FAKE `claude` first on PATH (tests/fake_claude.py). The real `claude`
is never run; setUp asserts that `claude` resolves into the temp folder.
AC6 (the live `claude -p` A3 test) is a manual procedure in tasks/TASK_REVIEW_HUN-81.md.
"""
import io
import json
import os
import queue
import shlex
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import easy_memory  # noqa: E402
from tests import fake_claude  # noqa: E402

MODULE = os.path.abspath(easy_memory.__file__)
PROTOCOL = "2025-06-18"
TOOLS = ["memory_forget", "memory_list", "memory_read", "memory_restore", "memory_search"]
ALLOW_RULE = "mcp__easy-memory"


class McpClient:
    """A `serve` subprocess spoken to over pipes (newline-delimited JSON-RPC)."""

    def __init__(self, cwd, env):
        self.proc = subprocess.Popen([sys.executable, MODULE, "serve"], cwd=cwd, env=env,
                                     stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                     stderr=subprocess.PIPE)
        self.lines = queue.Queue()
        self.raw = []
        threading.Thread(target=self._pump, daemon=True).start()
        self._next_id = 0

    def _pump(self):
        for line in self.proc.stdout:
            self.raw.append(line)
            self.lines.put(line)
        self.lines.put(None)

    def send_raw(self, data):
        self.proc.stdin.write(data if isinstance(data, bytes) else data.encode("utf-8"))
        self.proc.stdin.flush()

    def send(self, obj):
        self.send_raw(json.dumps(obj) + "\n")

    def recv(self, timeout=10):
        line = self.lines.get(timeout=timeout)
        self.assert_line(line)
        return json.loads(line)

    def assert_line(self, line):
        assert line is not None, "server closed stdout"
        assert line.endswith(b"\n") and line.count(b"\n") == 1, line
        msg = json.loads(line)
        assert msg.get("jsonrpc") == "2.0", msg  # nothing but JSON-RPC on stdout

    def no_more_output(self, wait=0.3):
        try:
            self.lines.get(timeout=wait)
        except queue.Empty:
            return True
        return False

    def request(self, method, params=None):
        self._next_id += 1
        msg = {"jsonrpc": "2.0", "id": self._next_id, "method": method}
        if params is not None:
            msg["params"] = params
        self.send(msg)
        reply = self.recv()
        assert reply.get("id") == self._next_id, reply
        return reply

    def call(self, name, arguments=None):
        reply = self.request("tools/call", {"name": name, "arguments": arguments or {}})
        return reply["result"]

    def text(self, name, arguments=None):
        result = self.call(name, arguments)
        return result["content"][0]["text"], bool(result.get("isError"))

    def close(self):
        self.proc.stdin.close()
        code = self.proc.wait(timeout=10)
        err = self.proc.stderr.read().decode("utf-8", "replace")
        self.proc.stdout.close()
        self.proc.stderr.close()
        return code, err


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="t008-")).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.bin = self.tmp / "bin"
        fake = fake_claude.install_fake_claude(self.bin)
        self.config = self.tmp / "claude-config"
        self.config.mkdir()
        self.settings = self.config / "settings.json"
        self.home = self.tmp / ".easy-memory"
        self.fake_home = self.tmp / "home"
        self.fake_home.mkdir()
        self.env = {**os.environ, **fake, "PATH": fake_claude.fake_path(self.bin),
                    "CLAUDE_CONFIG_DIR": str(self.config), "EASY_MEMORY_HOME": str(self.home),
                    "HOME": str(self.fake_home)}
        for patcher in (mock.patch.dict(os.environ, self.env, clear=True),
                        mock.patch.object(easy_memory.Path, "home", return_value=self.fake_home)):
            patcher.start()
            self.addCleanup(patcher.stop)
        # Safety guard: the only `claude` reachable is the fake one in this test's temp folder.
        self.assertEqual(Path(shutil.which("claude")).parent, self.bin)
        self.assertEqual(easy_memory.settings_path(), self.settings)
        self.assertEqual(os.path.commonpath([self.tmp, easy_memory.store_home()]), str(self.tmp))
        self.repo = self.make_repo("repo")

    def make_repo(self, name):
        repo = self.tmp / name
        (repo / "src").mkdir(parents=True)
        subprocess.run(["git", "init", "-q", str(repo)], check=True)
        for index in range(4):
            (repo / "src" / f"mod{index}.py").write_text(
                f"def shared_helper():\n    return {index}\n", encoding="utf-8")
        return repo

    def save(self, prompt, answer, files=None, repo=None):
        path = easy_memory.write_note(repo or self.repo, {
            "prompt": prompt, "answer": answer, "time": "2026-10-28T10:00:00Z",
            "session_id": "s1", "files": files or {}})
        return Path(path).stem

    def notes_dir(self, repo=None):
        return self.home / easy_memory.repo_key(repo or self.repo) / "notes"

    def client(self, cwd=None):
        client = McpClient(cwd or self.repo, self.env)
        self.addCleanup(self._finish, client)
        return client

    def _finish(self, client):
        if client.proc.poll() is None:
            client.proc.kill()
            client.proc.wait()
        for pipe in (client.proc.stdin, client.proc.stdout, client.proc.stderr):
            try:
                pipe.close()
            except (OSError, ValueError):
                pass

    def initialized(self, client=None):
        client = client or self.client()
        client.request("initialize", {"protocolVersion": PROTOCOL, "capabilities": {},
                                      "clientInfo": {"name": "t", "version": "0"}})
        client.send({"jsonrpc": "2.0", "method": "notifications/initialized"})
        return client


class ProtocolTest(Base):  # AC1
    def test_initialize_echoes_a_supported_version(self):
        client = self.client()
        for version in ("2024-11-05", "2025-03-26", PROTOCOL):
            reply = client.request("initialize", {"protocolVersion": version, "capabilities": {},
                                                  "clientInfo": {"name": "t", "version": "0"}})
            result = reply["result"]
            self.assertEqual(result["protocolVersion"], version)
            self.assertIn("tools", result["capabilities"])
            self.assertEqual(result["serverInfo"]["name"], "easy-memory")

    def test_initialize_with_an_unknown_version_answers_a_supported_one(self):
        client = self.client()
        reply = client.request("initialize", {"protocolVersion": "1999-01-01", "capabilities": {}})
        self.assertIn(reply["result"]["protocolVersion"], easy_memory.MCP_VERSIONS)
        reply = client.request("initialize", {})
        self.assertIn(reply["result"]["protocolVersion"], easy_memory.MCP_VERSIONS)

    def test_initialized_notification_gets_no_reply(self):
        client = self.initialized()
        self.assertTrue(client.no_more_output())
        self.assertEqual(client.request("ping")["result"], {})

    def test_tools_list_has_five_tools_with_schemas(self):
        client = self.initialized()
        tools = client.request("tools/list")["result"]["tools"]
        self.assertEqual(sorted(tool["name"] for tool in tools), TOOLS)
        by_name = {tool["name"]: tool for tool in tools}
        for tool in tools:
            self.assertTrue(tool["description"])
            self.assertEqual(tool["inputSchema"]["type"], "object")
        self.assertEqual(by_name["memory_search"]["inputSchema"]["required"], ["query"])
        self.assertEqual(by_name["memory_read"]["inputSchema"]["required"], ["id"])
        self.assertEqual(by_name["memory_forget"]["inputSchema"]["required"], ["id"])
        self.assertEqual(by_name["memory_restore"]["inputSchema"]["required"], ["id"])
        self.assertNotIn("required", by_name["memory_list"]["inputSchema"])

    def test_unknown_method_is_a_jsonrpc_error(self):
        client = self.initialized()
        reply = client.request("resources/list")
        self.assertEqual(reply["error"]["code"], -32601)
        self.assertNotIn("result", reply)

    def test_unknown_notification_gets_no_reply(self):
        client = self.initialized()
        client.send({"jsonrpc": "2.0", "method": "notifications/whatever"})
        client.send({"jsonrpc": "2.0", "method": "no/such/method"})
        self.assertTrue(client.no_more_output())
        self.assertEqual(client.request("ping")["result"], {})

    def test_unknown_tool_is_a_jsonrpc_error(self):
        client = self.initialized()
        reply = client.request("tools/call", {"name": "memory_edit", "arguments": {}})
        self.assertEqual(reply["error"]["code"], -32602)

    def test_stdout_holds_only_jsonrpc_lines_and_exit_is_zero_at_eof(self):
        client = self.initialized()
        self.save("q", "a" * 300)
        client.request("tools/list")
        client.text("memory_list")
        code, err = client.close()
        self.assertEqual(code, 0, err)
        self.assertEqual(len(client.raw), 3)  # initialize, tools/list, memory_list
        for line in client.raw:
            client.assert_line(line)

    def test_empty_stdin_ends_the_server_with_exit_zero_and_no_output(self):
        res = subprocess.run([sys.executable, MODULE, "serve"], env=self.env, cwd=self.repo,
                             stdin=subprocess.DEVNULL, capture_output=True, timeout=30)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(res.stdout, b"")

    def test_main_runs_the_loop_in_process(self):
        stdin = io.StringIO(json.dumps({"jsonrpc": "2.0", "id": 7, "method": "ping"}) + "\n")
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "stdin", stdin), redirect_stdout(out), redirect_stderr(err):
            code = easy_memory.main(["serve"])
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(out.getvalue()), {"jsonrpc": "2.0", "id": 7, "result": {}})
        self.assertEqual(err.getvalue(), "")


class ToolsTest(Base):  # AC2, AC3
    ANSWER = ("The invoice exporter lives in src/mod1.py and writes csv rows for billing.\n"
              + "More detail about the invoice export flow. " * 10)

    def cited(self):
        return {"src/mod1.py": easy_memory._sha256_file(self.repo / "src" / "mod1.py")}

    def test_the_server_cwd_decides_the_repo(self):  # AC2
        other = self.make_repo("other")
        mine = self.save("how does invoice export work", self.ANSWER)
        theirs = self.save("how does invoice export work", self.ANSWER, repo=other)
        text, _ = self.initialized(self.client(self.repo)).text("memory_list")
        self.assertIn(mine, text)
        self.assertNotIn(theirs, text)
        text, _ = self.initialized(self.client(other)).text("memory_list")
        self.assertIn(theirs, text)
        self.assertNotIn(mine, text)

    def test_a_subfolder_of_the_repo_uses_the_repo_store(self):  # AC2, E6
        note = self.save("how does invoice export work", self.ANSWER)
        text, _ = self.initialized(self.client(self.repo / "src")).text("memory_list")
        self.assertIn(note, text)

    def test_a_folder_outside_git_uses_its_own_store(self):  # edge: not a git repo
        plain = self.tmp / "plain"
        plain.mkdir()
        note = self.save("how does invoice export work", self.ANSWER, repo=plain)
        text, _ = self.initialized(self.client(plain)).text("memory_list")
        self.assertIn(note, text)

    def test_search_returns_the_hook_index_lines(self):  # AC3
        note_id = self.save("how does invoice export work", self.ANSWER, self.cited())
        self.save("unrelated gardening schedule", "Tomatoes need water twice a week. " * 10)
        easy_memory.build_weights(self.repo)
        note = [n for n in easy_memory.read_notes(self.repo) if n["id"] == note_id][0]
        want = easy_memory._index_line(note, os.path.realpath(self.repo))
        text, is_error = self.initialized().text("memory_search", {"query": "invoice export csv"})
        self.assertFalse(is_error)
        self.assertIn(want, text.splitlines())
        self.assertNotIn("gardening", text)
        data = {"prompt": "invoice export csv", "cwd": str(self.repo)}
        hook_text = easy_memory.prompt_index(data)
        self.assertIn(want, hook_text.splitlines())  # the very same line the hook adds

    def test_search_without_weights_still_matches_words_and_starts_no_build(self):
        note_id = self.save("how does invoice export work", self.ANSWER)
        text, is_error = self.initialized().text("memory_search", {"query": "invoice export"})
        self.assertFalse(is_error)
        self.assertIn(note_id, text)
        self.assertFalse((self.home / easy_memory.repo_key(self.repo) / "weights.lock").exists())
        self.assertFalse((self.home / easy_memory.repo_key(self.repo) / "weights.json").exists())

    def test_search_with_no_match_or_bad_query(self):
        self.save("how does invoice export work", self.ANSWER)
        client = self.initialized()
        text, is_error = client.text("memory_search", {"query": "zebra quantum"})
        self.assertFalse(is_error)
        self.assertIn("no matching notes", text.lower())
        for bad in ({}, {"query": ""}, {"query": 5}, {"query": "   "}):
            text, is_error = client.text("memory_search", bad)
            self.assertTrue(is_error, bad)

    def test_read_returns_the_full_note_and_no_flags_when_unchanged(self):
        note_id = self.save("how does invoice export work", self.ANSWER, self.cited())
        text, is_error = self.initialized().text("memory_read", {"id": note_id})
        self.assertFalse(is_error)
        for part in (note_id, "how does invoice export work", self.ANSWER, "src/mod1.py",
                     "2026-10-28T10:00:00Z"):
            self.assertIn(part, text)
        self.assertIn("changed since saving: none", text)

    def test_read_flags_changed_and_deleted_cited_files(self):
        files = {"src/mod1.py": easy_memory._sha256_file(self.repo / "src" / "mod1.py"),
                 "src/mod2.py": easy_memory._sha256_file(self.repo / "src" / "mod2.py")}
        note_id = self.save("how does invoice export work", self.ANSWER, files)
        (self.repo / "src" / "mod1.py").write_text("changed = True\n", encoding="utf-8")
        (self.repo / "src" / "mod2.py").unlink()
        text, _ = self.initialized().text("memory_read", {"id": note_id})
        self.assertIn("CHANGED:src/mod1.py", text)
        self.assertIn("DELETED:src/mod2.py", text)

    def test_read_caps_a_very_large_note(self):
        note_id = self.save("big", "x" * 30000)
        text, is_error = self.initialized().text("memory_read", {"id": note_id})
        self.assertFalse(is_error)
        self.assertIn("truncated", text)
        self.assertIn("30,000", text)
        shown = text.split("--- answer ---\n", 1)[1]
        self.assertEqual(shown.count("x"), easy_memory.MCP_READ_CHARS)

    def test_read_of_a_missing_note_is_an_error_result(self):
        text, is_error = self.initialized().text("memory_read", {"id": "20200101T000000000-deadbeef"})
        self.assertTrue(is_error)
        self.assertIn("not found", text)

    def test_list_is_newest_first_with_a_default_of_20(self):
        ids = []
        for index in range(25):
            ids.append(self.save(f"question number {index}", "answer text " * 30))
            time.sleep(0.003)
        client = self.initialized()
        text, is_error = client.text("memory_list")
        self.assertFalse(is_error)
        shown = [i for i in ids if i in text]
        self.assertEqual(shown, ids[-20:])
        self.assertLess(text.index(ids[-1]), text.index(ids[-2]))  # newest first
        self.assertNotIn(ids[0], text)
        text, _ = client.text("memory_list", {"limit": 3})
        self.assertEqual([i for i in ids if i in text], ids[-3:])
        text, is_error = client.text("memory_list", {"limit": "many"})
        self.assertTrue(is_error)

    def test_list_of_an_empty_store(self):
        text, is_error = self.initialized().text("memory_list")
        self.assertFalse(is_error)
        self.assertIn("no notes", text.lower())

    def test_forget_deletes_the_note_and_a_second_call_says_not_found(self):
        keep = self.save("keep me", "kept answer " * 30)
        gone = self.save("forget me", "gone answer " * 30)
        client = self.initialized()
        text, is_error = client.text("memory_forget", {"id": gone})
        self.assertFalse(is_error)
        self.assertFalse((self.notes_dir() / f"{gone}.json").exists())
        self.assertTrue((self.notes_dir() / f"{keep}.json").exists())
        text, is_error = client.text("memory_forget", {"id": gone})
        self.assertTrue(is_error)
        self.assertIn("not found", text)
        self.assertNotIn(gone, client.text("memory_list")[0])


class SecurityTest(Base):  # AC4
    BAD_IDS = ["../../etc/passwd", "..", "../x", "a/b", "/etc/passwd", "a\\b", "a b", "a..b",
               "x.json/../y", "%2e%2e%2f", "name;rm", "a\x00b", "é", "", "x" * 300, "a\nb"]

    def secret_files(self):
        """Files next to the notes that read/forget must never reach, even through an id."""
        store = self.notes_dir().parent
        (store / "secret.json").write_text(json.dumps(
            {"v": 1, "id": "secret", "prompt": "p", "answer": "TOPSECRET"}), encoding="utf-8")
        outside = self.tmp / "outside.json"
        outside.write_text(json.dumps({"v": 1, "id": "outside", "prompt": "p",
                                       "answer": "OUTSIDE"}), encoding="utf-8")
        return [store / "secret.json", outside]

    def test_bad_ids_are_rejected_for_read_and_forget(self):
        self.save("a note", "note answer " * 30)
        files = self.secret_files()
        client = self.initialized()
        for bad in self.BAD_IDS:
            for tool in ("memory_read", "memory_forget"):
                text, is_error = client.text(tool, {"id": bad})
                self.assertTrue(is_error, (tool, bad))
                self.assertNotIn("TOPSECRET", text)
                self.assertNotIn("OUTSIDE", text)
        for path in files:
            self.assertTrue(path.exists(), path)
        self.assertEqual(len(list(self.notes_dir().glob("*.json"))), 1)

    def test_a_non_string_id_is_rejected(self):
        client = self.initialized()
        for bad in (None, 5, ["a"], {"id": "a"}, True):
            for tool in ("memory_read", "memory_forget"):
                _, is_error = client.text(tool, {"id": bad})
                self.assertTrue(is_error, (tool, bad))
        for tool in ("memory_read", "memory_forget"):
            _, is_error = client.text(tool, {})
            self.assertTrue(is_error, tool)

    def test_a_symlink_in_the_notes_folder_is_not_followed(self):
        self.save("a note", "note answer " * 30)
        target = self.secret_files()[1]
        link = self.notes_dir() / "evil.json"
        link.symlink_to(target)
        client = self.initialized()
        text, is_error = client.text("memory_read", {"id": "evil"})
        self.assertTrue(is_error)
        self.assertNotIn("OUTSIDE", text)
        _, is_error = client.text("memory_forget", {"id": "evil"})
        self.assertTrue(is_error)
        self.assertTrue(target.exists())
        self.assertTrue(link.is_symlink())

    def test_a_note_in_another_repos_store_is_unreachable(self):
        other = self.make_repo("other")
        theirs = self.save("their note", "their answer " * 30, repo=other)
        client = self.initialized()
        for tool in ("memory_read", "memory_forget"):
            text, is_error = client.text(tool, {"id": theirs})
            self.assertTrue(is_error)
            self.assertNotIn("their answer", text)
        self.assertTrue((self.notes_dir(other) / f"{theirs}.json").exists())

    def test_ids_made_by_the_store_pass_the_rule(self):
        note_id = self.save("a note", "note answer " * 30)
        self.assertTrue(easy_memory.valid_note_id(note_id))
        self.assertFalse(easy_memory.valid_note_id("a/b"))
        self.assertFalse(easy_memory.valid_note_id(".."))
        self.assertTrue(easy_memory.valid_note_id("a.b-c_d"))


class MalformedInputTest(Base):  # AC7
    def test_garbage_does_not_crash_the_server(self):
        client = self.client()
        client.send_raw("this is not json\n")
        self.assertEqual(client.recv()["error"]["code"], -32700)
        client.send_raw(b"\xff\xfe\x00 {bad bytes}\n")
        self.assertEqual(client.recv()["error"]["code"], -32700)
        client.send_raw("{\"jsonrpc\": \"2.0\", \"id\": 1,\n")  # cut off
        self.assertEqual(client.recv()["error"]["code"], -32700)
        for odd in ("[]", "[1,2]", "\"text\"", "42", "null", "{}",
                    json.dumps({"jsonrpc": "2.0", "id": 9}),
                    json.dumps({"jsonrpc": "2.0", "id": 9, "method": 5}),
                    json.dumps({"jsonrpc": "2.0", "id": {"a": 1}, "method": "ping"})):
            client.send_raw(odd + "\n")
            reply = client.recv()
            self.assertIn("error", reply, odd)
            self.assertIn(reply["error"]["code"], (-32600, -32700), odd)
        client.send_raw("\n\n   \n")  # blank lines are ignored
        self.assertTrue(client.no_more_output())
        self.assertEqual(client.request("ping")["result"], {})  # still alive
        code, err = client.close()
        self.assertEqual(code, 0, err)

    def test_bad_params_do_not_crash_the_server(self):
        client = self.client()
        for params in (5, "x", [1], None):
            client.send({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": params})
            reply = client.recv()
            self.assertIn("error", reply)
        for params in ({"name": "memory_list", "arguments": [1]},
                       {"name": "memory_list", "arguments": "x"},
                       {"name": 5, "arguments": {}}, {}):
            client.send({"jsonrpc": "2.0", "id": 2, "method": "tools/call", "params": params})
            reply = client.recv()
            self.assertTrue("error" in reply or reply["result"].get("isError"), params)
        client.send({"jsonrpc": "2.0", "id": 3, "method": "initialize", "params": 7})
        self.assertIn("result", client.recv())
        self.assertEqual(client.request("ping")["result"], {})

    def test_a_corrupt_note_file_does_not_crash_list_search_or_read(self):
        good = self.save("good note about invoice export", "good answer " * 30)
        folder = self.notes_dir()
        (folder / "20200101T000000000-badbad00.json").write_text("{not json", encoding="utf-8")
        (folder / "20200101T000000001-badbad01.json").write_text("[1]", encoding="utf-8")
        client = self.initialized()
        text, is_error = client.text("memory_list")
        self.assertFalse(is_error)
        self.assertIn(good, text)
        _, is_error = client.text("memory_search", {"query": "invoice export"})
        self.assertFalse(is_error)
        _, is_error = client.text("memory_read", {"id": "20200101T000000000-badbad00"})
        self.assertTrue(is_error)
        self.assertEqual(client.request("ping")["result"], {})

    def test_an_oversize_line_is_rejected_and_the_next_line_still_works(self):
        stdin = io.StringIO("x" * 200 + "\n" + json.dumps(
            {"jsonrpc": "2.0", "id": 1, "method": "ping"}) + "\n")
        out = io.StringIO()
        with mock.patch.object(easy_memory, "MCP_MAX_LINE", 50), \
                mock.patch.object(sys, "stdin", stdin), redirect_stdout(out):
            code = easy_memory.main(["serve"])
        self.assertEqual(code, 0)
        replies = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual(len(replies), 2)
        self.assertEqual(replies[0]["error"]["code"], -32600)
        self.assertEqual(replies[1], {"jsonrpc": "2.0", "id": 1, "result": {}})

    def test_a_handler_crash_becomes_an_internal_error(self):
        stdin = io.StringIO(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"}) + "\n"
                            + json.dumps({"jsonrpc": "2.0", "id": 2, "method": "ping"}) + "\n")
        out = io.StringIO()
        calls = []

        def boom(*args):
            calls.append(args)
            if len(calls) == 1:
                raise RuntimeError("boom")
            return {}

        with mock.patch.object(easy_memory, "_mcp_dispatch", boom), \
                mock.patch.object(sys, "stdin", stdin), redirect_stdout(out):
            code = easy_memory.main(["serve"])
        self.assertEqual(code, 0)
        replies = [json.loads(line) for line in out.getvalue().splitlines()]
        self.assertEqual(replies[0]["error"]["code"], -32603)
        self.assertEqual(replies[1]["result"], {})
        self.assertIn("boom", (self.home / "hook.log").read_text(encoding="utf-8"))

    def test_the_client_closing_stdout_ends_the_server_quietly(self):
        stdin = io.StringIO(json.dumps({"jsonrpc": "2.0", "id": 1, "method": "ping"}) + "\n")

        class Broken(io.StringIO):
            def write(self, text):
                raise BrokenPipeError

        with mock.patch.object(sys, "stdin", stdin), redirect_stdout(Broken()):
            self.assertEqual(easy_memory.main(["serve"]), 0)


class InstallMcpTest(Base):  # AC5
    FIXTURE = {"model": "opus", "permissions": {"allow": ["Bash(git status)"], "deny": ["Read(.env)"]},
               "hooks": {"Stop": [{"hooks": [{"type": "command", "command": "notify-send done"}]}]}}
    ADD = ["mcp", "add", "--scope", "user", "easy-memory", "--", sys.executable, MODULE, "serve"]
    REMOVE = ["mcp", "remove", "--scope", "user", "easy-memory"]

    def write_settings(self, data):
        self.settings.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n",
                                 encoding="utf-8")

    def run_main(self, *argv, env=None):
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.dict(os.environ, env or {}), \
                mock.patch.object(sys, "stdin", io.StringIO("")), \
                redirect_stdout(out), redirect_stderr(err):
            code = easy_memory.main(list(argv))
        return code, out.getvalue(), err.getvalue()

    def calls(self):
        return fake_claude.read_calls(self.bin)

    def registered(self):
        return (self.bin / "registered").exists()

    def test_install_registers_the_server_and_adds_the_allow_rule(self):
        self.write_settings(self.FIXTURE)
        code, out, err = self.run_main("install")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.calls(), [self.ADD])
        self.assertTrue(self.registered())
        data = json.loads(self.settings.read_text(encoding="utf-8"))
        self.assertEqual(data["permissions"]["allow"], ["Bash(git status)", ALLOW_RULE])
        self.assertEqual(data["permissions"]["deny"], ["Read(.env)"])
        self.assertIn("Stop", data["hooks"])
        self.assertIn("UserPromptSubmit", data["hooks"])
        self.assertIn(shlex.join(["claude", *self.ADD]), out)

    def test_install_into_settings_without_permissions_creates_them(self):
        code, _, err = self.run_main("install")
        self.assertEqual(code, 0, err)
        data = json.loads(self.settings.read_text(encoding="utf-8"))
        self.assertEqual(data["permissions"], {"allow": [ALLOW_RULE]})

    def test_install_twice_is_idempotent(self):
        self.write_settings(self.FIXTURE)
        self.run_main("install")
        first = self.settings.read_text(encoding="utf-8")
        code, out, err = self.run_main("install")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.settings.read_text(encoding="utf-8"), first)
        self.assertEqual(json.loads(first)["permissions"]["allow"].count(ALLOW_RULE), 1)
        self.assertTrue(self.registered())
        # the second add found the server (fake: "already exists"), so it removed it and added it again
        self.assertEqual(self.calls(), [self.ADD, self.ADD, self.REMOVE, self.ADD])

    def test_dry_run_prints_the_command_and_changes_nothing(self):
        self.write_settings(self.FIXTURE)
        before = self.settings.read_text(encoding="utf-8")
        listing = sorted(os.listdir(self.config))
        code, out, err = self.run_main("install", "--dry-run")
        self.assertEqual(code, 0, err)
        self.assertEqual(self.settings.read_text(encoding="utf-8"), before)
        self.assertEqual(sorted(os.listdir(self.config)), listing)  # no backup file either
        self.assertEqual(self.calls(), [])  # claude was not run
        self.assertFalse(self.registered())
        self.assertIn(shlex.join(["claude", *self.ADD]), out)
        self.assertIn(ALLOW_RULE, out)  # the diff shows the new rule
        self.assertIn("dry run", out)

    def test_uninstall_unregisters_and_restores_the_original_json(self):
        for original in (self.FIXTURE, {}, {"model": "opus"},
                         {"permissions": {"allow": ["Bash(ls)"]}}, {"permissions": {"deny": ["Bash"]}}):
            with self.subTest(original=original):
                self.write_settings(original)
                before = self.settings.read_text(encoding="utf-8")
                self.run_main("install")
                self.assertNotEqual(self.settings.read_text(encoding="utf-8"), before)
                code, out, err = self.run_main("uninstall")
                self.assertEqual(code, 0, err)
                self.assertEqual(json.loads(self.settings.read_text(encoding="utf-8")), original)
                self.assertFalse(self.registered())
                self.assertEqual(self.calls()[-1], self.REMOVE)

    def test_uninstall_when_never_registered_still_succeeds(self):
        self.write_settings(self.FIXTURE)
        code, out, err = self.run_main("uninstall")  # the fake says "No MCP server found"
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(self.settings.read_text(encoding="utf-8")), self.FIXTURE)
        self.assertIn(shlex.join(["claude", *self.REMOVE]), out + err)

    def test_install_without_claude_still_installs_hooks_and_prints_the_manual_command(self):
        empty = self.tmp / "empty-path"
        empty.mkdir()
        self.assertIsNone(shutil.which("claude", path=str(empty)))
        self.write_settings(self.FIXTURE)
        code, out, err = self.run_main("install", env={"PATH": str(empty)})
        self.assertEqual(code, 0, err)
        data = json.loads(self.settings.read_text(encoding="utf-8"))
        self.assertIn("UserPromptSubmit", data["hooks"])
        self.assertIn(ALLOW_RULE, data["permissions"]["allow"])
        self.assertEqual(self.calls(), [])
        message = out + err
        self.assertIn("claude", message)
        self.assertIn("not found", message)
        self.assertIn(shlex.join(["claude", *self.ADD]), message)

    def test_uninstall_without_claude_still_removes_hooks_and_the_rule(self):
        empty = self.tmp / "empty-path"
        empty.mkdir()
        self.write_settings(self.FIXTURE)
        self.run_main("install")
        code, out, err = self.run_main("uninstall", env={"PATH": str(empty)})
        self.assertEqual(code, 0, err)
        self.assertEqual(json.loads(self.settings.read_text(encoding="utf-8")), self.FIXTURE)
        self.assertIn(shlex.join(["claude", *self.REMOVE]), out + err)

    def test_a_failing_claude_fails_the_install_but_keeps_the_hooks(self):
        self.write_settings(self.FIXTURE)
        code, out, err = self.run_main("install", env={"FAKE_CLAUDE_FAIL": "1"})
        self.assertEqual(code, 1)
        data = json.loads(self.settings.read_text(encoding="utf-8"))
        self.assertIn("UserPromptSubmit", data["hooks"])
        self.assertIn(shlex.join(["claude", *self.ADD]), err)  # the manual command

    def test_a_failing_claude_does_not_fail_the_uninstall(self):
        self.write_settings(self.FIXTURE)
        self.run_main("install")
        code, out, err = self.run_main("uninstall", env={"FAKE_CLAUDE_FAIL": "1"})
        self.assertEqual(code, 0)
        self.assertEqual(json.loads(self.settings.read_text(encoding="utf-8")), self.FIXTURE)
        self.assertIn(shlex.join(["claude", *self.REMOVE]), out + err)

    def test_bad_settings_stop_before_claude_is_run(self):
        self.settings.write_text("{not json", encoding="utf-8")
        code, _, _ = self.run_main("install")
        self.assertEqual(code, 1)
        self.assertEqual(self.calls(), [])
        self.settings.write_text(json.dumps({"permissions": {"allow": "Bash"}}), encoding="utf-8")
        code, _, _ = self.run_main("install")
        self.assertEqual(code, 1)
        self.assertEqual(self.calls(), [])

    def test_install_as_a_script_uses_only_the_fake_claude(self):  # subprocess env is temp too
        self.write_settings(self.FIXTURE)
        res = subprocess.run([sys.executable, MODULE, "install"], env=self.env,
                             capture_output=True, text=True, stdin=subprocess.DEVNULL, timeout=30)
        self.assertEqual(res.returncode, 0, res.stderr)
        self.assertEqual(self.calls(), [self.ADD])


if __name__ == "__main__":
    unittest.main()
