"""easy-memory: per-repo session notes for Claude Code (standard library only).

This module holds the subcommand table and the note store. A repo key names
the store folder ~/.easy-memory/<key>/ (override: EASY_MEMORY_HOME). Git
worktrees share the main repo's store. Nothing is ever written inside a repo.
"""
import argparse
import hashlib
import json
import os
import secrets
import subprocess
import sys
import time
from pathlib import Path

FORMAT_VERSION = 1
GIT_TIMEOUT_SECONDS = 5


class StoreError(OSError):
    """The store cannot be written. Callers (hooks) decide whether to swallow it."""


def store_home():
    """Store root: $EASY_MEMORY_HOME if set and not empty, else ~/.easy-memory."""
    override = os.environ.get("EASY_MEMORY_HOME")
    return Path(override) if override else Path.home() / ".easy-memory"


def _identity_path(path):
    """The path that names a repo: the git common dir, else the folder's real path."""
    real = os.path.realpath(path)
    try:
        res = subprocess.run(
            ["git", "-C", real, "rev-parse", "--path-format=absolute",
             "--git-common-dir"],
            capture_output=True, text=True, timeout=GIT_TIMEOUT_SECONDS)
        common = res.stdout.strip() if res.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        common = ""
    return os.path.realpath(common) if common else real


def repo_key(path):
    """Stable 16-hex-character key for a folder; worktrees of one repo share it."""
    return hashlib.sha256(_identity_path(path).encode()).hexdigest()[:16]


def _private_dir(path):
    """Create path (and parents) with mode 0700, whatever the umask."""
    path = Path(path)
    for folder in reversed([path, *path.parents]):
        if folder.exists():
            continue
        try:
            folder.mkdir(mode=0o700)
        except FileExistsError:  # another process created it first
            continue
        folder.chmod(0o700)
    path.chmod(0o700)


def _atomic_write(folder, name, text):
    """Write text to folder/name through a 0600 temp file and an atomic rename."""
    tmp = Path(folder) / f".{name}.{secrets.token_hex(4)}.tmp"
    fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            os.fchmod(handle.fileno(), 0o600)
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(tmp, Path(folder) / name)
    except BaseException:
        try:
            os.unlink(tmp)
        except OSError:
            pass
        raise


def _new_note_id():
    now = time.time()
    stamp = time.strftime("%Y%m%dT%H%M%S", time.gmtime(now))
    return f"{stamp}{int(now % 1 * 1000):03d}-{secrets.token_hex(4)}"


def write_note(path, note):
    """Save note (a dict) in the store of the repo at path; return the file path.

    Adds "v" (format version) and "id". Raises StoreError if the store is not writable.
    """
    key = repo_key(path)
    store = store_home() / key
    notes = store / "notes"
    try:
        _private_dir(notes)
        meta = store / "meta.json"
        if not meta.exists():
            _atomic_write(store, "meta.json", json.dumps(
                {"v": FORMAT_VERSION, "path": _identity_path(path)}, indent=2))
        while True:
            note_id = _new_note_id()
            if not (notes / f"{note_id}.json").exists():
                break
        body = {**note, "v": FORMAT_VERSION, "id": note_id}
        _atomic_write(notes, f"{note_id}.json", json.dumps(body, indent=2))
    except OSError as err:
        raise StoreError(f"cannot write easy-memory store under {store_home()}: {err}") from err
    return str(notes / f"{note_id}.json")


def read_notes(path):
    """Notes of the repo at path, oldest first. Skips corrupt and newer-version files."""
    notes = store_home() / repo_key(path) / "notes"
    try:
        names = sorted(name for name in os.listdir(notes) if name.endswith(".json"))
    except OSError:
        return []
    found = []
    for name in names:
        try:
            data = json.loads((notes / name).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        version = data.get("v") if isinstance(data, dict) else None
        if isinstance(version, bool) or not isinstance(version, int):
            continue
        if 1 <= version <= FORMAT_VERSION:
            found.append(data)
    return found


def _not_implemented(name):
    # stderr: a hook's stdout is added to the prompt, so stubs must not write there.
    def handler(args):
        print(f"easy-memory {name}: not implemented", file=sys.stderr)
        return 0
    return handler


SUBCOMMANDS = {name: _not_implemented(name) for name in (
    "hook-stop", "hook-prompt", "serve", "report", "install", "uninstall")}


def main(argv=None):
    parser = argparse.ArgumentParser(prog="easy_memory")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in SUBCOMMANDS:
        sub.add_parser(name)
    args = parser.parse_args(argv)
    return SUBCOMMANDS[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
