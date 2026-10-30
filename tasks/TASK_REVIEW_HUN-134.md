# TASK_REVIEW — HUN-134: easy-memory installs as a Claude Code plugin

> Sibling of `tasks/TASK_GUIDE_HUN-134.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Auto decisions

Mode: auto
1. Registered the draft on Linear through the Linear connector (board assigned HUN-134; P1→High, labels `complexity:c2`, `risk:medium`, project easy-memory-mcp), because `board_sync.py` could not run — FACT: scripts/board_sync.py:58 "`LINEAR_API_KEY` is read from the environment only and never printed (NFR-001)." (the env had no key: `pull failed: LINEAR_API_KEY is not set`)
2. Extended track — RULE: AGENTS.md:142 "The extended track applies if any of: C2 or above; Risk Medium or High"
3. Requirement Fidelity Gate signed `auto (Supervisor)` — RULE: docs/claude-md/tracks.md:215 "Signed `auto (Supervisor)`, not by the user."
4. Spawned backend-developer on opus (CLI Model Table empty) and the Supervisor made the worktree itself (`git worktree add ../easy-memory-mcp-HUN-134`) instead of a Common-Infrastructure spawn — DEBATED: opus + Supervisor worktree (Advocate 1: opus, Supervisor runs `git worktree add`; Advocate 2: sonnet, Common-Infrastructure agent creates the worktree per docs/claude-md/pipeline-stages.md:169) ⚠ decided for you — please review
5. AC 8 evidence without your login: no credential linked into the throwaway config (it printed `Not logged in · Please run /login`); instead a live run with your real config + `--plugin-dir plugin` (no settings write, throwaway `EASY_MEMORY_HOME`) plus the installed plugin copy's hooks driven with that run's real transcript — DEBATED: never touch credentials (Advocate 1: symlink `~/.claude-hung2/.credentials.json` into the throwaway config for the run; Advocate 2: no credentials, live run with real config + `--plugin-dir`, AC 8 plugin-only session left partial) ⚠ decided for you — please review
6. Kept an untracked, refreshed copy of `tasks/TASK_GUIDE_HUN-134.md` in the main checkout (the spawn hook reads guides there; a fast-forward of `main` was denied as a merge) — DEBATED: keep and refresh until merge (Advocate 1: keep it so main-checkout hooks find the guide; Advocate 2: delete it now so main is untouched and the merge cannot be blocked) ⚠ decided for you — please review. **Before you merge: `rm tasks/TASK_GUIDE_HUN-134.md` in the main checkout**, or git refuses the merge.
7. security-review done by an independent reviewer agent after the built-in skill failed (`fatal: ambiguous argument 'origin/HEAD...'`) — FACT: memory/MEMORY.md:37 "security-review needs `origin`; board has no Ready-for-Review ... use an independent agent"
8. Linear stays In Progress (no Ready-for-Review state on the board); the board-cache row moves to Ready for Review on the task branch by hand — FACT: memory/MEMORY.md:37 "board has no Ready-for-Review"
9. README allow rule kept as the guide states it (security P3: it also allows `memory_forget`) — FACT: tasks/TASK_GUIDE_HUN-134.md:79 "the allow rule for the new tool names (`mcp__plugin_easy-memory_easy-memory`)"
10. Did not run `/verify`, merge, push, tag or move to Done — RULE: docs/claude-md/tracks.md § Never in auto mode (line 353)
Checks: tests `python3 -m unittest discover -s tests` — `Ran 434 tests in 24.865s` `OK (skipped=3)`; `claude plugin validate .` and `claude plugin validate plugin` — `✔ Validation passed`; reviews code-review — 0 P0, 1 P1 (process), 1 P2, security-review (independent agent) — pass, 3 × P3; real runs `experiments/hun-134/work/ac5.sh`, `ac6live.sh`, `ac8drive.sh` — see Evidence (auto-checked, not /verify)
Not done: merge (yours); /verify (yours); `git tag v0.2.0` + push (yours — Easy Kit T217 pins ref v0.2.0); `rm tasks/TASK_GUIDE_HUN-134.md` in the main checkout before merging; board description of HUN-134 still holds the pre-review guide (`board_sync.py update --guide HUN-134` needs `LINEAR_API_KEY`)
Paused: auto-mode check failed — Risk Medium, but the trace has no `security-review` Skill call

## Stage 4 findings

**code-review** (scope: `easy_memory.py` guard + install warning and their callers `hook_stop`, `hook_prompt`, `install_command`; `plugin/*`; `.claude-plugin/marketplace.json`; `tests/test_plugin.py`; `README.md`). Lane: `lane: C2, 10 files, 2272 lines, EXCEEDS (lines 2272 > 500); unpredicted: tasks/TASK_GUIDE_HUN-134.md` — 1773 lines are the test-guarded copy `plugin/easy_memory.py`; not under-labelled. Entry point `.claude-plugin/marketplace.json` → `plugin/` exists (reachable).

| Sev | File | Finding | Conf | Action |
|---|---|---|---|---|
| P1 (process) | — | The backend agent was stopped by the runner's background limit before its final report, so there is no `Startup reads:` line (the rule counts all reads as missing). The diff follows the guide (tests derive hooks from `HOOK_EVENTS`; copy-not-symlink decision measured) | 100 | Not fixable after the fact; recorded here |
| P2 | `easy_memory.py` `_plugin_defers_to_old_hooks` | A stale old hook entry (clone deleted) still makes the plugin defer, so no notes are saved, silently | 75 | Suggestion: log one `hook.log` line when deferring, or check the old hook's script path exists |

**security-review** (independent agent, `cmp` confirmed the copy is identical): `security-review: pass`. P3 only: README allow rule also auto-allows `memory_forget` (same breadth as the old `mcp__easy-memory` rule); `_is_ours` substring match can make the plugin defer (fails closed); `bin/easy-memory` breaks if invoked through a symlink. Checked, no issue: hook command quoting, `.mcp.json` args array, hooks always exit 0, guard never bypasses redaction or changes the store path, reads user-level settings only, no secrets.

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_plugin.py` (new, 16 tests): `ManifestTest` (AC 1–4: marketplace, manifest 0.2.0, hooks derived from `HOOK_EVENTS`, `.mcp.json`, byte-identical copy, no dev kit in plugin), `DoubleInstallTest` (AC 6 + edge cases: invalid settings, foreign hooks), `BinWrapperTest` (AC 5 wrapper), `InstallWarningTest` (AC 7). Full suite: `Ran 434 tests in 24.865s` / `OK (skipped=3)` |
| Verification command run | ☑ pass | `python3 -m unittest discover -s tests && claude plugin validate . && claude plugin validate plugin` → `OK (skipped=3)`, `✔ Validation passed`, `✔ Validation passed` |
| Negative cases hold | ☑ pass | AC 6 live (`ac6live.sh`, 2026-10-30 08:28:55Z, real config with old hooks + `--plugin-dir plugin`): 2 turns → `notes saved after turn 2 (expect 2): 2` — one note per turn, not two. Tests: invalid settings JSON → note saved; `enabledPlugins` false → install proceeds |
| Real run: marketplace install (AC 5) | ☑ pass | `ac5.sh` 2026-10-30 08:25:53Z, throwaway `CLAUDE_CONFIG_DIR`: `✔ Successfully installed plugin: easy-memory@easy-memory (scope: user)`; `claude plugin details`: `easy-memory 0.2.0` … `Hooks (2)  Stop, UserPromptSubmit` … `MCP servers (1)  easy-memory`; `cached easy_memory.py identical to repo root`; cached `bin/easy-memory switch on` → `switch: on`, `report` → exit 0 |
| Real run: note saved + index (AC 8) | ☑ pass (plugin-only session partial) | Live session with plugin (`ac6live.sh`): note `475f0bad466b2cd9/notes/20261030T082907438-54bf2fa6.json`; tool names `mcp__plugin_easy-memory_easy-memory__memory_read`, `mcp__plugin_easy-memory_easy-memory__memory_search` (T217 contract). Installed plugin copy alone (`ac8drive.sh`, 08:30:22Z, `CLAUDE_PLUGIN_ROOT` = cache, no old hooks): `hook-stop` exit 0 → `475f0bad466b2cd9/notes/20261030T083022805-02175209.json`; `hook-prompt` → `<easy-memory-index>\n- id 20261030T083022805-02175209 | question: "How does the kettle thermostat stop the heater? …"`. A fully plugin-only `claude -p` session needs a logged-in throwaway config (decision 5) |
| verify | ☑ pass | /verify run by the user from the Easy Kit session (personal-agentic-claude, 2026-10-30 08:42–08:47Z, haiku, throwaway `CLAUDE_CONFIG_DIR` + `EASY_MEMORY_HOME`): marketplace add + `claude plugin install easy-memory@easy-memory` → `✔ Successfully installed plugin`; `details`: `Hooks (2) Stop, UserPromptSubmit`, `MCP servers (1) easy-memory`; plugin-only live turn 1 saved `notes/20261030T084318430-ac61d23c.json`; turn 2 `injected: true` + 4 `mcp__plugin_easy-memory_easy-memory__*` tools; Easy Kit T217 `qa-expert` got the 2 plugin tool names and, with the README allow rule, `memory_search` returned `20261030T084318430-ac61d23c`; uninstall kept all 3 notes. Probe ⚠: real config with old hooks in settings.json + `--setting-sources project,local` → 0 notes, no log line (same weakness as code-review P2) |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Diff files + callers `hook_stop`, `hook_prompt`, `install_command`, `_is_ours`, `settings_path`; `site/`, `agents/`, `skills/`, `.claude/` untouched |
| Full smoke suite still green (no regression) | ☑ pass | `Ran 434 tests` `OK (skipped=3)`; existing install tests unchanged |
| **Companion score (easy-verifier)** | ☑ N/A | not run in this auto run |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | no UI |
| **UI: Responsiveness at target viewports** | ☑ N/A | no UI |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured by backend-developer in the worktree, before any implementation commit; HEAD `cf6e22b`):

```
$ date -u; claude --version; claude plugin validate .; ls plugin .claude-plugin
Fri Oct 30 08:13:02 AM UTC 2026
2.1.314 (Claude Code)
Validating components in: /home/hungnguyenhuu/workspace/pets/hungnguyen111/easy-memory-mcp-HUN-134
Validating skill: .../easy-memory-mcp-HUN-134/.claude/skills
  ❯ directory: This directory is a symlink and nothing in it was read ...
Validating agent: .../easy-memory-mcp-HUN-134/.claude/agents
  ❯ directory: This directory is a symlink and nothing in it was read ...
✘ Found 1 problem the plugin directory refuses a submission for:
  ❯ LICENSE: License missing (LICENSE_MISSING). ...
ℹ Found 1 plugin directory note:
  ❯ .claude-plugin/plugin.json file: MANIFEST_NOT_FOUND. No .claude-plugin/plugin.json. ...
✔ Validation passed with warnings
exit 0
ls: cannot access 'plugin': No such file or directory
ls: cannot access '.claude-plugin': No such file or directory
exit 2
```

No marketplace and no plugin exist: the validator only sees the repo root as a bare skills tree (MANIFEST_NOT_FOUND), and `plugin/` and `.claude-plugin/` are absent. Getting easy-memory today needs a clone plus `python3 easy_memory.py install`, which edits user settings.

**AFTER**: `claude plugin validate .` / `claude plugin validate plugin` → `✔ Validation passed`; throwaway install (2026-10-30 08:25:53Z):

```
✔ Successfully installed plugin: easy-memory@easy-memory (scope: user)
easy-memory 0.2.0
  Hooks (2)  Stop, UserPromptSubmit  (harness-only — no model context cost)
  MCP servers (1)  easy-memory  (tool schemas resolved at runtime; not counted)
cached easy_memory.py identical to repo root
```

**DELTA**: a user gets easy-memory with `/plugin marketplace add thunderkds/easy-memory-mcp` and `/plugin install easy-memory@easy-memory` — no clone, no `install` command, no settings edit; a leftover old install still gives one note per turn.

**WITNESS**: Supervisor session, 2026-10-30 08:25–08:30Z, scripts `experiments/hun-134/work/ac5.sh`, `ac6live.sh`, `ac8drive.sh` (gitignored), independent of the implementing agent; trace `memory/event-trace/HUN-134.jsonl`.
