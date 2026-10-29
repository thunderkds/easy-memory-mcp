# RUNBOOK — easy-memory-mcp
**Last updated**: 2026-10-28

> How to install, check and remove easy-memory. Full steps for each release are in `docs/RELEASE_<version>.md`.

---

## Service Identity

- **Name**: easy-memory (`easy_memory.py`)
- **Repo**: git@github.com:thunderkds/easy-memory-mcp.git (local: `/home/hungnguyenhuu/workspace/pets/hungnguyen111/easy-memory-mcp`)
- **Deployment target**: the user's machine only; installed into the user-level Claude Code settings (`$CLAUDE_CONFIG_DIR/settings.json`)
- **Tech**: Python 3, standard library only
- **Owner / on-call**: thunderkds

---

## Deploy Procedure

1. **Pre-deploy checks**: run from the main checkout; `git status --short` is clean; `python3 -m unittest discover -s tests` ends `OK`.
2. `python3 easy_memory.py install --dry-run` → read the diff. Nothing is written.
3. `python3 easy_memory.py install` → pass condition: `installed`, a `backup:` path, `mcp: registered easy-memory`.
4. **Post-deploy health check**: `claude mcp list` → pass condition: `easy-memory` is listed and connected.

---

## Rollback Procedure

- **Trigger conditions**: a hook error on every prompt, slow prompts (about 1 s or more), the MCP server failed, a permission prompt when opening a note.
- **Reverse steps** (in order):
  1. `python3 easy_memory.py uninstall` (removes both hooks and the allow rule).
  2. `claude mcp remove --scope user easy-memory` (only if step 1 printed it as a manual step).
  3. If the settings file is still wrong: `cp "$CLAUDE_CONFIG_DIR"/settings.json.easy-memory.bak.<timestamp> "$CLAUDE_CONFIG_DIR/settings.json"`.
  4. Optional: `python3 easy_memory.py uninstall --purge` deletes `~/.easy-memory` after printing its size.
- **Verify rollback**: `grep easy_memory "$CLAUDE_CONFIG_DIR/settings.json"` → no output; `claude mcp list` → no `easy-memory`.

---

## Health Checks & Dashboards

| Check | Command / URL | Pass condition |
|-------|---------------|----------------|
| Hooks and server registered | `claude mcp list` | `easy-memory` connected |
| Switch state | `python3 easy_memory.py switch` | prints `switch: <state>` |
| A note was saved | `ls ~/.easy-memory/*/notes` | a new `.json` after a long answer |
| Hook errors | `cat ~/.easy-memory/hook.log` | empty, or old lines only |
| On vs off | `python3 easy_memory.py report` | a table; "too few sessions" under 10 per group |

- **Dashboards**: none. Logs are `~/.easy-memory/hook.log` and `~/.easy-memory/<repo key>/prompts.log`.

---

## Common Failure Modes & Remediation

| Symptom | Likely cause | Remediation |
|---------|-------------|-------------|
| Hooks silently do nothing (exit 127) | Installed from a worktree that was deleted | Run `install` again from the main checkout |
| No index in prompts | Weights not built yet, switch is off today, or no note matches | `python3 easy_memory.py switch`; wait for the first background build |
| Index disappears after weeks | Too many notes (hook slower than its 5 s timeout) | Delete old notes, or `uninstall --purge`; known defect D1 |
| `install` aborts | Settings file is not valid JSON, or its folder is missing | Fix the file or `CLAUDE_CONFIG_DIR`; nothing was changed |

---

## On-Call / Escalation

1. **First responder**: thunderkds.
2. **Escalate to**: none (personal tool). Roll back first, then investigate.
3. **Comms**: none.

---

## Release Log

| Version / Tag | Date | Scope (Task IDs) | Deployer | Approved (by / when / answer) | Outcome |
|---------------|------|------------------|----------|-------------------------------|---------|
| v0.1.0 (commit 7916424, not tagged) | 2026-10-28 | HUN-74 to HUN-82 | installer run 2026-10-28T07:22:23Z (settings backup stamp) | user / 2026-10-28 / "Approve v0.1.0 @ 7916424 (Recommended)" | Planned (approved; AC6 live check still open) |

---

## Measurement Window (v0.1 on/off comparison)

Recorded 2026-10-29 from `~/.easy-memory/*/prompts.log` and the settings backup stamp. Times are UTC.

| Event | Time | Evidence |
|-------|------|----------|
| Hooks installed in the user settings | 2026-10-28T07:22:23Z | `settings.json.easy-memory.bak.20261028T072223Z` |
| Forced `on` and `off` sessions (verification, not part of the comparison) | 2026-10-28T07:22Z to 08:05Z and later | store `0e5001d12a9965ce` (43 lines), store `26b799979a291c4c` (3 lines): no `configured: auto` line |
| First `configured: auto` line in a scratch clone (not a real repo) | 2026-10-28T08:05:17Z | store `57e9c974e7888078` (1 line, path under `/tmp`) |
| **Window start: first `configured: auto` session in a real repo** | **2026-10-29T02:01:36Z** | store `c5aa0c6dafcc6672` (this repo), session `bf02bb49…` |
| Redaction (FR-009) shipped | not yet | Gate 0 in `PRD_v0.2.md`; write the date here when it ships |

Sample bar: 10 `configured == auto` sessions per group in one repo (`REPORT_MIN_SESSIONS`, `easy_memory.py:1063`). On 2026-10-29 the count is 1 session, in the `off` group.

Caveats:
- The window start is the Supervisor's reading of the logs. The user may set a different start.
- `report` groups by `effective` and does not yet filter on `configured`, so forced `on` and `off` sessions would enter the comparison (open item O5 in `PRD_v0.2.md`).
