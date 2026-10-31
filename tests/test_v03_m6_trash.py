"""HUN-135 (v0.3 M6): memory_forget moves a note to <store>/trash/, memory_restore brings it back.

Every test uses a temp EASY_MEMORY_HOME and HOME (tests.test_t008_mcp.Base). All secrets are
fake and split in the source so a secret scanner does not flag this file.
"""
import contextlib
import io
import json
import os
import stat
import sys
import time
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import easy_memory  # noqa: E402
from tests import test_t008_mcp as t8  # noqa: E402

DAY = 86400
AWS = "AK" + "IA" + "0123456789ABCDEF"
GITHUB = "gh" + "p_" + "0123456789abcdefghijklmnopqrstuvwxyzAB"[:36]


class TrashBase(t8.Base):
    def trash_dir(self, repo=None):
        return self.notes_dir(repo).parent / "trash"

    def forget(self, client, note_id):
        return client.text("memory_forget", {"id": note_id})

    def age(self, path, days):
        """Set the trash file's move time to `days` days ago."""
        then = time.time() - days * DAY
        os.utime(path, (then, then))


class ForgetRestoreTest(TrashBase):
    def test_forget_then_restore_gives_back_the_same_bytes(self):  # AC1
        note_id = self.save("restore me", "restore answer " * 30)
        path = self.notes_dir() / f"{note_id}.json"
        before = path.read_bytes()
        client = self.initialized()
        text, is_error = self.forget(client, note_id)
        self.assertFalse(is_error)
        self.assertFalse(path.exists())
        self.assertEqual((self.trash_dir() / f"{note_id}.json").read_bytes(), before)
        text, is_error = client.text("memory_restore", {"id": note_id})
        self.assertFalse(is_error, text)
        self.assertEqual(path.read_bytes(), before)
        self.assertFalse((self.trash_dir() / f"{note_id}.json").exists())
        text, is_error = client.text("memory_read", {"id": note_id})
        self.assertFalse(is_error)
        self.assertIn("restore answer", text)

    def test_forget_reply_names_restore_and_thirty_days(self):  # requirement
        note_id = self.save("a", "answer " * 40)
        text, is_error = self.forget(self.initialized(), note_id)
        self.assertFalse(is_error)
        self.assertIn(note_id, text)
        self.assertIn("memory_restore", text)
        self.assertIn("30 days", text)

    def test_forget_of_an_unknown_id_is_an_error_and_moves_nothing(self):  # AC2
        keep = self.save("keep", "keep answer " * 30)
        client = self.initialized()
        text, is_error = self.forget(client, "20260101T000000000-deadbeef")
        self.assertTrue(is_error)
        self.assertIn("note not found: 20260101T000000000-deadbeef", text)
        self.assertTrue((self.notes_dir() / f"{keep}.json").exists())
        self.assertEqual(list(self.trash_dir().glob("*")) if self.trash_dir().exists() else [], [])

    def test_forget_twice_the_second_says_not_found(self):
        note_id = self.save("a", "answer " * 40)
        client = self.initialized()
        self.assertFalse(self.forget(client, note_id)[1])
        text, is_error = self.forget(client, note_id)
        self.assertTrue(is_error)
        self.assertIn("note not found", text)
        self.assertTrue((self.trash_dir() / f"{note_id}.json").exists())

    def test_forget_never_overwrites_a_trash_file_with_the_same_id(self):
        note_id = self.save("new", "new answer " * 30)
        trash = self.trash_dir()
        easy_memory._private_dir(trash)
        (trash / f"{note_id}.json").write_text("OLD TRASHED CONTENT", encoding="utf-8")
        text, is_error = self.forget(self.initialized(), note_id)
        self.assertTrue(is_error, text)
        self.assertEqual((trash / f"{note_id}.json").read_text(encoding="utf-8"), "OLD TRASHED CONTENT")
        self.assertTrue((self.notes_dir() / f"{note_id}.json").exists())  # the note stays put

    def test_forgotten_note_is_gone_from_list_search_read_and_the_index(self):  # AC3
        gone = self.save("zebra migration policy", "zebra migration answer " * 20)
        stay = self.save("zebra other topic", "zebra other answer " * 20)
        weights = {"n": 0, "df": {}}
        self.assertIn(gone, "\n".join(easy_memory._index_lines("zebra migration", self.repo, weights)))
        client = self.initialized()
        self.assertFalse(self.forget(client, gone)[1])
        self.assertNotIn(gone, client.text("memory_list")[0])
        self.assertIn(stay, client.text("memory_list")[0])
        self.assertNotIn(gone, client.text("memory_search", {"query": "zebra migration"})[0])
        text, is_error = client.text("memory_read", {"id": gone})
        self.assertTrue(is_error)
        self.assertIn("not found", text)
        self.assertNotIn(gone, "\n".join(easy_memory._index_lines("zebra migration", self.repo, weights)))
        self.assertEqual([n["id"] for n in easy_memory.read_notes(self.repo)], [stay])

    def test_restore_of_an_id_not_in_the_trash_is_an_error(self):  # AC4
        live = self.save("live", "live answer " * 30)
        client = self.initialized()
        for bad in ("20260101T000000000-deadbeef", live):  # unknown; live in notes/, not trash
            text, is_error = client.text("memory_restore", {"id": bad})
            self.assertTrue(is_error, bad)
            self.assertIn(bad, text)
        self.assertTrue((self.notes_dir() / f"{live}.json").exists())

    def test_restore_never_overwrites_a_note_with_the_same_id(self):  # AC4
        note_id = self.save("original", "original answer " * 30)
        client = self.initialized()
        self.assertFalse(self.forget(client, note_id)[1])
        newer = self.notes_dir() / f"{note_id}.json"
        newer.write_text("NEWER NOTE", encoding="utf-8")
        text, is_error = client.text("memory_restore", {"id": note_id})
        self.assertTrue(is_error)
        self.assertIn("already exists", text)
        self.assertEqual(newer.read_text(encoding="utf-8"), "NEWER NOTE")
        self.assertIn("original answer", (self.trash_dir() / f"{note_id}.json").read_text(encoding="utf-8"))

    def test_restore_does_not_follow_a_symlink_in_the_notes_folder(self):
        note_id = self.save("original", "original answer " * 30)
        client = self.initialized()
        self.assertFalse(self.forget(client, note_id)[1])
        target = self.tmp / "elsewhere.json"
        target.write_text("ELSEWHERE", encoding="utf-8")
        (self.notes_dir() / f"{note_id}.json").symlink_to(target)
        _, is_error = client.text("memory_restore", {"id": note_id})
        self.assertTrue(is_error)
        self.assertEqual(target.read_text(encoding="utf-8"), "ELSEWHERE")
        self.assertTrue((self.trash_dir() / f"{note_id}.json").exists())

    def test_restore_recreates_a_missing_notes_folder(self):
        note_id = self.save("a", "answer " * 40)
        client = self.initialized()
        self.assertFalse(self.forget(client, note_id)[1])
        self.notes_dir().rmdir()
        self.assertFalse(client.text("memory_restore", {"id": note_id})[1])
        self.assertTrue((self.notes_dir() / f"{note_id}.json").exists())
        self.assertEqual(stat.S_IMODE(self.notes_dir().stat().st_mode), 0o700)

    def test_bad_ids_are_rejected_by_restore_and_nothing_moves(self):
        note_id = self.save("a", "answer " * 40)
        client = self.initialized()
        self.assertFalse(self.forget(client, note_id)[1])
        outside = self.trash_dir().parent / "secret.json"
        outside.write_text("SECRET", encoding="utf-8")
        for bad in t8.SecurityTest.BAD_IDS + [None, 5, ["a"], True]:
            text, is_error = client.text("memory_restore", {"id": bad})
            self.assertTrue(is_error, bad)
            self.assertNotIn("SECRET", text)
        self.assertTrue(client.text("memory_restore", {})[1])
        self.assertEqual(outside.read_text(encoding="utf-8"), "SECRET")
        self.assertTrue((self.trash_dir() / f"{note_id}.json").exists())
        self.assertEqual(list(self.notes_dir().glob("*")), [])

    def test_a_symlink_in_the_trash_is_not_restored(self):
        target = self.tmp / "outside.json"
        target.write_text("OUTSIDE", encoding="utf-8")
        easy_memory._private_dir(self.trash_dir())
        (self.trash_dir() / "evil.json").symlink_to(target)
        self.save("a", "answer " * 40)  # make the store exist
        text, is_error = self.initialized().text("memory_restore", {"id": "evil"})
        self.assertTrue(is_error)
        self.assertNotIn("OUTSIDE", text)
        self.assertEqual(list(self.notes_dir().glob("evil*")), [])
        self.assertTrue(target.exists())

    def test_a_trash_folder_that_is_a_symlink_is_refused(self):
        note_id = self.save("a", "answer " * 40)
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        self.trash_dir().symlink_to(elsewhere)
        text, is_error = self.forget(self.initialized(), note_id)
        self.assertTrue(is_error, text)
        self.assertEqual(list(elsewhere.iterdir()), [])
        self.assertTrue((self.notes_dir() / f"{note_id}.json").exists())

    def test_restore_refuses_a_trash_folder_that_is_a_symlink(self):
        self.save("a", "answer " * 40)  # make the store exist
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        outside = elsewhere / "x-1.json"
        outside.write_text("OUTSIDE", encoding="utf-8")
        self.trash_dir().symlink_to(elsewhere)
        text, is_error = self.initialized().text("memory_restore", {"id": "x-1"})
        self.assertTrue(is_error, text)
        self.assertIn("trash folder is a symlink", text)
        self.assertTrue(outside.exists())
        self.assertEqual(outside.read_text(encoding="utf-8"), "OUTSIDE")
        self.assertFalse((self.notes_dir() / "x-1.json").exists())

    def test_forget_in_one_repo_leaves_another_repos_trash_alone(self):
        other = self.make_repo("other")
        theirs = self.save("theirs", "their answer " * 30, repo=other)
        mine = self.save("mine", "my answer " * 30)
        client = self.initialized()
        self.assertFalse(self.forget(client, mine)[1])
        self.assertTrue(self.forget(client, theirs)[1])
        self.assertTrue((self.notes_dir(other) / f"{theirs}.json").exists())
        self.assertFalse(self.trash_dir(other).exists())


class ToolListTest(TrashBase):
    def test_memory_restore_is_listed_with_the_schema_of_forget(self):  # AC6
        tools = self.initialized().request("tools/list")["result"]["tools"]
        by_name = {tool["name"]: tool for tool in tools}
        self.assertIn("memory_restore", by_name)
        self.assertTrue(by_name["memory_restore"]["description"])
        self.assertEqual(by_name["memory_restore"]["inputSchema"]["type"], "object")
        self.assertEqual(by_name["memory_restore"]["inputSchema"]["required"], ["id"])
        self.assertEqual(by_name["memory_restore"]["inputSchema"]["properties"]["id"]["type"], "string")
        self.assertEqual(by_name["memory_forget"]["inputSchema"]["required"], ["id"])
        self.assertIn("memory_restore", by_name["memory_forget"]["description"])
        self.assertNotIn("cannot be undone", by_name["memory_forget"]["description"])

    def test_the_other_tools_still_answer(self):  # old clients that never call memory_restore
        note_id = self.save("a", "answer " * 40)
        client = self.initialized()
        self.assertFalse(client.text("memory_list")[1])
        self.assertFalse(client.text("memory_read", {"id": note_id})[1])
        self.assertFalse(client.text("memory_search", {"query": "answer"})[1])


class RetentionTest(TrashBase):
    def trashed(self, client, *days):
        """Forget one note per entry of days, then age each trash file; return their paths."""
        ids = [self.save(f"old {d}", "answer " * 40) for d in days]
        for note_id in ids:
            self.assertFalse(self.forget(client, note_id)[1])
        paths = [self.trash_dir() / f"{note_id}.json" for note_id in ids]
        for path, d in zip(paths, days):
            self.age(path, d)
        return paths if len(paths) > 1 else paths[0]

    def test_forget_sets_the_move_time_not_the_save_time(self):  # edge: rename keeps mtime
        note_id = self.save("a", "answer " * 40)
        path = self.notes_dir() / f"{note_id}.json"
        self.age(path, 90)  # saved 90 days ago
        self.assertFalse(self.forget(self.initialized(), note_id)[1])
        moved = self.trash_dir() / f"{note_id}.json"
        self.assertLess(time.time() - moved.stat().st_mtime, 60)
        self.assertTrue(moved.exists())  # an old note is not purged by its own forget

    def test_a_failed_utime_skips_the_purge_so_the_note_is_kept(self):  # Stage 4 fix
        # If the move time cannot be set, the note keeps its save time; a purge right after
        # would delete a note saved over 30 days ago at once. Forget must then skip the purge.
        note_id = self.save("a", "answer " * 40)
        self.age(self.notes_dir() / f"{note_id}.json", 90)
        with mock.patch.object(easy_memory.os, "utime", side_effect=PermissionError("denied")):
            text = easy_memory._tool_forget(self.repo, {"id": note_id})
        self.assertIn("memory_restore", text)
        self.assertTrue((self.trash_dir() / f"{note_id}.json").exists())
        self.assertIn("PermissionError", (self.home / "hook.log").read_text(encoding="utf-8"))

    def test_trash_older_than_30_days_is_deleted_at_the_next_forget(self):  # AC5
        client = self.initialized()
        old, recent = self.trashed(client, 31, 29)
        self.assertTrue(old.exists() and recent.exists())  # no purge until a forget
        trigger = self.save("trigger", "trigger answer " * 30)
        self.assertFalse(self.forget(client, trigger)[1])
        self.assertFalse(old.exists())
        self.assertTrue(recent.exists())
        self.assertTrue((self.trash_dir() / f"{trigger}.json").exists())

    def test_a_failed_forget_does_not_purge(self):
        client = self.initialized()
        old = self.trashed(client, 40)
        self.assertTrue(self.forget(client, "20260101T000000000-deadbeef")[1])
        self.assertTrue(old.exists())

    def test_purge_leaves_other_files_and_folders_in_trash_alone(self):
        client = self.initialized()
        self.trashed(client, 1)
        stray = self.trash_dir() / "notes.txt"
        stray.write_text("keep", encoding="utf-8")
        sub = self.trash_dir() / "sub.json"
        sub.mkdir()
        outside = self.tmp / "outside.json"
        outside.write_text("keep", encoding="utf-8")
        link = self.trash_dir() / "link.json"
        link.symlink_to(outside)
        for item in (stray, sub):
            self.age(item, 100)
        os.utime(link, (0, 0), follow_symlinks=False)
        trigger = self.save("trigger", "trigger answer " * 30)
        self.assertFalse(self.forget(client, trigger)[1])
        self.assertTrue(stray.exists() and sub.is_dir() and outside.exists())
        self.assertEqual(stray.read_text(encoding="utf-8"), "keep")

    def test_a_purge_error_is_logged_and_forget_still_succeeds(self):  # edge: purge errors
        note_id = self.save("a", "answer " * 40)
        trash = self.trash_dir()
        easy_memory._private_dir(trash)
        stuck = trash / "stuck.json"
        stuck.write_text("{}", encoding="utf-8")
        self.age(stuck, 45)
        real_unlink = os.unlink

        def unlink(path, *args, **kwargs):
            if os.path.basename(path) == "stuck.json":
                raise PermissionError("denied")
            return real_unlink(path, *args, **kwargs)

        with mock.patch.object(easy_memory.os, "unlink", side_effect=unlink):
            text = easy_memory._tool_forget(self.repo, {"id": note_id})
        self.assertIn("memory_restore", text)
        self.assertTrue(stuck.exists())
        self.assertTrue((trash / f"{note_id}.json").exists())
        self.assertIn("PermissionError", (self.home / "hook.log").read_text(encoding="utf-8"))


class ModeTest(TrashBase):
    def test_trash_is_0700_and_a_trashed_file_0600(self):  # AC8
        note_id = self.save("a", "answer " * 40)
        old_umask = os.umask(0)
        try:
            self.assertFalse(self.forget(self.initialized(), note_id)[1])
        finally:
            os.umask(old_umask)
        self.assertEqual(stat.S_IMODE(self.trash_dir().stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE((self.trash_dir() / f"{note_id}.json").stat().st_mode), 0o600)

    def test_uninstall_purge_removes_the_trash(self):  # AC8
        note_id = self.save("a", "answer " * 40)
        self.assertFalse(self.forget(self.initialized(), note_id)[1])
        trashed = self.trash_dir() / f"{note_id}.json"
        self.assertTrue(trashed.exists())
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = easy_memory.main(["uninstall", "--purge"])
        self.assertEqual(code, 0, err.getvalue())
        self.assertFalse(self.home.exists())
        self.assertFalse(trashed.exists())


class RedactTrashTest(TrashBase):
    def run_redact(self, *flags):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = easy_memory.main(["redact", "--repo", str(self.repo), *flags])
        return code, out.getvalue() + err.getvalue()

    def trashed_secret(self, days=10):
        note_id = self.save(f"deploy with {AWS}", f"log had {GITHUB}")
        self.assertFalse(self.forget(self.initialized(), note_id)[1])
        path = self.trash_dir() / f"{note_id}.json"
        self.age(path, days)
        return note_id, path

    def test_dry_run_lists_a_trash_hit_with_a_trash_label_and_writes_nothing(self):  # AC7
        note_id, path = self.trashed_secret()
        before = (path.read_bytes(), path.stat().st_mtime_ns)
        code, out = self.run_redact()
        self.assertEqual(code, 0)
        self.assertIn(f"trash/{note_id}: ", out)
        self.assertIn("aws_access_key 1", out)
        self.assertNotIn(AWS, out)
        self.assertEqual((path.read_bytes(), path.stat().st_mtime_ns), before)

    def test_apply_rewrites_the_trashed_note_and_keeps_its_move_time(self):  # AC7
        note_id, path = self.trashed_secret(days=10)
        moved_at = path.stat().st_mtime_ns
        code, out = self.run_redact("--apply")
        self.assertEqual(code, 0, out)
        self.assertIn(f"trash/{note_id}: ", out)
        text = path.read_text(encoding="utf-8")
        self.assertNotIn(AWS, text)
        self.assertNotIn(GITHUB, text)
        self.assertIn("[REDACTED:aws_access_key]", text)
        self.assertEqual(path.stat().st_mtime_ns, moved_at)  # redact must not restart the 30 days
        self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        code, out = self.run_redact()
        self.assertEqual(code, 0)
        self.assertIn("No secrets found", out)

    def test_apply_covers_notes_and_trash_together(self):  # AC7
        live = self.save(f"live {AWS}", "live answer")
        note_id, path = self.trashed_secret()
        code, out = self.run_redact("--apply")
        self.assertEqual(code, 0)
        self.assertIn("Rewrote 2 note(s).", out)
        self.assertIn(f"\n{live}: ", "\n" + out)  # a live hit keeps its plain label
        self.assertNotIn(AWS, (self.notes_dir() / f"{live}.json").read_text(encoding="utf-8"))
        self.assertNotIn(AWS, path.read_text(encoding="utf-8"))

    def test_a_store_with_only_a_trash_is_still_scanned(self):  # AC7
        note_id, path = self.trashed_secret()
        self.notes_dir().rmdir()
        code, out = self.run_redact("--apply")
        self.assertEqual(code, 0, out)
        self.assertNotIn(AWS, path.read_text(encoding="utf-8"))

    def test_clean_notes_and_trash_are_counted_together(self):
        self.save("clean", "clean answer")
        gone = self.save("clean too", "clean answer too")
        self.assertFalse(self.forget(self.initialized(), gone)[1])
        code, out = self.run_redact()
        self.assertEqual(code, 0)
        self.assertIn("No secrets found in 2 note(s).", out)

    def test_a_corrupt_or_symlinked_trash_file_is_skipped_and_named_as_trash(self):
        note_id = self.save("a", "answer " * 40)
        self.assertFalse(self.forget(self.initialized(), note_id)[1])
        (self.trash_dir() / "broken.json").write_text("{not json", encoding="utf-8")
        outside = self.tmp / "outside.json"
        outside.write_text(json_note(f"x {AWS}"), encoding="utf-8")
        (self.trash_dir() / "link.json").symlink_to(outside)
        code, out = self.run_redact("--apply")
        self.assertEqual(code, 0)
        self.assertIn("trash/broken: skipped", out)
        self.assertIn("trash/link: skipped (symlink)", out)
        self.assertIn(AWS, outside.read_text(encoding="utf-8"))  # the link target is never rewritten

    def test_a_trash_folder_that_is_a_symlink_is_not_scanned(self):
        self.save("clean", "clean answer")
        elsewhere = self.tmp / "elsewhere"
        elsewhere.mkdir()
        victim = elsewhere / "x.json"
        victim.write_text(json_note(f"x {AWS}"), encoding="utf-8")
        self.trash_dir().symlink_to(elsewhere)
        code, out = self.run_redact("--apply")
        self.assertEqual(code, 1)
        self.assertIn("cannot read trash", out)
        self.assertIn(AWS, victim.read_text(encoding="utf-8"))


def json_note(prompt):
    return json.dumps({"v": 1, "id": "outside", "prompt": prompt, "answer": "a"})


if __name__ == "__main__":
    unittest.main()
