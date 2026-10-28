"""A fake `claude` executable for tests (HUN-81). It never reads credentials or the network.

Tests put the folder from install_fake_claude() first on PATH, so `claude mcp add|remove`
reaches this script and never the real CLI. It records every call as one JSON argv line in
$FAKE_CLAUDE_LOG and keeps a "registered" flag in $FAKE_CLAUDE_STATE:
  mcp add     fails (exit 1, "already exists") if flagged, else flags it
  mcp remove  fails (exit 1, "No MCP server found") if not flagged, else unflags it
  FAKE_CLAUDE_FAIL=1 makes every call exit 1 (a claude that is broken).
"""
import json
import os
import stat
import sys
from pathlib import Path

SCRIPT = """#!{python}
import json, os, sys
with open(os.environ["FAKE_CLAUDE_LOG"], "a") as log:
    log.write(json.dumps(sys.argv[1:]) + "\\n")
state = os.environ["FAKE_CLAUDE_STATE"]
if os.environ.get("FAKE_CLAUDE_FAIL"):
    sys.stderr.write("fake claude: forced failure\\n")
    sys.exit(1)
args = sys.argv[1:3]
if args == ["mcp", "add"]:
    if os.path.exists(state):
        sys.stderr.write("MCP server easy-memory already exists in user config\\n")
        sys.exit(1)
    open(state, "w").write(json.dumps(sys.argv[1:]))
elif args == ["mcp", "remove"]:
    if not os.path.exists(state):
        sys.stderr.write("No MCP server found with name: easy-memory\\n")
        sys.exit(1)
    os.unlink(state)
else:
    sys.stderr.write("fake claude: unexpected call\\n")
    sys.exit(2)
"""


def install_fake_claude(folder):
    """Write folder/claude (executable) and return the env entries it needs."""
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    script = folder / "claude"
    script.write_text(SCRIPT.format(python=sys.executable), encoding="utf-8")
    script.chmod(script.stat().st_mode | stat.S_IXUSR)
    return {"FAKE_CLAUDE_LOG": str(folder / "calls.log"), "FAKE_CLAUDE_STATE": str(folder / "registered")}


def fake_path(folder):
    """PATH with the fake claude first."""
    return str(folder) + os.pathsep + os.environ.get("PATH", "")


def read_calls(folder):
    """The argv lists (without the program name) the fake claude received, in order."""
    log = Path(folder) / "calls.log"
    if not log.exists():
        return []
    return [json.loads(line) for line in log.read_text(encoding="utf-8").splitlines()]
