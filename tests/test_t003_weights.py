"""HUN-76 (T003): compact word weights, background build, score. Standard library only.

Every test uses temp folders and EASY_MEMORY_HOME; nothing touches the real
home or the real ~/.easy-memory. Real background builds are only started on tiny
synthetic repos, and the tests wait for every one of them before they end.
"""
import contextlib
import io
import json
import math
import os
import stat
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from collections import Counter
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True  # experiments/ is read-only evidence: no __pycache__ there
sys.path.insert(0, str(ROOT / "experiments" / "02-auto-memory"))

import easy_memory  # noqa: E402
import memstore  # noqa: E402

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com",
       "-c", "commit.gpgsign=false"]
SCRIPT = str(ROOT / "easy_memory.py")
REAL_POPEN = subprocess.Popen


def run_git(cwd, *args):
    subprocess.run([*GIT, *args], cwd=cwd, check=True, capture_output=True)


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def mode(path):
    return stat.S_IMODE(os.stat(path).st_mode)


def make_repo(tmp, git=True):
    """A small repo: 'shared' is in 3 files, 'pairword' in 2, 'zebraonly' in one, plus skipped folders."""
    repo = Path(tmp) / "repo"
    write(repo / "a.py", "def shared_loader(): return zebraonly_value, pairword\n")
    write(repo / "src" / "b.ts", "export const sharedLoader = 1; // shared loader pairword\n")
    write(repo / "docs" / "c.md", "The shared loader reads config.\n")
    write(repo / "node_modules" / "d.js", "const shared_loader = nodemodulesword;\n")
    write(repo / "build" / "e.py", "buildfolderword = 1\n")
    write(repo / "notes.txt", "wrong extension txtword shared\n")
    write(repo / "big.py", "bigfileword = 1\n" + "x = 1\n" * 60000)  # > 300 KB
    if git:
        run_git(repo, "init", "-q")
        run_git(repo, "add", "a.py", "src", "docs")
        run_git(repo, "commit", "-q", "-m", "init")
    return repo


class BuildSpy:
    """Stands in for subprocess.Popen. Only build-weights launches are counted (and faked, or
    really started if real=True); git calls made by subprocess.run pass through untouched."""

    def __init__(self, children, real=False, error=None):
        self.children, self.real, self.error = children, real, error
        self.calls = []

    def __call__(self, argv, *args, **kwargs):
        if "build-weights" not in argv:
            return REAL_POPEN(argv, *args, **kwargs)
        self.calls.append((list(argv), kwargs))
        if self.error:
            raise self.error
        if self.real:
            child = REAL_POPEN(argv, *args, **kwargs)
            self.children.append(child)
            return child
        return mock.MagicMock()

    @property
    def call_count(self):
        return len(self.calls)

    @property
    def call_args(self):
        return (self.calls[-1][0],), self.calls[-1][1]

    def assert_called_once(self):
        assert self.call_count == 1, f"expected 1 build launch, got {self.call_count}"

    def assert_not_called(self):
        assert self.call_count == 0, f"expected no build launch, got {self.call_count}"


class WeightsTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.home = Path(self.tmp.name) / "home"
        patcher = mock.patch.dict(os.environ, {"EASY_MEMORY_HOME": str(self.home)})
        patcher.start()
        self.addCleanup(patcher.stop)
        self.children = []
        self.addCleanup(self.reap_children)

    def reap_children(self):
        for child in self.children:
            try:
                child.wait(timeout=60)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()

    @contextlib.contextmanager
    def spy(self, real=False, error=None):
        """Patch subprocess.Popen with a BuildSpy inside the with block."""
        spy = BuildSpy(self.children, real=real, error=error)
        with mock.patch.object(easy_memory.subprocess, "Popen", spy):
            yield spy

    def store_of(self, repo):
        return self.home / easy_memory.repo_key(repo)

    def weights_file(self, repo):
        return self.store_of(repo) / "weights.json"

    def wait_for(self, predicate, seconds=60):
        deadline = time.time() + seconds
        while time.time() < deadline:
            if predicate():
                return True
            time.sleep(0.02)
        return False

    def write_weights(self, repo, built_at, head, df=None, n=3):
        store = self.store_of(repo)
        easy_memory._private_dir(store)
        data = {"v": 1, "n": n, "head": head, "built_at": built_at, "df": df or {"shared": 3}}
        (store / "weights.json").write_text(json.dumps(data))
        return data


class BuildWeightsTest(WeightsTestCase):
    def test_writes_compact_file_from_source_files(self):  # AC1
        repo = make_repo(self.tmp.name)
        easy_memory.build_weights(repo)
        data = json.loads(self.weights_file(repo).read_text())
        self.assertEqual(set(data), {"v", "n", "head", "built_at", "df"})
        self.assertEqual(data["n"], 3)  # a.py, b.ts, c.md; skipped folders, .txt and big.py out
        self.assertEqual(data["df"]["shared"], 3)
        self.assertEqual(data["df"]["loader"], 3)
        for word in ("zebraonly", "pairword", "nodemodulesword", "buildfolderword", "txtword", "bigfileword"):
            self.assertNotIn(word, data["df"])
        self.assertTrue(all(count >= easy_memory.MIN_FILES_PER_WORD
                            for count in data["df"].values()))  # rare words dropped
        head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
        self.assertEqual(data["head"], head)
        self.assertAlmostEqual(data["built_at"], time.time(), delta=60)

    def test_same_counts_as_memstore_build_idf(self):  # AC1, AC7
        repo = make_repo(self.tmp.name)
        out = Path(self.tmp.name) / "idf.json"
        memstore.build_idf(repo, out)
        full = json.loads(out.read_text())
        easy_memory.build_weights(repo)
        data = json.loads(self.weights_file(repo).read_text())
        self.assertEqual(data["n"], full["n"])
        self.assertEqual(data["df"], {w: c for w, c in full["df"].items()
                                      if c >= easy_memory.MIN_FILES_PER_WORD})
        self.assertGreater(len(full["df"]), len(data["df"]))  # words found in one file are gone

    def test_word_in_exactly_one_file_is_dropped_whatever_the_limit(self):  # AC1
        repo = make_repo(self.tmp.name)
        with mock.patch.object(easy_memory, "MIN_FILES_PER_WORD", 2):
            easy_memory.build_weights(repo)
        df = json.loads(self.weights_file(repo).read_text())["df"]
        self.assertEqual(df["pairword"], 2)
        self.assertNotIn("zebraonly", df)

    def test_file_is_private_and_no_temp_left(self):  # AC1
        repo = make_repo(self.tmp.name)
        easy_memory.build_weights(repo)
        self.assertEqual(mode(self.weights_file(repo)), 0o600)
        self.assertEqual(mode(self.store_of(repo)), 0o700)
        self.assertEqual([p.name for p in self.store_of(repo).iterdir()], ["weights.json"])

    def test_repo_is_byte_identical_after_build(self):  # FR-002
        repo = make_repo(self.tmp.name)
        before = sorted((str(p), p.stat().st_mtime_ns) for p in repo.rglob("*")
                        if ".git" not in p.parts)
        easy_memory.build_weights(repo)
        after = sorted((str(p), p.stat().st_mtime_ns) for p in repo.rglob("*")
                       if ".git" not in p.parts)
        self.assertEqual(before, after)

    def test_atomic_write_failure_leaves_no_partial_file(self):  # edge: build killed
        repo = make_repo(self.tmp.name)
        with mock.patch.object(easy_memory.os, "replace", side_effect=OSError("boom")):
            with self.assertRaises(OSError):
                easy_memory.build_weights(repo)
        self.assertFalse(self.weights_file(repo).exists())
        self.assertEqual(list(self.store_of(repo).iterdir()), [])

    def test_repo_without_source_files_gives_valid_empty_file(self):  # edge: no sources
        repo = Path(self.tmp.name) / "empty"
        write(repo / "readme.txt", "nothing\n")
        easy_memory.build_weights(repo)
        data = json.loads(self.weights_file(repo).read_text())
        self.assertEqual((data["n"], data["df"]), (0, {}))
        # a fresh empty file is a ready file: no rebuild loop
        with self.spy() as popen:
            self.assertIsNotNone(easy_memory.ensure_weights(repo))
        popen.assert_not_called()

    def test_non_git_repo_records_null_head(self):  # edge: not git
        repo = make_repo(self.tmp.name, git=False)
        easy_memory.build_weights(repo)
        self.assertIsNone(json.loads(self.weights_file(repo).read_text())["head"])

    def test_repo_with_no_commit_records_null_head(self):
        repo = make_repo(self.tmp.name, git=False)
        run_git(repo, "init", "-q")
        easy_memory.build_weights(repo)
        self.assertIsNone(json.loads(self.weights_file(repo).read_text())["head"])

    def test_subfolder_builds_from_repo_root(self):
        repo = make_repo(self.tmp.name)
        easy_memory.build_weights(repo / "src")
        self.assertEqual(json.loads(self.weights_file(repo).read_text())["n"], 3)

    def test_unreadable_source_file_is_skipped(self):
        repo = make_repo(self.tmp.name, git=False)
        real_open = open

        def flaky_open(path, *a, **kw):
            if str(path).endswith("c.md"):
                raise PermissionError("no")
            return real_open(path, *a, **kw)

        with mock.patch("builtins.open", flaky_open):
            easy_memory.build_weights(repo)
        self.assertEqual(json.loads(self.weights_file(repo).read_text())["n"], 2)


class BuildCommandTest(WeightsTestCase):
    def run_cli(self, *args):
        env = {**os.environ, "EASY_MEMORY_HOME": str(self.home)}
        return subprocess.run([sys.executable, SCRIPT, *args], capture_output=True,
                              text=True, env=env, timeout=60)

    def test_build_weights_subcommand_writes_file_and_prints_nothing(self):  # AC1
        repo = make_repo(self.tmp.name)
        res = self.run_cli("build-weights", "--repo", str(repo))
        self.assertEqual((res.returncode, res.stdout, res.stderr), (0, "", ""))
        self.assertTrue(self.weights_file(repo).exists())

    def test_build_failure_exits_zero_logs_and_prints_nothing_on_stdout(self):  # exit-0 safe
        res = self.run_cli("build-weights", "--repo", str(Path(self.tmp.name) / "missing"))
        self.assertEqual((res.returncode, res.stdout), (0, ""))
        # a missing folder is just an empty repo, so also try an unwritable store
        blocker = Path(self.tmp.name) / "blocker"
        blocker.write_text("file, not folder")
        env = {**os.environ, "EASY_MEMORY_HOME": str(blocker / "sub")}
        repo = make_repo(self.tmp.name)
        res = subprocess.run([sys.executable, SCRIPT, "build-weights", "--repo", str(repo)],
                             capture_output=True, text=True, env=env, timeout=60)
        self.assertEqual((res.returncode, res.stdout), (0, ""))
        self.assertIn("build-weights", res.stderr)

    def test_release_lock_flag_removes_the_lock_after_the_build(self):  # AC5
        repo = make_repo(self.tmp.name)
        store = self.store_of(repo)
        easy_memory._private_dir(store)
        (store / "weights.lock").write_text("")
        self.run_cli("build-weights", "--repo", str(repo), "--release-lock")
        self.assertFalse((store / "weights.lock").exists())
        self.assertTrue(self.weights_file(repo).exists())

    def test_without_release_lock_flag_the_lock_stays(self):
        repo = make_repo(self.tmp.name)
        store = self.store_of(repo)
        easy_memory._private_dir(store)
        (store / "weights.lock").write_text("")
        self.run_cli("build-weights", "--repo", str(repo))
        self.assertTrue((store / "weights.lock").exists())

    def test_lock_released_even_when_build_fails(self):  # AC5
        repo = make_repo(self.tmp.name)
        store = self.store_of(repo)
        easy_memory._private_dir(store)
        (store / "weights.lock").write_text("")
        with mock.patch.object(easy_memory, "build_weights", side_effect=OSError("boom")), \
                contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(easy_memory.main(
                ["build-weights", "--repo", str(repo), "--release-lock"]), 0)
        self.assertFalse((store / "weights.lock").exists())


class EnsureWeightsTest(WeightsTestCase):
    def test_missing_file_returns_not_ready_fast_and_starts_one_build(self):  # AC3, SC1
        repo = make_repo(self.tmp.name)
        with self.spy(real=True):
            started = time.perf_counter()
            result = easy_memory.ensure_weights(repo)
            elapsed = time.perf_counter() - started
        self.assertIsNone(result)
        self.assertLess(elapsed, 0.05)
        self.assertEqual(len(self.children), 1)
        self.assertTrue((self.store_of(repo) / "weights.lock").exists() or
                        self.weights_file(repo).exists())
        # the detached build finishes, writes the file and removes its lock
        self.assertTrue(self.wait_for(lambda: self.weights_file(repo).exists()
                                      and not (self.store_of(repo) / "weights.lock").exists()))
        self.assertIsNotNone(easy_memory.ensure_weights(repo))

    def test_build_is_detached_with_closed_streams(self):  # AC3
        repo = make_repo(self.tmp.name)
        with self.spy() as popen:
            easy_memory.ensure_weights(repo)
        args, kwargs = popen.call_args
        self.assertEqual(args[0][0], sys.executable)
        self.assertEqual(args[0][1:4], [SCRIPT, "build-weights", "--repo"])
        self.assertIn("--release-lock", args[0])
        self.assertTrue(kwargs["start_new_session"])
        for stream in ("stdin", "stdout", "stderr"):
            self.assertEqual(kwargs[stream], subprocess.DEVNULL)

    def test_ensure_writes_nothing_to_stdout(self):  # hook-facing code
        repo = make_repo(self.tmp.name)
        with self.spy():
            with mock.patch("sys.stdout") as out:
                easy_memory.ensure_weights(repo)
        out.write.assert_not_called()

    def test_fresh_file_is_returned_with_no_build(self):  # AC3
        repo = make_repo(self.tmp.name)
        data = self.write_weights(repo, time.time(), "abc")
        with self.spy() as popen:
            self.assertEqual(easy_memory.ensure_weights(repo), data)
        popen.assert_not_called()

    def test_old_file_and_head_changed_rebuilds_but_returns_old(self):  # AC4
        repo = make_repo(self.tmp.name)
        data = self.write_weights(repo, time.time() - 2 * 86400, "0" * 40)
        with self.spy() as popen:
            self.assertEqual(easy_memory.ensure_weights(repo), data)
        popen.assert_called_once()

    def test_old_file_and_same_head_does_not_rebuild(self):  # AC4
        repo = make_repo(self.tmp.name)
        head = subprocess.run(["git", "-C", str(repo), "rev-parse", "HEAD"],
                              capture_output=True, text=True).stdout.strip()
        data = self.write_weights(repo, time.time() - 2 * 86400, head)
        with self.spy() as popen:
            self.assertEqual(easy_memory.ensure_weights(repo), data)
        popen.assert_not_called()

    def test_young_file_and_head_changed_does_not_rebuild(self):  # AC4
        repo = make_repo(self.tmp.name)
        data = self.write_weights(repo, time.time() - 3600, "0" * 40)
        with self.spy() as popen:
            self.assertEqual(easy_memory.ensure_weights(repo), data)
        popen.assert_not_called()

    def test_not_git_old_file_rebuilds_on_age_only(self):  # edge: not git
        repo = make_repo(self.tmp.name, git=False)
        data = self.write_weights(repo, time.time() - 2 * 86400, None)
        with self.spy() as popen:
            self.assertEqual(easy_memory.ensure_weights(repo), data)
        popen.assert_called_once()

    def test_not_git_young_file_does_not_rebuild(self):
        repo = make_repo(self.tmp.name, git=False)
        self.write_weights(repo, time.time() - 60, None)
        with self.spy() as popen:
            self.assertIsNotNone(easy_memory.ensure_weights(repo))
        popen.assert_not_called()

    def test_corrupt_or_newer_file_counts_as_missing(self):
        repo = make_repo(self.tmp.name)
        store = self.store_of(repo)
        easy_memory._private_dir(store)
        for body in ("{not json", "[]", json.dumps({"v": 99, "n": 1, "head": None,
                                                    "built_at": time.time(), "df": {}}),
                     json.dumps({"v": 1, "n": "x", "head": None, "built_at": 1, "df": {}}),
                     json.dumps({"v": 1, "n": 1, "head": None, "built_at": 1, "df": []})):
            (store / "weights.json").write_text(body)
            (store / "weights.lock").unlink(missing_ok=True)
            with self.spy() as popen:
                self.assertIsNone(easy_memory.ensure_weights(repo), body)
            popen.assert_called_once()

    def test_spawn_failure_returns_not_ready_and_frees_lock(self):  # edge
        repo = make_repo(self.tmp.name)
        with self.spy(error=OSError("nope")):
            self.assertIsNone(easy_memory.ensure_weights(repo))
        self.assertFalse((self.store_of(repo) / "weights.lock").exists())
        self.assertIn("ensure-weights", (self.home / "hook.log").read_text())

    def test_unwritable_store_returns_not_ready(self):  # edge: E9
        repo = make_repo(self.tmp.name)
        blocker = Path(self.tmp.name) / "blocker"
        blocker.write_text("file")
        with mock.patch.dict(os.environ, {"EASY_MEMORY_HOME": str(blocker / "sub")}):
            with self.spy() as popen:
                self.assertIsNone(easy_memory.ensure_weights(repo))
        popen.assert_not_called()


class LockTest(WeightsTestCase):
    def test_second_call_with_live_lock_starts_no_build(self):  # AC5
        repo = make_repo(self.tmp.name)
        with self.spy() as popen:
            easy_memory.ensure_weights(repo)
            easy_memory.ensure_weights(repo)
        self.assertEqual(popen.call_count, 1)

    def test_simultaneous_calls_start_one_build(self):  # AC5, SC3
        repo = make_repo(self.tmp.name)
        easy_memory.repo_key(repo)
        threads, barrier = [], threading.Barrier(8)

        def call():
            barrier.wait()
            easy_memory.ensure_weights(repo)

        with self.spy() as popen:
            threads = [threading.Thread(target=call) for _ in range(8)]
            for thread in threads:
                thread.start()
            for thread in threads:
                thread.join()
        self.assertEqual(popen.call_count, 1)

    def test_simultaneous_processes_start_one_build(self):  # AC5, SC3 (real processes)
        repo = make_repo(self.tmp.name)
        code = ("import sys, easy_memory; easy_memory.ensure_weights(sys.argv[1])")
        env = {**os.environ, "EASY_MEMORY_HOME": str(self.home), "PYTHONPATH": str(ROOT)}
        procs = [REAL_POPEN([sys.executable, "-c", code, str(repo)], env=env)
                 for _ in range(4)]
        self.children.extend(procs)
        for proc in procs:
            self.assertEqual(proc.wait(timeout=60), 0)
        self.assertTrue(self.wait_for(lambda: self.weights_file(repo).exists()
                                      and not (self.store_of(repo) / "weights.lock").exists()))
        # one build means one lock cycle; a second build would have rewritten the file
        built_at = json.loads(self.weights_file(repo).read_text())["built_at"]
        time.sleep(0.3)
        self.assertEqual(json.loads(self.weights_file(repo).read_text())["built_at"], built_at)

    def test_stale_lock_is_replaced(self):  # AC5: 10-minute timeout
        repo = make_repo(self.tmp.name)
        store = self.store_of(repo)
        easy_memory._private_dir(store)
        lock = store / "weights.lock"
        lock.write_text("")
        old = time.time() - 601
        os.utime(lock, (old, old))
        with self.spy() as popen:
            easy_memory.ensure_weights(repo)
        popen.assert_called_once()
        self.assertGreater(lock.stat().st_mtime, time.time() - 60)

    def test_lock_just_under_ten_minutes_is_respected(self):  # AC5
        repo = make_repo(self.tmp.name)
        store = self.store_of(repo)
        easy_memory._private_dir(store)
        lock = store / "weights.lock"
        lock.write_text("")
        recent = time.time() - 590
        os.utime(lock, (recent, recent))
        with self.spy() as popen:
            self.assertIsNone(easy_memory.ensure_weights(repo))
        popen.assert_not_called()

    def test_lock_file_is_private(self):
        repo = make_repo(self.tmp.name)
        with self.spy():
            easy_memory.ensure_weights(repo)
        self.assertEqual(mode(self.store_of(repo) / "weights.lock"), 0o600)

    def test_old_file_with_live_lock_still_returns_old_data(self):  # AC4 + AC5
        repo = make_repo(self.tmp.name)
        data = self.write_weights(repo, time.time() - 2 * 86400, "0" * 40)
        lock = self.store_of(repo) / "weights.lock"
        lock.write_text("")
        with self.spy() as popen:
            self.assertEqual(easy_memory.ensure_weights(repo), data)
        popen.assert_not_called()


class ScoreTest(unittest.TestCase):
    WORDS = {"n": 100, "df": {"loader": 50, "shared": 3, "config": 40, "reader": 2}}

    def test_matches_memstore_score_with_full_weights(self):  # AC7
        prompts = ["How does the shared loader read config?",
                   "parseHTTPResponse_header and snake_case_name; the and for",
                   "", "!!", "zebra only unknownword"]
        docs = ["The shared loader reads config. loader loader shared",
                "nothing relevant here", "", "snake case name parse http response header",
                "zebra unknownword zebra"]
        with tempfile.TemporaryDirectory() as tmp:
            idf = Path(tmp) / "idf.json"
            idf.write_text(json.dumps(self.WORDS))
            for prompt in prompts:
                expected = memstore.score(prompt, docs, idf)
                got = [easy_memory.score(prompt, doc, self.WORDS) for doc in docs]
                self.assertEqual(len(got), len(expected))
                for want, have in zip(expected, got):
                    self.assertAlmostEqual(have, want, places=12)

    def test_tokens_match_memstore(self):  # AC7
        text = "parseHTTPResponse snake_case_name X1 ab The and Foo2Bar"
        self.assertEqual(sorted(easy_memory.tokens(text)), sorted(memstore.tokens(text)))

    def test_empty_prompt_or_no_overlap_scores_zero(self):
        self.assertEqual(easy_memory.score("", "text here", self.WORDS), 0.0)
        self.assertEqual(easy_memory.score("loader", "nothing", self.WORDS), 0.0)

    def test_score_is_within_zero_and_one(self):
        value = easy_memory.score("shared loader", "shared loader " * 30, self.WORDS)
        self.assertTrue(0 < value <= 1)

    def test_missing_word_carries_the_rarest_weight(self):
        # a word that is not in the table scores like df = 0 (documented choice)
        n = self.WORDS["n"]
        with_zero = easy_memory.score("zzzword loader", "zzzword", self.WORDS)
        want = math.log(n + 1) + 1
        other = math.log((n + 1) / 51) + 1
        self.assertAlmostEqual(with_zero, want / ((want + other) * 2.2), places=12)


class MainTest(WeightsTestCase):
    def test_build_weights_is_a_registered_subcommand(self):
        self.assertIn("build-weights", easy_memory.SUBCOMMANDS)

    def test_existing_stubs_unchanged(self):
        for name in ("hook-prompt", "serve", "report", "install", "uninstall"):
            self.assertIn(name, easy_memory.SUBCOMMANDS)


if __name__ == "__main__":
    unittest.main()
