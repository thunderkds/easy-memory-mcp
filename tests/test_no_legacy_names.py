"""HUN-218: tracked files name the two test repos only as Project A / Project B.

The real names are built from pieces so this file does not match its own search.
"""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LEGACY = ["tap" + "chat", "order" + "ly", "beauti" + "fly", "phan" + "py"]


class NoLegacyNamesTest(unittest.TestCase):
    def test_no_tracked_file_names_a_legacy_project(self):
        files = subprocess.run(["git", "ls-files", "-z"], cwd=ROOT, capture_output=True,
                               check=True).stdout.decode().split("\0")
        pattern = re.compile("|".join(LEGACY), re.IGNORECASE)
        hits = []
        for name in filter(None, files):
            path = ROOT / name
            try:
                text = path.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue  # binary or unreadable
            hits += [f"{name}:{n}" for n, line in enumerate(text.splitlines(), 1) if pattern.search(line)]
        self.assertEqual(hits, [], f"{len(hits)} lines still name a legacy project")


if __name__ == "__main__":
    unittest.main()
