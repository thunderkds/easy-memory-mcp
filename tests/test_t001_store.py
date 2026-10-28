"""HUN-74 (T001): repo key and note store. Standard library only.

Every test uses temp folders and EASY_MEMORY_HOME; nothing touches the real home.
"""
import hashlib
import io
import json
import os
import stat
import subprocess
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import easy_memory  # noqa: E402

GIT = ["git", "-c", "user.name=t", "-c", "user.email=t@example.com",
       "-c", "commit.gpgsign=false"]


def run_git(cwd, *args):
    subprocess.run([*GIT, *args], cwd=cwd, check=True, capture_output=True)


def tree_digest(root):
    """Hash of every path, mode and content under root (symlinks not followed)."""
    h = hashlib.sha256()
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames.sort()
        for name in sorted(filenames + dirnames):
            p = os.path.join(dirpath, name)
            st = os.lstat(p)
            h.update(f"{os.path.relpath(p, root)}|{st.st_mode}\n".encode())
            if stat.S_ISREG(st.st_mode):
                h.update(Path(p).read_bytes())
    return h.hexdigest()


def mode(path):
    return stat.S_IMODE(os.stat(path).st_mode)


class StoreTestCase(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix="t001-")).resolve()
        self.addCleanup(lambda: subprocess.run(["rm", "-rf", str(self.tmp)]))
        self.home = self.tmp / "store-home"
        patcher = mock.patch.dict(os.environ, {"EASY_MEMORY_HOME": str(self.home)})
        patcher.start()
        self.addCleanup(patcher.stop)

    def make_repo(self, name="repo"):
        repo = self.tmp / name
        repo.mkdir()
        run_git(repo, "init", "-q")
        (repo / "a.txt").write_text("hello\n")
        run_git(repo, "add", "a.txt")
        run_git(repo, "commit", "-q", "-m", "init")
        return repo


class RepoKeyTest(StoreTestCase):
    def test_worktree_shares_key_with_main_checkout(self):  # AC1
        repo = self.make_repo()
        wt = self.tmp / "wt"
        run_git(repo, "worktree", "add", "-q", "-b", "feat", str(wt))
        self.assertEqual(easy_memory.repo_key(repo), easy_memory.repo_key(wt))

    def test_subfolder_of_repo_shares_key(self):
        repo = self.make_repo()
        (repo / "sub").mkdir()
        self.assertEqual(easy_memory.repo_key(repo), easy_memory.repo_key(repo / "sub"))

    def test_different_repos_have_different_keys(self):
        self.assertNotEqual(easy_memory.repo_key(self.make_repo("one")),
                            easy_memory.repo_key(self.make_repo("two")))

    def test_symlinked_repo_path_gives_same_key(self):  # edge: symlink
        repo = self.make_repo()
        link = self.tmp / "link"
        link.symlink_to(repo)
        self.assertEqual(easy_memory.repo_key(repo), easy_memory.repo_key(link))

    def test_non_git_folder_uses_real_path_and_does_not_raise(self):  # AC2, E7
        plain = self.tmp / "plain"
        plain.mkdir()
        link = self.tmp / "plain-link"
        link.symlink_to(plain)
        key = easy_memory.repo_key(plain)
        self.assertTrue(key)
        self.assertEqual(key, easy_memory.repo_key(link))
        self.assertNotEqual(key, easy_memory.repo_key(self.make_repo()))

    def test_missing_folder_does_not_raise(self):
        self.assertTrue(easy_memory.repo_key(self.tmp / "does-not-exist"))

    def test_git_missing_falls_back_without_raising(self):  # edge: git missing
        repo = self.make_repo()
        empty_bin = self.tmp / "empty-bin"
        empty_bin.mkdir()
        with mock.patch.dict(os.environ, {"PATH": str(empty_bin)}):
            key = easy_memory.repo_key(repo)
        self.assertTrue(key)

    def test_key_is_a_safe_folder_name(self):
        key = easy_memory.repo_key(self.make_repo())
        self.assertRegex(key, r"^[0-9a-f]{16}$")


class WriteNoteTest(StoreTestCase):
    def test_creates_note_file_with_private_modes_and_version(self):  # AC3
        repo = self.make_repo()
        path = Path(easy_memory.write_note(repo, {"prompt": "p", "answer": "a"}))
        key = easy_memory.repo_key(repo)
        self.assertEqual(path.parent, self.home / key / "notes")
        self.assertEqual(path.suffix, ".json")
        self.assertEqual(mode(path), 0o600)
        for folder in (self.home, self.home / key, self.home / key / "notes"):
            self.assertEqual(mode(folder), 0o700, folder)
        data = json.loads(path.read_text())
        self.assertEqual(data["v"], 1)
        self.assertEqual(data["prompt"], "p")
        self.assertEqual(data["id"], path.stem)

    def test_caller_cannot_override_version(self):
        path = Path(easy_memory.write_note(self.make_repo(), {"v": 99}))
        self.assertEqual(json.loads(path.read_text())["v"], 1)

    def test_meta_file_holds_readable_path_and_is_private(self):
        repo = self.make_repo()
        easy_memory.write_note(repo, {"x": 1})
        meta = self.home / easy_memory.repo_key(repo) / "meta.json"
        self.assertEqual(mode(meta), 0o600)
        data = json.loads(meta.read_text())
        self.assertEqual(data["v"], 1)
        self.assertEqual(data["path"], str(repo / ".git"))

    def test_modes_hold_under_permissive_umask(self):  # edge: umask
        old = os.umask(0)
        try:
            path = Path(easy_memory.write_note(self.make_repo(), {"x": 1}))
        finally:
            os.umask(old)
        self.assertEqual(mode(path), 0o600)
        self.assertEqual(mode(path.parent), 0o700)
        self.assertEqual(mode(path.parent.parent), 0o700)
        self.assertEqual(mode(self.home), 0o700)
        self.assertEqual(mode(path.parent.parent / "meta.json"), 0o600)

    def test_no_temp_file_left_and_same_second_ids_differ(self):  # AC4
        repo = self.make_repo()
        fixed = 1_700_000_000.0
        with mock.patch.object(easy_memory.time, "time", return_value=fixed):
            paths = [Path(easy_memory.write_note(repo, {"n": i})) for i in range(20)]
        self.assertEqual(len({p.name for p in paths}), 20)
        left = sorted(p.name for p in paths[0].parent.iterdir())
        self.assertEqual(left, sorted(p.name for p in paths))
        self.assertTrue(all(n.endswith(".json") for n in left))

    def test_temp_file_removed_when_write_fails(self):  # AC4
        repo = self.make_repo()
        easy_memory.write_note(repo, {"n": 0})
        notes = self.home / easy_memory.repo_key(repo) / "notes"
        before = sorted(os.listdir(notes))
        with mock.patch.object(easy_memory.os, "replace", side_effect=OSError("boom")):
            with self.assertRaises(OSError):
                easy_memory.write_note(repo, {"n": 1})
        self.assertEqual(sorted(os.listdir(notes)), before)

    def test_concurrent_writers_get_unique_ids(self):  # edge: two processes
        repo = self.make_repo()
        with ThreadPoolExecutor(max_workers=8) as pool:
            paths = list(pool.map(lambda i: easy_memory.write_note(repo, {"n": i}),
                                  range(60)))
        self.assertEqual(len(set(paths)), 60)
        self.assertEqual(len(easy_memory.read_notes(repo)), 60)

    def test_unwritable_home_raises_clear_error(self):  # edge: home not writable
        blocker = self.tmp / "blocker"
        blocker.write_text("i am a file")
        with mock.patch.dict(os.environ, {"EASY_MEMORY_HOME": str(blocker / "store")}):
            with self.assertRaises(easy_memory.StoreError) as ctx:
                easy_memory.write_note(self.make_repo(), {"x": 1})
        self.assertIsInstance(ctx.exception, OSError)
        self.assertIn(str(blocker), str(ctx.exception))

    @unittest.skipIf(os.geteuid() == 0, "root ignores directory permissions")
    def test_read_only_home_raises_clear_error(self):
        self.home.mkdir(mode=0o700)
        self.home.chmod(0o500)
        self.addCleanup(self.home.chmod, 0o700)
        with self.assertRaises(easy_memory.StoreError):
            easy_memory.write_note(self.make_repo(), {"x": 1})

    def test_repo_folder_is_byte_identical_after_write_and_read(self):  # AC6
        repo = self.make_repo()
        before = tree_digest(repo)
        easy_memory.write_note(repo, {"prompt": "p"})
        easy_memory.read_notes(repo)
        self.assertEqual(tree_digest(repo), before)
        self.assertFalse(str(self.home).startswith(str(repo)))

    def test_non_git_folder_is_byte_identical_after_write_and_read(self):  # AC6, E7
        plain = self.tmp / "plain"
        plain.mkdir()
        (plain / "f.txt").write_text("x")
        before = tree_digest(plain)
        easy_memory.write_note(plain, {"prompt": "p"})
        easy_memory.read_notes(plain)
        self.assertEqual(tree_digest(plain), before)


class ReadNotesTest(StoreTestCase):
    def notes_dir(self, repo):
        easy_memory.write_note(repo, {"seed": True})
        return self.home / easy_memory.repo_key(repo) / "notes"

    def test_round_trip_in_id_order(self):
        repo = self.make_repo()
        with mock.patch.object(easy_memory.time, "time", side_effect=[1.0, 2.0, 3.0]):
            for i in range(3):
                easy_memory.write_note(repo, {"n": i})
        self.assertEqual([n["n"] for n in easy_memory.read_notes(repo)], [0, 1, 2])

    def test_empty_when_store_missing_and_creates_nothing(self):
        self.assertEqual(easy_memory.read_notes(self.make_repo()), [])
        self.assertFalse(self.home.exists())

    def test_skips_newer_version_and_corrupt_json(self):  # AC5
        repo = self.make_repo()
        notes = self.notes_dir(repo)
        (notes / "z-future.json").write_text(json.dumps({"v": 99, "id": "z-future"}))
        (notes / "z-broken.json").write_text("{broken")
        got = easy_memory.read_notes(repo)
        self.assertEqual([n["seed"] for n in got], [True])

    def test_skips_other_bad_shapes_and_non_json_files(self):  # AC5
        repo = self.make_repo()
        notes = self.notes_dir(repo)
        (notes / "list.json").write_text("[1, 2]")
        (notes / "nov.json").write_text(json.dumps({"id": "nov"}))
        (notes / "strv.json").write_text(json.dumps({"v": "1"}))
        (notes / "boolv.json").write_text(json.dumps({"v": True}))
        (notes / "zero.json").write_text(json.dumps({"v": 0}))
        (notes / "binary.json").write_bytes(b"\xff\xfe\x00")
        (notes / "empty.json").write_text("")
        (notes / "x.tmp").write_text(json.dumps({"v": 1, "tmp": True}))
        (notes / "subdir.json").mkdir()
        got = easy_memory.read_notes(repo)
        self.assertEqual([n.get("seed") for n in got], [True])

    def test_worktree_reads_notes_written_from_main(self):  # AC1 end to end
        repo = self.make_repo()
        wt = self.tmp / "wt"
        run_git(repo, "worktree", "add", "-q", "-b", "feat", str(wt))
        easy_memory.write_note(repo, {"from": "main"})
        self.assertEqual([n["from"] for n in easy_memory.read_notes(wt)], ["main"])


class StoreHomeTest(StoreTestCase):
    def test_env_var_overrides_store_root(self):  # AC7
        self.assertEqual(easy_memory.store_home(), self.home)

    def test_default_is_dot_easy_memory_in_home(self):  # AC7
        env = {k: v for k, v in os.environ.items() if k != "EASY_MEMORY_HOME"}
        with mock.patch.dict(os.environ, env, clear=True):
            with mock.patch.object(easy_memory.Path, "home", return_value=self.tmp):
                self.assertEqual(easy_memory.store_home(), self.tmp / ".easy-memory")

    def test_empty_env_var_uses_default(self):
        with mock.patch.dict(os.environ, {"EASY_MEMORY_HOME": ""}):
            with mock.patch.object(easy_memory.Path, "home", return_value=self.tmp):
                self.assertEqual(easy_memory.store_home(), self.tmp / ".easy-memory")


class SubcommandTableTest(unittest.TestCase):
    NAMES = ["hook-stop", "hook-prompt", "serve", "report", "install", "uninstall"]

    def test_table_has_all_subcommands(self):
        self.assertEqual(sorted(easy_memory.SUBCOMMANDS), sorted(self.NAMES))

    def test_each_stub_says_not_implemented_and_exits_zero(self):
        for name in self.NAMES:
            out, err = io.StringIO(), io.StringIO()
            with redirect_stdout(out), redirect_stderr(err):
                code = easy_memory.main([name])
            self.assertEqual(code, 0, name)
            self.assertIn("not implemented", out.getvalue() + err.getvalue())

    def test_stub_writes_nothing_to_stdout(self):  # E12: hook stdout is the prompt
        out = io.StringIO()
        with redirect_stdout(out), redirect_stderr(io.StringIO()):
            easy_memory.main(["hook-prompt"])
        self.assertEqual(out.getvalue(), "")

    def test_runs_as_a_script(self):
        res = subprocess.run([sys.executable, str(ROOT / "easy_memory.py"), "report"],
                             capture_output=True, text=True)
        self.assertEqual(res.returncode, 0)
        self.assertIn("not implemented", res.stdout + res.stderr)


if __name__ == "__main__":
    unittest.main()
