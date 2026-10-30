**Date**: 2026-10-30
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: backend-developer
**Agent guide**: `agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/backend.md` in full
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/backend.md`
6. Read `easy_memory.py` sections: `HOOK_EVENTS`, `settings_path`, `hook_entries`, `_is_ours`, `install_command`, `uninstall_command`, `hook_stop`, `hook_prompt`, `serve_command`; and `README.md` `## Use it`
7. Read the Easy Kit spike results: `/home/hungnguyenhuu/workspace/pets/personal-agentic-claude/experiments/plugin-spike/README.md` (read-only; another repo)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-10-30 (Easy Kit session): "make this kit simple more … split this kit as small pieces … support to run as plugin, just call and do not care more about the way to setting up", then "plan easy-memory plugin", then "start both tasks as parallel". Easy Kit decision: `personal-agentic-claude/docs/brainstorming/BRAINSTORMING_LOG_distribution.md` (Option C) and its spike T216. easy-memory stays optional for the kit (user, 2026-10-28: "you have it, you reduce the token, if you don't have…").

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> A user gets easy-memory with `/plugin marketplace add thunderkds/easy-memory-mcp` and `/plugin install easy-memory@easy-memory`. No clone, no `install` command, no edit to their settings. The plugin runs the same Stop and prompt hooks and the same MCP server as `easy_memory.py install` does today, saves notes in the same store (`~/.easy-memory/`), and never runs twice when the old install is still present. `python3 easy_memory.py install` keeps working unchanged for users who want it.

**Out of scope** (what this task explicitly does NOT do):

* Changing note format, store location, ranking, hook output or MCP tools.
* Removing or changing `install` / `uninstall` behaviour, except the one warning in AC 7.
* Codex, Cursor or other CLIs (Codex plugin hooks need trust; open question from T216).
* Pushing, tagging a release, or listing the plugin in Easy Kit's marketplace (the user tags; Easy Kit T217 adds the listing).
* The site (`site/`).

**Requirement Refs**: the user quotes above; T216 spike facts.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [x] Restated intent confirmed to match the user's request (auto (Supervisor), 2026-10-30)
- [x] Every Acceptance Criterion below traces to the requirement

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: none. Easy Kit T217 depends on this task's tag.

**Entry point**: `.claude-plugin/marketplace.json` (repo root) → plugin folder `plugin/`.

**Known facts (measured in T216 and on 2026-10-30, Claude Code 2.1.314):**
- A plugin MCP server's tools are named `mcp__plugin_<plugin>_<server>__<tool>`: here `mcp__plugin_easy-memory_easy-memory__memory_search` (measured with `--plugin-dir`), not `mcp__easy-memory__memory_search`. The old allow rule `mcp__easy-memory` does not match them.
- A plugin cannot set permissions (only `agent`, `subagentStatusLine` keys take effect).
- `${CLAUDE_PLUGIN_ROOT}` expands in hook commands and `.mcp.json`; it changes on every update — write no state there.
- `${CLAUDE_PLUGIN_DATA}` is deleted on uninstall — do not move the store there.
- The plugin root must NOT be the repo root: the repo's own `agents/` and `skills/` would load as plugin agents and skills.

---

## Acceptance Criteria

| # | Criterion (testable) | Traces to requirement |
|---|----------------------|-----------------------|
| 1 | `claude plugin validate .` (marketplace) and `claude plugin validate plugin` both exit 0 | "run as plugin" |
| 2 | `plugin/hooks/hooks.json` registers exactly the two events of `HOOK_EVENTS` (Stop → `hook-stop`, timeout 10; UserPromptSubmit → `hook-prompt`, timeout 5), each running `easy_memory.py` through `${CLAUDE_PLUGIN_ROOT}`; a test derives the expected entries from `HOOK_EVENTS` so they cannot drift | same hooks as today |
| 3 | `plugin/.mcp.json` registers server `easy-memory` running `easy_memory.py serve` through `${CLAUDE_PLUGIN_ROOT}` | same MCP server |
| 4 | The `easy_memory.py` the plugin runs is byte-identical to the repo root `easy_memory.py` (symlink if it survives `claude plugin install` into the cache, else a copy guarded by a test); one source of truth | no drift |
| 5 | Installed from the local marketplace into a throwaway `CLAUDE_CONFIG_DIR`, `claude plugin details easy-memory@easy-memory` lists 2 hooks and 1 MCP server, and `plugin/bin/easy-memory switch`/`report` run (the `bin/` wrapper is on the Bash PATH) | "do not care more about the way to setting up" |
| 6 | Double install: when a hook runs from the plugin (`CLAUDE_PLUGIN_ROOT` set) and user settings still hold our hooks (`_is_ours`), it exits 0 and saves/prints nothing — the old hooks keep working; exactly one note per turn | never runs twice |
| 7 | `python3 easy_memory.py install` prints one warning line and changes nothing when user settings enable `easy-memory@…` in `enabledPlugins`; with no plugin enabled it behaves exactly as before (existing install tests unchanged and passing) | old path keeps working |
| 8 | Live: in a throwaway folder, a headless `claude -p` run with the plugin saves a note under a throwaway `EASY_MEMORY_HOME` and the next prompt gets the index | same behaviour |
| 9 | `README.md` `## Use it` gains a plugin section: the two install commands, the allow rule for the new tool names (`mcp__plugin_easy-memory_easy-memory`), and "run `python3 easy_memory.py uninstall` (no `--purge`) first if you installed the old way — your notes stay" | user can follow it |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| # | Given (input/state) | Expect (output/behavior) | How it's checked |
|---|---------------------|--------------------------|------------------|
| 1 | plugin hooks.json and `HOOK_EVENTS` | same events, commands, timeouts | automated test |
| 2 | `CLAUDE_PLUGIN_ROOT` set + our hooks in settings | hook exits 0, no note written | automated test |
| 3 | `CLAUDE_PLUGIN_ROOT` set, no old hooks | hook saves the note as today | automated test |
| 4 | `enabledPlugins` has `easy-memory@easy-memory: true` | `install` warns, settings byte-identical | automated test |
| 5 | marketplace install in throwaway config | details: 2 hooks, 1 MCP | real run (paste output) |
| 6 | headless run with `--plugin-dir plugin` | note saved; next prompt gets index | real run (paste output) |

### Verification Command (exact, runnable)

```bash
python3 -m unittest discover -s tests && claude plugin validate . && claude plugin validate plugin
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-134.md` (review sections are never taken from the board).

---

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_HUN-134.md` (review sections are never taken from the board).

---

## Approach

1. Tests first (red): hooks.json matches `HOOK_EVENTS`; `.mcp.json`; double-install no-op; `install` warning; file identity.
2. Add `.claude-plugin/marketplace.json` (name `easy-memory`, one plugin, `source: "./plugin"`), `plugin/.claude-plugin/plugin.json` (name `easy-memory`, version matching the next release, author, license if the repo has one), `plugin/hooks/hooks.json`, `plugin/.mcp.json`, `plugin/bin/easy-memory`, and `plugin/easy_memory.py` (symlink first; check it survives install into the cache in a throwaway `CLAUDE_CONFIG_DIR`; else copy + identity test).
3. Add the plugin guard in the hook entry points and the `install` warning. Keep the change small and next to `_is_ours`.
4. README section. Real runs (throwaway config dirs only — never the user's real `~/.claude*`).

---

## Edge Case Checklist

- [ ] Plugin + old install both active: one note per turn, not two (AC 6)
- [ ] Both MCP servers active: tools appear twice under two names — README tells the user to uninstall the old way
- [ ] `python3` on PATH is older than the version the code needs: the hook must fail quietly (exit 0, logged), never block the user's prompt
- [ ] Hook runs inside a git worktree: repo identity resolves as today
- [ ] Plugin update changes `${CLAUDE_PLUGIN_ROOT}`: no state stored there; the background `build-weights` child uses `sys.executable` + `__file__` and still works
- [ ] Plugin uninstalled: notes in `~/.easy-memory/` stay
- [ ] Settings file missing or invalid JSON when the guard reads it: guard treats it as "no old hooks" and never crashes the hook

## Files to Change (Predicted)

| File | Change |
|------|--------|
| `.claude-plugin/marketplace.json` | new: marketplace with one plugin |
| `plugin/` | new: manifest, hooks.json, .mcp.json, bin wrapper, easy_memory.py link/copy |
| `easy_memory.py` | plugin guard in the hook path; `install` warning |
| `tests/test_plugin.py` | new |
| `README.md` | plugin section |

## Files Must NOT Touch

| File | Reason |
|------|--------|
| `site/` | out of scope |
| note store format (`FORMAT_VERSION`), ranking, MCP tool code | behaviour must not change |
| `agents/`, `skills/`, `.claude/` | the repo's own dev kit |
| user's real `~/.claude*` settings | real runs use throwaway config dirs |

## Test Plan

`python3 -m unittest discover -s tests` (full suite) plus the two `claude plugin validate` calls and the two real runs above.

## Completion Checklist

- [ ] Tests written first and failing, then passing
- [ ] Full suite passes, output pasted
- [ ] Real runs pasted (AC 5, AC 8)
- [ ] README section added
- [ ] Report: `Status: done` with commits, or `Status: blocked` + `Question:`
