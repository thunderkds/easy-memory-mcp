"""HUN-75 (T002): Stop hook saves one note per turn. Standard library only.

Every test uses temp folders and EASY_MEMORY_HOME; nothing touches the real
home, the real Claude settings or the real ~/.easy-memory. Transcripts are
synthetic.
"""
import hashlib
import io
import json
import math
import os
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import easy_memory  # noqa: E402

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com",
       "-c", "commit.gpgsign=false"]
SCRIPT = str(ROOT / "easy_memory.py")


def run_git(cwd, *args):
    subprocess.run([*GIT, *args], cwd=cwd, check=True, capture_output=True)


def mode(path):
    return stat.S_IMODE(os.stat(path).st_mode)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def user_entry(content, **extra):
    return {"type": "user", "message": {"role": "user", "content": content}, **extra}


def tool_result_entry():
    return user_entry([{"type": "tool_result", "tool_use_id": "t1", "content": "ok"}])


def assistant_entry(text):
    return {"type": "assistant",
            "message": {"role": "assistant", "content": [{"type": "text", "text": text}]}}


def long_answer(*cites, size=500):
    """An answer of at least size characters that mentions every path in cites."""
    text = "Looked at " + ", ".join(cites) + ". "
    return text + "Detail sentence. " * (size // 10)


class HookTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="t002-")).resolve()
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(self.tmp)]))
        self.home = self.tmp / "store-home"
        patcher = mock.patch.dict(os.environ, {"EASY_MEMORY_HOME": str(self.home)})
        patcher.start()
        self.addCleanup(patcher.stop)
        real_popen = subprocess.Popen

        def popen(argv, *args, **kwargs):  # the report refresh starts no real process (HUN-197)
            if "--release-lock" in argv and "report" in argv:
                return mock.MagicMock()
            return real_popen(argv, *args, **kwargs)
        popen_patcher = mock.patch.object(easy_memory.subprocess, "Popen", popen)
        popen_patcher.start()
        self.addCleanup(popen_patcher.stop)

    def make_repo(self, files=None):
        repo = self.tmp / "repo"
        repo.mkdir()
        run_git(repo, "init", "-q")
        for rel, body in (files or {"src/a.py": "x = 1\n"}).items():
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_bytes(body if isinstance(body, bytes) else body.encode())
        run_git(repo, "add", ".")
        run_git(repo, "commit", "-q", "-m", "init")
        return repo

    def write_transcript(self, entries, tail=""):
        path = self.tmp / "transcript.jsonl"
        path.write_text("".join(json.dumps(e) + "\n" for e in entries) + tail)
        return path

    def stop_input(self, repo, answer, transcript=None, **extra):
        data = {"session_id": "sess-1", "hook_event_name": "Stop", "cwd": str(repo),
                "transcript_path": str(transcript or self.write_transcript(
                    [user_entry("what is in a.py?"), assistant_entry(answer)])),
                "stop_hook_active": False, "last_assistant_message": answer}
        data.update(extra)
        return json.dumps(data)

    def run_hook(self, stdin_text):
        """Run hook-stop in process; return (exit code, stdout, stderr)."""
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "stdin", io.StringIO(stdin_text)), \
                redirect_stdout(out), redirect_stderr(err):
            code = easy_memory.main(["hook-stop"])
        return code, out.getvalue(), err.getvalue()

    def notes(self, repo):
        return easy_memory.read_notes(repo)

    def log_lines(self):
        log = self.home / "hook.log"
        return log.read_text().splitlines() if log.exists() else []


class SaveNoteTest(HookTestCase):
    def test_writes_one_note_with_all_fields_and_file_hash(self):  # AC1, SC1
        repo = self.make_repo()
        answer = long_answer("src/a.py")
        code, out, _ = self.run_hook(self.stop_input(repo, answer))
        self.assertEqual((code, out), (0, ""))
        notes = self.notes(repo)
        self.assertEqual(len(notes), 1)
        note = notes[0]
        self.assertEqual(note["prompt"], "what is in a.py?")
        self.assertEqual(note["answer"], answer)
        self.assertEqual(note["session_id"], "sess-1")
        self.assertEqual(note["files"], {"src/a.py": sha(b"x = 1\n")})
        self.assertRegex(note["time"], r"^\d{4}-\d\d-\d\dT\d\d:\d\d:\d\dZ$")
        self.assertEqual(self.log_lines(), [])

    def test_note_files_and_folders_are_private(self):  # NFR-003 via write_note
        repo = self.make_repo()
        self.run_hook(self.stop_input(repo, long_answer("src/a.py")))
        key_dir = self.home / easy_memory.repo_key(repo)
        for folder in (self.home, key_dir, key_dir / "notes"):
            self.assertEqual(mode(folder), 0o700, folder)
        (note_file,) = (key_dir / "notes").iterdir()
        self.assertEqual(mode(note_file), 0o600)

    def test_two_turns_make_two_notes(self):
        repo = self.make_repo()
        self.run_hook(self.stop_input(repo, long_answer("src/a.py")))
        self.run_hook(self.stop_input(repo, long_answer("src/a.py", size=600)))
        self.assertEqual(len(self.notes(repo)), 2)

    def test_answer_without_citations_has_empty_files(self):
        repo = self.make_repo()
        self.run_hook(self.stop_input(repo, long_answer()))
        self.assertEqual(self.notes(repo)[0]["files"], {})

    def test_cwd_in_subfolder_uses_repo_relative_paths_and_same_store(self):
        repo = self.make_repo({"src/a.py": "x = 1\n", "sub/keep.txt": "k"})
        data = json.loads(self.stop_input(repo, long_answer("src/a.py")))
        data["cwd"] = str(repo / "sub")
        self.run_hook(json.dumps(data))
        self.assertEqual(list(self.notes(repo)[0]["files"]), ["src/a.py"])

    def test_worktree_note_lands_in_main_repo_store(self):
        repo = self.make_repo()
        wt = self.tmp / "wt"
        run_git(repo, "worktree", "add", "-q", "-b", "feat", str(wt))
        self.run_hook(self.stop_input(wt, long_answer("src/a.py")))
        self.assertEqual(len(self.notes(repo)), 1)
        self.assertEqual(list(self.notes(repo)[0]["files"]), ["src/a.py"])

    def test_non_git_folder_still_saves_with_direct_paths_only(self):
        plain = self.tmp / "plain"
        (plain / "src").mkdir(parents=True)
        (plain / "src" / "a.py").write_text("x = 1\n")
        (plain / "src" / "b.py").write_text("y = 2\n")
        self.run_hook(self.stop_input(plain, long_answer("src/a.py", "b.py")))
        # b.py is a bare name: there is no tracked-file list outside git, so it is ignored.
        self.assertEqual(list(self.notes(plain)[0]["files"]), ["src/a.py"])

    def test_repo_is_byte_identical_after_hook(self):  # FR-002
        repo = self.make_repo()
        before = subprocess.run(["git", "status", "--porcelain", "--ignored"], cwd=repo,
                                capture_output=True, text=True).stdout
        listing = sorted(str(p) for p in repo.rglob("*") if ".git/" not in str(p))
        self.run_hook(self.stop_input(repo, long_answer("src/a.py")))
        after = subprocess.run(["git", "status", "--porcelain", "--ignored"], cwd=repo,
                               capture_output=True, text=True).stdout
        self.assertEqual(after, before)
        self.assertEqual(sorted(str(p) for p in repo.rglob("*") if ".git/" not in str(p)),
                         listing)


class PromptTest(HookTestCase):
    def prompt_for(self, entries, tail=""):
        repo = self.make_repo()
        transcript = self.write_transcript(entries, tail)
        self.run_hook(self.stop_input(repo, long_answer(), transcript))
        notes = self.notes(repo)
        return notes[0]["prompt"] if notes else None

    def test_skips_tool_results_back_to_real_prompt(self):  # AC2
        got = self.prompt_for([
            user_entry("first question"), assistant_entry("a"),
            user_entry("the real prompt"), assistant_entry("let me look"),
            tool_result_entry(), assistant_entry("more"), tool_result_entry(),
            assistant_entry("final")])
        self.assertEqual(got, "the real prompt")

    def test_uses_last_prompt_not_first(self):  # A6
        got = self.prompt_for([user_entry("one"), assistant_entry("a"),
                               user_entry("two"), assistant_entry("b")])
        self.assertEqual(got, "two")

    def test_text_blocks_in_list_content(self):
        got = self.prompt_for([user_entry([{"type": "text", "text": "typed in blocks"}])])
        self.assertEqual(got, "typed in blocks")

    def test_system_reminder_is_removed_from_prompt(self):
        got = self.prompt_for([user_entry(
            "<system-reminder>noise</system-reminder>\nwhat did I type")])
        self.assertEqual(got, "what did I type")

    def test_reminder_only_entry_is_not_a_prompt(self):
        got = self.prompt_for([
            user_entry("real one"), assistant_entry("a"),
            user_entry([{"type": "text", "text": "<system-reminder>x</system-reminder>"}])])
        self.assertEqual(got, "real one")

    def test_slash_command_keeps_command_and_args(self):
        got = self.prompt_for([user_entry(
            "<command-message>go</command-message><command-name>/go</command-name>"
            "<command-args>now please</command-args>")])
        self.assertEqual(got, "/go now please")

    def test_local_command_output_and_meta_and_sidechain_are_skipped(self):
        got = self.prompt_for([
            user_entry("real"),
            user_entry("<local-command-stdout>out</local-command-stdout>"),
            user_entry("meta text", isMeta=True),
            user_entry("subagent text", isSidechain=True)])
        self.assertEqual(got, "real")

    def test_partial_last_line_is_ignored(self):
        got = self.prompt_for([user_entry("complete prompt")], tail='{"type": "user", "mes')
        self.assertEqual(got, "complete prompt")

    def test_blank_and_non_object_lines_are_ignored(self):
        got = self.prompt_for([user_entry("ok prompt")], tail='\n[1, 2]\n"str"\n')
        self.assertEqual(got, "ok prompt")

    def test_transcript_without_a_prompt_saves_nothing_and_logs(self):  # E3
        repo = self.make_repo()
        transcript = self.write_transcript([assistant_entry("a"), tool_result_entry()])
        code, out, _ = self.run_hook(self.stop_input(repo, long_answer(), transcript))
        self.assertEqual((code, out), (0, ""))
        self.assertEqual(self.notes(repo), [])
        self.assertEqual(len(self.log_lines()), 1)


class SkipTest(HookTestCase):
    def test_short_answer_writes_no_note(self):  # AC3, SC2
        repo = self.make_repo()
        code, out, _ = self.run_hook(self.stop_input(repo, "x" * 50))
        self.assertEqual((code, out), (0, ""))
        self.assertEqual(self.notes(repo), [])
        self.assertFalse(self.home.exists())

    def test_boundary_199_skipped_200_saved(self):  # AC3
        repo = self.make_repo()
        self.run_hook(self.stop_input(repo, "y" * 199))
        self.assertEqual(self.notes(repo), [])
        self.run_hook(self.stop_input(repo, "y" * 200))
        self.assertEqual(len(self.notes(repo)), 1)

    def test_padding_whitespace_does_not_count(self):
        repo = self.make_repo()
        self.run_hook(self.stop_input(repo, "y" * 100 + " " * 200))
        self.assertEqual(self.notes(repo), [])

    def test_stop_hook_active_writes_no_note_and_no_log(self):  # AC4
        repo = self.make_repo()
        code, out, _ = self.run_hook(
            self.stop_input(repo, long_answer(), stop_hook_active=True))
        self.assertEqual((code, out), (0, ""))
        self.assertEqual(self.notes(repo), [])
        self.assertEqual(self.log_lines(), [])

    def test_missing_or_non_string_answer_writes_no_note(self):
        repo = self.make_repo()
        data = json.loads(self.stop_input(repo, long_answer()))
        for value in (None, 123, ["x" * 300]):
            data["last_assistant_message"] = value
            self.assertEqual(self.run_hook(json.dumps(data))[:2], (0, ""))
        del data["last_assistant_message"]
        self.assertEqual(self.run_hook(json.dumps(data))[:2], (0, ""))
        self.assertEqual(self.notes(repo), [])


class CitationTest(HookTestCase):
    def cited(self, files, answer_cites, extra_untracked=None):
        repo = self.make_repo(files)
        for rel, body in (extra_untracked or {}).items():
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_bytes(body)
        self.run_hook(self.stop_input(repo, long_answer(*answer_cites)))
        return self.notes(repo)[0]["files"]

    def test_unique_bare_name_counts(self):  # AC5
        got = self.cited({"src/deep/util.py": "u\n", "other.md": "o"}, ["util.py"])
        self.assertEqual(got, {"src/deep/util.py": sha(b"u\n")})

    def test_ambiguous_bare_name_is_ignored(self):  # AC5
        got = self.cited({"a/util.py": "1", "b/util.py": "2"}, ["util.py"])
        self.assertEqual(got, {})

    def test_partial_path_that_is_unique_counts(self):
        got = self.cited({"a/x/util.py": "1", "b/y/util.py": "2"}, ["x/util.py"])
        self.assertEqual(list(got), ["a/x/util.py"])

    def test_partial_path_does_not_match_inside_a_longer_name(self):
        got = self.cited({"src/myutil.py": "1"}, ["util.py"])
        self.assertEqual(got, {})

    def test_path_that_does_not_exist_is_ignored(self):  # AC5
        got = self.cited({"src/a.py": "x"}, ["src/ghost.py", "docs/missing.md"])
        self.assertEqual(got, {})

    def test_line_suffix_is_stripped(self):
        got = self.cited({"src/a.py": "x"}, ["src/a.py:42", "src/a.py:7"])
        self.assertEqual(list(got), ["src/a.py"])

    def test_leading_dot_slash_and_dotfile_directory(self):
        got = self.cited({"src/a.py": "x", ".github/ci.yml": "on: push\n"},
                         ["./src/a.py", ".github/ci.yml"])
        self.assertEqual(sorted(got), [".github/ci.yml", "src/a.py"])

    def test_json_is_not_cut_to_js(self):
        got = self.cited({"app.js": "j", "conf.json": "{}"}, ["conf.json"])
        self.assertEqual(list(got), ["conf.json"])

    def test_untracked_but_existing_file_counts(self):
        got = self.cited({"src/a.py": "x"}, ["new.py"], {"new.py": b"fresh"})
        self.assertEqual(got, {"new.py": sha(b"fresh")})

    def test_path_traversal_and_symlink_escape_are_ignored(self):
        outside = self.tmp / "secret.md"
        outside.write_text("top secret")
        repo = self.make_repo({"src/a.py": "x"})
        (repo / "link.md").symlink_to(outside)
        self.run_hook(self.stop_input(
            repo, long_answer("src/../../secret.md", "link.md", "../secret.md")))
        self.assertEqual(self.notes(repo)[0]["files"], {})

    def test_file_over_5_mb_is_not_hashed_and_binary_is(self):
        big = b"\0" * (5 * 1024 * 1024 + 1)
        got = self.cited({"big.json": big, "small.json": b"\xff\xfe\x00bin"},
                         ["big.json", "small.json"])
        self.assertEqual(got, {"small.json": sha(b"\xff\xfe\x00bin")})

    def test_directory_named_like_a_file_is_ignored(self):
        got = self.cited({"dir.d/inner.txt": "t"}, ["dir.py"], {"dir.py/x": b"1"})
        self.assertEqual(got, {})

    def test_pathological_long_token_is_fast(self):  # E: huge answer
        repo = self.make_repo()
        answer = "a" * 200_000 + " src/a.py " + "b/" * 50_000
        start = time.monotonic()
        self.run_hook(self.stop_input(repo, answer))
        self.assertLess(time.monotonic() - start, 3)
        self.assertEqual(list(self.notes(repo)[0]["files"]), ["src/a.py"])


class FailureTest(HookTestCase):
    def assert_silent_failure(self, stdin_text, log_count=1):
        code, out, _ = self.run_hook(stdin_text)
        self.assertEqual(code, 0)
        self.assertEqual(out, "")
        self.assertEqual(len(self.log_lines()), log_count)
        log = self.home / "hook.log"
        self.assertEqual(mode(log), 0o600)
        self.assertIn("hook-stop", self.log_lines()[0])

    def test_bad_json_exits_zero_and_logs_one_line(self):  # AC6, SC3
        self.assert_silent_failure("not json")

    def test_empty_stdin_and_non_object_json(self):  # AC6
        self.assert_silent_failure("")
        self.assertEqual(len(self.log_lines()), 1)
        self.run_hook("[1, 2]")
        self.assertEqual(len(self.log_lines()), 2)

    def test_unreadable_transcript_logs_and_saves_nothing(self):  # AC6
        repo = self.make_repo()
        self.assert_silent_failure(self.stop_input(
            repo, long_answer(), transcript=self.tmp / "no-such.jsonl"))
        self.assertEqual(self.notes(repo), [])

    def test_missing_transcript_path_logs(self):  # AC6
        repo = self.make_repo()
        data = json.loads(self.stop_input(repo, long_answer()))
        del data["transcript_path"]
        self.assert_silent_failure(json.dumps(data))

    def test_transcript_that_is_a_folder_logs(self):  # AC6
        repo = self.make_repo()
        self.assert_silent_failure(self.stop_input(
            repo, long_answer(), transcript=self.tmp))

    def test_unwritable_store_logs_and_exits_zero(self):  # AC6
        repo = self.make_repo()
        notes_dir = self.home / easy_memory.repo_key(repo) / "notes"
        notes_dir.parent.mkdir(parents=True)
        notes_dir.write_text("a file where the notes folder should be")
        self.assert_silent_failure(self.stop_input(repo, long_answer()))
        self.assertTrue(notes_dir.is_file())

    @unittest.skipIf(os.geteuid() == 0, "root ignores directory permissions")
    def test_read_only_store_home_logs_nothing_and_exits_zero(self):  # AC6
        repo = self.make_repo()
        self.home.mkdir(mode=0o700)
        self.home.chmod(0o500)
        self.addCleanup(self.home.chmod, 0o700)
        code, out, _ = self.run_hook(self.stop_input(repo, long_answer()))
        self.assertEqual((code, out), (0, ""))
        self.assertEqual(self.notes(repo), [])

    def test_store_home_that_is_a_file_exits_zero(self):  # AC6
        blocker = self.tmp / "blocker"
        blocker.write_text("file")
        repo = self.make_repo()
        with mock.patch.dict(os.environ, {"EASY_MEMORY_HOME": str(blocker / "store")}):
            code, out, _ = self.run_hook(self.stop_input(repo, long_answer()))
        self.assertEqual((code, out), (0, ""))

    def test_log_appends_and_stays_0600_under_permissive_umask(self):
        old = os.umask(0)
        try:
            self.run_hook("bad")
            self.run_hook("bad again")
        finally:
            os.umask(old)
        self.assertEqual(len(self.log_lines()), 2)
        self.assertEqual(mode(self.home / "hook.log"), 0o600)
        self.assertEqual(mode(self.home), 0o700)

    def test_log_line_is_one_line_even_when_the_error_spans_lines(self):
        with mock.patch.object(easy_memory, "save_stop_note",
                               side_effect=RuntimeError("line one\nline two")):
            self.run_hook("{}")
        lines = self.log_lines()
        self.assertEqual(len(lines), 1)
        self.assertIn("line one line two", lines[0])

    def test_unexpected_exception_in_handler_exits_zero(self):
        with mock.patch.object(easy_memory, "write_note", side_effect=KeyError("boom")):
            repo = self.make_repo()
            code, out, _ = self.run_hook(self.stop_input(repo, long_answer()))
        self.assertEqual((code, out), (0, ""))
        self.assertEqual(len(self.log_lines()), 1)

    def test_bad_command_line_exits_zero_with_empty_stdout(self):  # AC8
        out, err = io.StringIO(), io.StringIO()
        with mock.patch.object(sys, "stdin", io.StringIO("{}")), \
                redirect_stdout(out), redirect_stderr(err):
            code = easy_memory.main(["hook-stop", "--bogus"])
        self.assertEqual((code, out.getvalue()), (0, ""))
        self.assertEqual(len(self.log_lines()), 1)

    def test_other_subcommand_bad_arguments_still_exit_nonzero(self):
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as ctx:
            easy_memory.main(["report", "--bogus"])
        self.assertEqual(ctx.exception.code, 2)


class ScriptTest(HookTestCase):
    def run_script(self, stdin_text, *args):
        return subprocess.run([sys.executable, SCRIPT, "hook-stop", *args],
                              input=stdin_text, capture_output=True, text=True,
                              env={**os.environ, "EASY_MEMORY_HOME": str(self.home)})

    def test_stdout_and_stderr_empty_on_success(self):  # AC8
        repo = self.make_repo()
        res = self.run_script(self.stop_input(repo, long_answer("src/a.py")))
        self.assertEqual((res.returncode, res.stdout, res.stderr), (0, "", ""))
        self.assertEqual(len(self.notes(repo)), 1)

    def test_stdout_empty_on_every_failure_path(self):  # AC8
        repo = self.make_repo()
        cases = ["not json", "", "[]", self.stop_input(repo, "short"),
                 self.stop_input(repo, long_answer(), stop_hook_active=True),
                 self.stop_input(repo, long_answer(), transcript=self.tmp / "x")]
        for stdin_text in cases:
            res = self.run_script(stdin_text)
            self.assertEqual((res.returncode, res.stdout), (0, ""), stdin_text[:40])
        self.assertEqual(self.run_script("{}", "--bogus").returncode, 0)
        self.assertEqual(self.run_script("{}", "--bogus").stdout, "")

    def test_closed_stdin_exits_zero(self):
        res = subprocess.run([sys.executable, SCRIPT, "hook-stop"], stdin=subprocess.DEVNULL,
                             capture_output=True, text=True,
                             env={**os.environ, "EASY_MEMORY_HOME": str(self.home)})
        self.assertEqual((res.returncode, res.stdout), (0, ""))


class LatencyTest(unittest.TestCase):
    """AC7 / NFR-001: Stop hook <= 2 s at p95 over 20 runs on a 7,000-file repo."""
    FILES = 7000
    RUNS = 20

    @classmethod
    def setUpClass(cls):
        cls.tmp = Path(tempfile.mkdtemp(prefix="t002-lat-")).resolve()
        cls.repo = cls.tmp / "big"
        for i in range(cls.FILES):
            folder = cls.repo / f"pkg{i % 70}" / f"mod{i % 10}"
            folder.mkdir(parents=True, exist_ok=True)
            (folder / f"file{i}.py").write_text(f"VALUE = {i}\n" * 20)
        run_git(cls.repo, "init", "-q")
        run_git(cls.repo, "add", ".")
        run_git(cls.repo, "commit", "-q", "-m", "big")
        # A transcript with 2,000 lines, the real prompt before a long tool loop.
        entries = [user_entry("how does file42 work?")]
        for _ in range(1000):
            entries += [assistant_entry("thinking " * 30), tool_result_entry()]
        cls.transcript = cls.tmp / "t.jsonl"
        cls.transcript.write_text("".join(json.dumps(e) + "\n" for e in entries))

    @classmethod
    def tearDownClass(cls):
        subprocess.run(["rm", "-rf", str(cls.tmp)])

    def test_p95_within_two_seconds(self):
        # Worst case: one direct path, three bare names that need `git ls-files`.
        answer = long_answer("pkg1/mod1/file1.py:3", "file42.py", "file4242.py",
                             "file6999.py", "missing_name.py")
        stdin_text = json.dumps({
            "session_id": "s", "cwd": str(self.repo), "stop_hook_active": False,
            "transcript_path": str(self.transcript), "last_assistant_message": answer})
        env = {**os.environ, "EASY_MEMORY_HOME": str(self.tmp / "store")}
        durations = []
        for _ in range(self.RUNS):
            start = time.perf_counter()
            res = subprocess.run([sys.executable, SCRIPT, "hook-stop"], input=stdin_text,
                                 capture_output=True, text=True, env=env)
            durations.append(time.perf_counter() - start)
            self.assertEqual((res.returncode, res.stdout), (0, ""))
        durations.sort()
        p95 = durations[math.ceil(0.95 * self.RUNS) - 1]  # nearest rank: 19th of 20
        print(f"\n[NFR-001] {self.FILES} files, {self.RUNS} runs: "
              f"min={durations[0]:.3f}s p50={durations[10]:.3f}s "
              f"p95={p95:.3f}s max={durations[-1]:.3f}s")
        (key_dir,) = (self.tmp / "store").iterdir()
        self.assertEqual(len(list((key_dir / "notes").iterdir())), self.RUNS)
        self.assertLessEqual(p95, 2.0)


if __name__ == "__main__":
    unittest.main()
