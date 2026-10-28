"""easy-memory: per-repo session notes for Claude Code (standard library only).

This module holds the subcommand table and the note store. A repo key names
the store folder ~/.easy-memory/<key>/ (override: EASY_MEMORY_HOME). Git
worktrees share the main repo's store. Nothing is ever written inside a repo.
"""
import argparse
import hashlib
import json
import os
import posixpath
import re
import secrets
import subprocess
import sys
import time
from pathlib import Path

FORMAT_VERSION = 1
GIT_TIMEOUT_SECONDS = 5
MIN_ANSWER_CHARS = 200
MAX_CITED_FILE_BYTES = 5 * 1024 * 1024
MAX_STDIN_CHARS = 10 * 1024 * 1024
# A path-like token that ends in a known extension, with an optional :line suffix.
# The token length is capped so a long run of word characters cannot make the
# search quadratic; the lookahead keeps ".js" from matching inside ".json".
CITED_PATH = re.compile(
    r"(\.?[A-Za-z0-9_][A-Za-z0-9_.\-/]{0,200}\.(?:tsx|ts|jsx|js|java|py|kt|ftl|sql|xml|"
    r"yml|yaml|json|md))(?![A-Za-z0-9_])(?::\d+)?")


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


def log_hook_error(command, err):
    """Append one error line to <store root>/hook.log (0600). Never raises."""
    try:
        text = " ".join(f"{type(err).__name__}: {err}".split())[:300]
        stamp = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        home = store_home()
        _private_dir(home)
        fd = os.open(home / "hook.log", os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, "a", encoding="utf-8") as handle:
            os.fchmod(handle.fileno(), 0o600)
            handle.write(f"{stamp} {command} error: {text}\n")
    except Exception:  # a hook must stay silent even when it cannot log
        pass


def _repo_root(cwd):
    """Top folder of the git work tree that holds cwd, else cwd itself."""
    try:
        res = subprocess.run(["git", "-C", cwd, "rev-parse", "--show-toplevel"],
                             capture_output=True, text=True, timeout=GIT_TIMEOUT_SECONDS)
        top = res.stdout.strip() if res.returncode == 0 else ""
    except (OSError, subprocess.SubprocessError):
        top = ""
    return top or cwd


def _tracked_files(root):
    try:
        res = subprocess.run(["git", "-C", root, "ls-files", "-z"],
                             capture_output=True, text=True, timeout=GIT_TIMEOUT_SECONDS)
    except (OSError, subprocess.SubprocessError):
        return []
    return [name for name in res.stdout.split("\0") if name] if res.returncode == 0 else []


def _sha256_file(path):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _hash_if_repo_file(root_real, rel):
    """sha256 of root/rel if it is a regular file inside the repo and <= 5 MB, else None."""
    full = os.path.realpath(os.path.join(root_real, rel))
    if os.path.commonpath([root_real, full]) != root_real:
        return None  # a ".." path or a symlink that leaves the repo
    try:
        if not os.path.isfile(full) or os.path.getsize(full) > MAX_CITED_FILE_BYTES:
            return None
        return _sha256_file(full)
    except OSError:
        return None


def cited_files(text, root):
    """{repo-relative path: sha256} for repo files that text cites.

    A path counts if the file exists under root. A bare name or partial path
    counts only if exactly one tracked file matches it. No full-tree walk.
    """
    root_real = os.path.realpath(root)
    tracked = None
    found = {}
    for match in CITED_PATH.finditer(text):
        ref = posixpath.normpath(match.group(1))
        if ref in found or ref.startswith(("..", "/")):
            continue
        digest = _hash_if_repo_file(root_real, ref)
        if digest is None:
            if tracked is None:
                tracked = _tracked_files(root_real)
            hits = [name for name in tracked if name == ref or name.endswith("/" + ref)]
            if len(hits) != 1:
                continue
            ref = hits[0]
            if ref in found:
                continue
            digest = _hash_if_repo_file(root_real, ref)
        if digest is not None:
            found[ref] = digest
    return found


def _typed_text(content):
    """What the user typed in one transcript message, or None if it is not a prompt."""
    if isinstance(content, list):
        content = "\n".join(block.get("text", "") for block in content
                            if isinstance(block, dict) and block.get("type") == "text"
                            and isinstance(block.get("text"), str))
    if not isinstance(content, str):
        return None
    content = re.sub(r"<system-reminder>.*?</system-reminder>", "", content, flags=re.S)
    if "<local-command-" in content:
        return None  # output of a local slash command, not something the user typed
    command = re.search(r"<command-name>(.*?)</command-name>", content, re.S)
    if command:
        args = re.search(r"<command-args>(.*?)</command-args>", content, re.S)
        content = f"{command.group(1).strip()} {args.group(1).strip() if args else ''}"
    content = content.strip()
    return content or None


def last_user_prompt(transcript_path):
    """Text of the last real user message in a transcript JSONL (skips tool results).

    Lines that are not valid JSON (a partial last line) are ignored.
    """
    with open(transcript_path, "rb") as handle:
        lines = handle.read().splitlines()
    for raw in reversed(lines):
        try:
            entry = json.loads(raw)
        except ValueError:
            continue
        if not isinstance(entry, dict) or entry.get("type") != "user":
            continue
        if entry.get("isSidechain") or entry.get("isMeta"):
            continue
        message = entry.get("message")
        text = _typed_text(message.get("content")) if isinstance(message, dict) else None
        if text:
            return text
    return None


def save_stop_note(data):
    """Write the note for one Stop event (a dict). Returns the note path or None."""
    if data.get("stop_hook_active"):
        return None
    answer = data.get("last_assistant_message")
    if not isinstance(answer, str) or len(answer.strip()) < MIN_ANSWER_CHARS:
        return None
    cwd = data.get("cwd")
    cwd = cwd if isinstance(cwd, str) and cwd else os.getcwd()
    transcript = data.get("transcript_path")
    if not isinstance(transcript, str) or not transcript:
        raise ValueError("Stop input has no transcript_path")
    prompt = last_user_prompt(transcript)
    if prompt is None:
        raise ValueError("no user prompt found in transcript")
    session_id = data.get("session_id")
    return write_note(cwd, {
        "prompt": prompt,
        "answer": answer,
        "time": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "session_id": session_id if isinstance(session_id, str) else "",
        "files": cited_files(answer, _repo_root(cwd)),
    })


def hook_stop(args):
    """Stop hook: stdin is the hook JSON. Prints nothing; always returns 0 (NFR-004)."""
    try:
        data = json.loads(sys.stdin.read(MAX_STDIN_CHARS))
        if not isinstance(data, dict):
            raise ValueError("Stop input is not a JSON object")
        save_stop_note(data)
    except Exception as err:
        log_hook_error("hook-stop", err)
    return 0


def _not_implemented(name):
    # stderr: a hook's stdout is added to the prompt, so stubs must not write there.
    def handler(args):
        print(f"easy-memory {name}: not implemented", file=sys.stderr)
        return 0
    return handler


SUBCOMMANDS = {name: _not_implemented(name) for name in (
    "hook-stop", "hook-prompt", "serve", "report", "install", "uninstall")}
SUBCOMMANDS["hook-stop"] = hook_stop


def main(argv=None):
    parser = argparse.ArgumentParser(prog="easy_memory")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in SUBCOMMANDS:
        sub.add_parser(name)
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        # argparse exits 2, which would block a hook's event; hooks always exit 0.
        if (sys.argv[1:] if argv is None else list(argv))[:1] == ["hook-stop"]:
            log_hook_error("hook-stop", ValueError("bad command line"))
            return 0
        raise
    return SUBCOMMANDS[args.command](args)


if __name__ == "__main__":
    sys.exit(main())
