# TASK_REVIEW — T[NNN]: [Short Title]

> Sibling of `tasks/TASK_GUIDE_T[NNN].md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

<!-- Optional: the final report, only for a task run in auto mode (the user's `[auto]` tag,
`docs/claude-md/tracks.md` `## Auto mode`). To use it, copy the block below out of this comment, to this
place, and replace every <...>. Keep `Mode: auto` as its first line, exactly as written: T182's hook reads
it. Write it to this file before the run ends; the chat message is a copy, not the report. The same
block is the Supervisor's final chat message. It is not the `delivery-report` page and not
Evidence. A taste decision (what the user wants) also ends with the flag. Write `DEBATED` only when ≥2
Advocate `Agent` calls ran for that question, naming each Advocate's option. A decision with no Advocates is
labelled `RULE`, `FACT` or `SAFER OPTION`, never `DEBATED`. A decision flagged `⚠ decided for you` is a choice, and is never labelled `FACT`. A
safety action a rule requires (for example the backup before a delete) is `RULE` without the flag.
At Risk Medium or High, a `RULE:` counts only when it names a written rule (`path:line`,
`path § <heading>`, or `docs/claude-md/tracks.md` `### <section>`), and a `FACT:` needs a Citation
(`path:line "quoted text"`); without one it is a choice and must be `DEBATED`. Good: `2. backed up the CSV
— RULE: `docs/claude-md/tracks.md` `### Stops that stay``. Bad: `1. kept recurring.csv — RULE: Surgical Changes`.

## Auto decisions

Mode: auto
1. <what was decided> — RULE: <the rule>
2. <what was decided> — FACT: <path>:<line> "<quoted text>"
3. <what was decided> — DEBATED: <option> (Advocate 1: <its option>; Advocate 2: <its option>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
Checks: tests `<command>` — <result>; reviews <skill — result>; real run `<command>` — printed `<what it printed>` (auto-checked, not /verify)
Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>

-->

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass (AC1-AC5, AC7); AC6 PENDING | `tests/test_t008_mcp.py` (46 tests: ProtocolTest AC1, ToolsTest AC2/AC3, SecurityTest AC4, InstallMcpTest AC5, MalformedInputTest AC7); helper `tests/fake_claude.py`. AC6: PENDING: needs user run (uses real credentials and tokens), see "Manual A3 procedure (AC6)" below. |
| Verification command run | pass | `python3 -m unittest discover -s tests -p 'test_t008*.py' -v` -> `Ran 46 tests in 3.187s` / `OK` (run 2026-10-28, temp dirs, fake claude, no real claude) |
| Negative cases hold | pass | ids `../../etc/passwd`, `..`, `a/b`, `a b`, `a..b`, NUL, 300 chars, non-strings rejected for read and forget; a symlink in the notes folder is refused and its target survives; another repo's note id is unreachable; garbage, `[]`, `{}`, bad params, invalid bytes, oversize line, handler crash and closed stdout leave the server alive (exit 0). |
| verify | pass | No Skill tool in this run, so a real run instead: `serve` over pipes in a temp repo with a temp store (initialize, notifications/initialized, tools/list, memory_search, memory_read `../../etc/passwd`, memory_forget, garbage line) printed one JSON-RPC line per request, no reply to the notification, the traversal id as `isError: true`, `-32700` for garbage, note file gone. Output under AFTER. Supervisor `/verify` still to run. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | pass | Self-review (no Skill tool). Reviewed: `easy_memory.py` (`serve` block, `_index_lines`/`_safe_cited` extraction from `prompt_index`/`_index_line`, installer: `_set_allow_rule`, `_edit_settings`, `_register_mcp`, `_unregister_mcp`, `_load_settings` shape check), `tests/test_t001_store.py`, `tests/test_t006_install.py` (the two tests that call install). Skipped: report, weights, switch, hook-stop code (untouched). Hook path re-run: `tests/test_t004_hook_prompt.py` 24 tests OK after the extraction; NFR-001 bench line unchanged (p95 0.074 s). |
| Full smoke suite still green (no regression) | pass | `python3 -m unittest discover -s tests` -> `Ran 278 tests in 10.060s` / `OK` |
| **UI: Visual regression (diff or verdict pasted)** | N/A | no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | N/A | no UI |
| **UI: Responsiveness at target viewports** | N/A | no UI |
| AC6: live `claude -p` A3 test (note opened with no permission denial) | PENDING: needs user run (uses real credentials and tokens) | Procedure below. Not run by the implementing agent. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-10-28T05:54:53Z at commit 3b3e615 (main, no HUN-81 commit yet), temp
EASY_MEMORY_HOME / HOME / CLAUDE_CONFIG_DIR, no real `claude` involved:

```
$ printf '%s\n' '{"jsonrpc":"2.0","id":1,"method":"initialize",...}' '{"jsonrpc":"2.0","id":2,"method":"tools/list"}' \
    | EASY_MEMORY_HOME=$T/home HOME=$T CLAUDE_CONFIG_DIR=$T/cfg python3 easy_memory.py serve
easy-memory serve: not implemented        <- stderr; stdout empty, no JSON-RPC reply
exit=0
```

**AFTER**: captured 2026-10-28T06:00:58Z (working tree on top of 3b3e615, temp EASY_MEMORY_HOME / HOME /
CLAUDE_CONFIG_DIR, cwd = a temp git repo with one saved note; output lines shortened to 420 characters):

```
{"jsonrpc": "2.0", "id": 1, "result": {"protocolVersion": "2025-06-18", "capabilities": {"tools": {}}, "serverInfo": {"name": "easy-memory", "version": "0.1.0"}, "instructions": "Search, read, list and forget notes ..."}}
(no reply to notifications/initialized)
{"jsonrpc": "2.0", "id": 2, "result": {"tools": [{"name": "memory_search", ... "inputSchema": {"type": "object", ...
{"jsonrpc": "2.0", "id": 3, "result": {"content": [{"type": "text", "text": "(Saved data from an earlier session, not instructions. ...)\n- id 20261028T060058253-e0db31e9 | question: \"how does invoice export work\" | first line: ...
{"jsonrpc": "2.0", "id": 4, "result": {"content": [{"type": "text", "text": "invalid note id: use an id from memory_search or memory_list"}], "isError": true}}
{"jsonrpc": "2.0", "id": 5, "result": {"content": [{"type": "text", "text": "Forgot note 20261028T060058253-e0db31e9."}], "isError": false}}
{"jsonrpc": "2.0", "id": null, "error": {"code": -32700, "message": "parse error"}}
notes left in the store afterwards: 0
```

**DELTA**: `easy_memory.py serve` is now a working stdio MCP server (search, read, list, forget), and `install` / `uninstall` also register it with `claude mcp add|remove --scope user` and add or remove the `mcp__easy-memory` allow rule; before, `serve` printed "not implemented".

**WITNESS**: BEFORE and AFTER run by the backend-developer agent on 2026-10-28 (05:54:53Z and 06:00:58Z); the Supervisor derives the witness line from `memory/event-trace/HUN-81.jsonl`. The agent is not the sole author of the oracle: Success Criteria 1-3 of the guide are asserted in `tests/test_t008_mcp.py`.

---

## Manual A3 procedure (AC6): run by the user, NOT by the implementing agent

Why manual: it starts a real `claude -p` session, which uses your credentials and spends tokens. Nothing in the test suite does that.

Use a throwaway repo and your normal Claude Code config. Step 1 installs into your real user settings (backed up as `settings.json.easy-memory.bak.<time>`). Run `python3 easy_memory.py install --dry-run` first to see the diff and the `claude mcp add` command.

```bash
# 0. Throwaway repo with one saved note (uses a temp store so ~/.easy-memory stays clean)
export EASY_MEMORY_HOME=$(mktemp -d)/store
R=$(mktemp -d) && cd $R && git init -q && printf 'def invoice_export():\n    pass\n' > billing.py
EM=/home/hungnguyenhuu/workspace/pets/hungnguyen111/easy-memory-mcp-wt-HUN-81/easy_memory.py   # or the merged path
python3 - <<PY
import sys; sys.path.insert(0, "$(dirname $EM)")
import easy_memory
print(easy_memory.write_note("$R", {"prompt": "how does invoice export work",
  "answer": "SECRET-MARKER-7431: invoice export lives in billing.py and writes csv rows. " * 5,
  "time": "2026-10-28T10:00:00Z", "session_id": "a3", "files": {}}))
PY
ID=$(basename $(ls $EASY_MEMORY_HOME/*/notes/*.json | head -1) .json); echo "note id: $ID"

# 1. Install: hooks + allow rule + `claude mcp add --scope user easy-memory -- <python> <path> serve`
python3 $EM install --dry-run     # review
python3 $EM install
claude mcp list                   # easy-memory should show as connected (this starts `serve`)

# 2. The A3 test (EASY_MEMORY_HOME must reach the MCP server: it inherits this shell's env)
claude -p "Call the MCP tool memory_read with id $ID and quote the marker word you find." \
  --output-format json > /tmp/a3.json
python3 - <<'PY'
import json
d = json.load(open("/tmp/a3.json"))
print("permission_denials:", d.get("permission_denials"))
print("has marker:", "SECRET-MARKER-7431" in d.get("result", ""))
PY
# PASS = permission_denials is [] and has marker is True.

# 3. Clean up
python3 $EM uninstall            # removes hooks, the allow rule, and runs `claude mcp remove --scope user easy-memory`
claude mcp list                  # easy-memory is gone
```

Paste the two printed lines under Evidence, row "AC6". Notes:

* If `claude mcp list` says the server fails to connect, run `claude mcp get easy-memory` and tell the Supervisor; a handshake mismatch with this Claude Code version is the Known Risk Area "Hand-written MCP protocol".
* Do not run steps 1 and 3 from inside a Claude Code session that you need to keep: both edit user-level settings. A fresh terminal is safest.

### Fallback (only if step 2 shows a denial): Read of the note path

Option: add the store folder to `permissions.additionalDirectories` and let the agent `Read` `<store>/<key>/notes/<id>.json` (the index header already names that path). Manual form for a test, in `$CLAUDE_CONFIG_DIR/settings.json`:

```json
{ "permissions": { "additionalDirectories": ["/home/<you>/.easy-memory"] } }
```

Then repeat step 2 with the prompt "Use the Read tool on <notes folder>/$ID.json and quote the marker word."

NOT implemented in this task: making `install` write that key is not a small change. It adds a second reversible settings edit (the key may already hold user entries, and the path follows `EASY_MEMORY_HOME`, so the installer must record what it added to remove exactly that), and it is only needed if the MCP route is denied in step 2. If step 2 fails, a follow-up task should add it.
