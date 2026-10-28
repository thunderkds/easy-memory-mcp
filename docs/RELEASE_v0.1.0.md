# easy-memory-mcp v0.1.0 (prototype)

**Proposed tag:** `v0.1.0` on commit `e412e14` (not tagged yet).
**Verdict:** NO-GO until two items are closed: the production approval, and the live permission check (HUN-81 AC6).
This page is a plan. The operator runs it. Nothing here was run against your real Claude settings.

## What this release is

A single-file Python tool (`easy_memory.py`, standard library only) that gives Claude Code a memory per repo.

- A **Stop hook** saves one note after each answer of 200 characters or more.
- A **prompt hook** adds a short index of matching notes to your next prompt. The agent can ignore it or open a note.
- An **MCP server** lets the agent search, read, list and forget notes.
- A **switch** turns memory on, off or auto for each repo. Auto is on for even days and off for odd days, so you get a fair comparison.
- A **report** compares sessions with memory on and off, using Claude's own session logs.

## Release notes

### Features
- HUN-74: repo key (git worktrees share one store) and atomic, versioned note store under `~/.easy-memory/`. Files are 0600 and folders 0700.
- HUN-75: Stop hook saves one note per turn. It cites only files that exist in the repo.
- HUN-76: word weights are built in the background and never inside a hook.
- HUN-77: prompt hook injects a framed index. Note text is quoted as data and cannot leave the frame.
- HUN-78: `switch on|off|auto` per repo, and one `prompts.log` line per prompt.
- HUN-79: `install` and `uninstall` edit the user-level Claude Code settings, with a backup.
- HUN-80: `report` compares memory on and off.
- HUN-81: MCP server with `memory_search`, `memory_read`, `memory_list` and `memory_forget`.

### Internal
- HUN-82: independent end-to-end tests. 307 tests pass (3 skipped: opt-in or host-dependent).

### Measured
- `hook-prompt` p95 0.212 s on a 7,831-file repo with 200 notes (limit 1 s).
- `hook-stop` p95 0.066 s (limit 2 s).
- Weights file 1.69 MB, loads in 0.024 s.

### Known limits
- **D1:** `hook-prompt` gets about 1 ms slower per saved note. It passes the 1 s limit at roughly 1,000 to 3,000 notes. At about 5 s, Claude Code's hook timeout kills the hook and the index silently disappears.
- **D2:** `hook-stop` reads the whole transcript into memory (a 400 MB transcript used 808 MB).
- **D3:** the background weights build has no cap when Claude Code starts in a folder that is not a git repo.
- Answers and prompts are saved in clear text (mode 600). Do not use it on a repo where answers can hold secrets you would not keep on disk.
- The live check that opening a note causes no permission prompt (HUN-81 AC6) has not run.

## Pre-deploy checks

1. Run from the **main checkout**, never a worktree: `cd /home/hungnguyenhuu/workspace/pets/hungnguyen111/easy-memory-mcp && git status --short && git branch --show-current`. Pass: no output except `?? .claude/hooks/.state/`, and the branch is `main`.
2. Smoke test, defined before the deploy: `python3 -m unittest discover -s tests`. Pass: `OK (skipped=3)` with `Ran 307 tests`.
3. Back up your settings by hand as well: `cp "$CLAUDE_CONFIG_DIR/settings.json" "$CLAUDE_CONFIG_DIR/settings.json.manual-backup"`. Pass: the copy exists.

## Deploy steps (the operator runs these)

1. Preview: `python3 easy_memory.py install --dry-run`. Read the diff. Pass: it adds only a `Stop` entry, a `UserPromptSubmit` entry and `mcp__easy-memory` in `permissions.allow`, and prints the `claude mcp add` command. Nothing is written.
2. Install: `python3 easy_memory.py install`. Pass: it prints `installed`, a `backup:` path, and `mcp: registered easy-memory`.
3. Turn it on for one repo and look: `cd <your repo> && python3 /home/hungnguyenhuu/workspace/pets/hungnguyen111/easy-memory-mcp/easy_memory.py switch`. Pass: it prints `switch: auto` and what that means today.

## Post-deploy health check

1. `claude mcp list`. Pass: `easy-memory` is listed and connected.
2. Use Claude Code in a test repo, ask for a long answer (200 characters or more), then run `ls ~/.easy-memory/*/notes`. Pass: one new `.json` note appears.
3. Start a new prompt in that repo on a day when the switch is on. Pass: the prompt carries an `<easy-memory-index>` block, or nothing if no note matches.
4. The HUN-81 AC6 procedure (`tasks/TASK_REVIEW_HUN-81.md`, "Manual A3 procedure"). Pass: the agent opens a note by id and `permission_denials` is an empty list.

## Rollback plan

**Roll back if:** Claude Code fails to start or shows a hook error on every prompt, prompts feel slow (more than about 1 s), the MCP server shows as failed in `claude mcp list`, or the permission check in step 4 fails.

Reverse steps, in order:
1. `python3 /home/hungnguyenhuu/workspace/pets/hungnguyen111/easy-memory-mcp/easy_memory.py uninstall`. Pass: it prints `uninstalled`, removes both hooks and the allow rule, and your other settings stay.
2. If `claude` was missing or the removal printed a manual command, run: `claude mcp remove --scope user easy-memory`.
3. If the settings file is still wrong, restore the backup: `cp "$CLAUDE_CONFIG_DIR"/settings.json.easy-memory.bak.<timestamp> "$CLAUDE_CONFIG_DIR/settings.json"`. Use the oldest backup, or `settings.json.manual-backup`.
4. Optional: delete the saved notes with `python3 easy_memory.py uninstall --purge`. This prints the size first and deletes only `~/.easy-memory`.
5. Verify: `claude mcp list` no longer shows `easy-memory`, and `grep easy_memory "$CLAUDE_CONFIG_DIR/settings.json"` prints nothing.

## GO gate

| Item | State |
|---|---|
| Stage 5 evidence green for all 9 tasks | Yes (307 tests; each task run by hand in temp folders) |
| Rollback plan with triggers and exact reverse steps | Yes |
| Post-deploy health check with a pass condition | Yes |
| Deploy command known | Yes (`install`, from PROJECT_SPEC.md target: your machine) |
| HUN-81 AC6 live check | **Open** (needs your credentials; steps above) |
| Production approval for v0.1.0 @ e412e14 | **Open** (asked in chat) |

This is a recommendation. You run the steps.
