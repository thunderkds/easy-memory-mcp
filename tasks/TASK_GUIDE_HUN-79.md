**Date**: 2026-10-28
**Complexity Level**: C2
**Risk Level**: High
**Priority**: P1
**Assigned agent**: backend-developer
**Agent guide**: `agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/backend.md`
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth) from the Complexity matrix in your role guide (`agents/backend.md`)
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md` if it exists (it does not yet: the repo has only `experiments/` and, from HUN-74 on, `easy_memory.py`)
7. Also read `PRD.md` (the Requirement Refs below) and `BRAINSTORMING_LOG.md` (edge cases E1 to E12)

---

## Requirement (Pillar 1 — Adapt the requirement)

One install command must register both hooks in the user-level Claude Code settings for all repos, and an uninstall command must remove them cleanly. The installer edits the user's real settings, so it needs a backup and a dry run.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> The user runs one command once and memory works in every repo; running uninstall returns the settings file to exactly what it was apart from the user's own later edits.

**Out of scope** (what this task explicitly does NOT do):

* MCP server registration and its allow rule (HUN-81).
* Per-repo install.
* Editing project-level settings.

**Requirement Refs** (FR/NFR/US IDs from `PRD.md` this task satisfies):

* US-007
* FR-008: one install command, one uninstall command, user-level, all repos
* NFR-004: a broken hook must not break Claude Code
* NFR-003: private store
* A3: permission-prompt-free opening (handled in HUN-81)

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary (`grill-with-docs` run if terminology was fuzzy)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [ ] All Requirement Refs exist in `PRD.md` and are fully covered by the Acceptance Criteria above

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: HUN-75 — Stop hook; HUN-77 — prompt hook

**Entry point**: `install` and `uninstall` subcommands of `easy_memory.py`

---

## Acceptance Criteria

> Each criterion must trace back to the Requirement above (Pillar 1 → Pillar 3 link).

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | `install --dry-run` prints the exact changes (a unified diff of the settings JSON) and writes nothing, not even a backup. | FR-008 |
| 2 | `install` first copies the settings file to `<file>.easy-memory.bak.<timestamp>`, then adds one Stop hook and one UserPromptSubmit hook whose command is `<abs python3> <abs path>/easy_memory.py hook-stop|hook-prompt`, with a `timeout` (Stop 10 s, UserPromptSubmit 5 s). | FR-008 |
| 3 | The settings dir is `$CLAUDE_CONFIG_DIR` if set, else `~/.claude`. | FR-008, edge |
| 4 | Running `install` twice leaves the file unchanged the second time. | FR-008 |
| 5 | All keys and all other hooks in the file are preserved (JSON-equal apart from our two entries). | FR-008 |
| 6 | If the settings file is not valid JSON, `install` aborts with a message and writes nothing. | NFR-004 |
| 7 | `uninstall` removes exactly the entries whose command contains `easy_memory.py`, keeps everything else, and leaves `~/.easy-memory/` data alone; `uninstall --purge` also deletes the store after printing its size. | FR-008, US-005 |
| 8 | After `install` then `uninstall` on a fixture file, the JSON equals the original. | FR-008 |
| 9 | Tests run only against a temp `CLAUDE_CONFIG_DIR`; no test reads or writes the real `~/.claude*`. | safety |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The reviewer fills **Evidence** at Stage 4/5 in `tasks/TASK_REVIEW_T006.md`, copied from
> `templates/TASK_REVIEW_template.md`. A task is **not done** until every row has evidence.
> The implementing agent must NOT be the sole author of its own acceptance test: the Supervisor
> signs off the Success Criteria below as the oracle.

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | Fixture settings with another Stop hook | after install both hooks present; after uninstall only the other hook remains | unittest |
| 2 | Invalid JSON settings file | exit non-zero, file untouched, no backup | unittest |
| 3 | `--dry-run` | diff printed, directory listing unchanged | unittest |

### Verification Command (exact, runnable)

```bash
python3 -m unittest discover -s tests -p 'test_t006*.py' -v
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-79.md` (review sections are never taken from the board).

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_HUN-79.md` (review sections are never taken from the board).

## Approach

**Pattern reference**: None — no comparable prior art in this repo. Hook entry shape: [https://code.claude.com/docs/en/hooks](<https://code.claude.com/docs/en/hooks>) (hooks → event → matcher group → `{type: command, command, timeout}`); read the current page before writing.

**Vital slice**: Add and remove two hook entries safely, with dry run and backup.
**Cut list**: Project-level install.; Interactive prompts.; Auto-update of the module path.

Load JSON, deep-copy, add entries under `hooks.Stop` and `hooks.UserPromptSubmit` (create lists if missing), write to temp then rename, keep file mode. Identify our entries by the `easy_memory.py` substring. Print a diff with `difflib`. This machine has both `~/.claude` and `~/.claude-personal`: honor `CLAUDE_CONFIG_DIR` and print which file was changed.

**Conventions**: Python 3, standard library only (NFR-005). Tests use `unittest` (pytest is not guaranteed). Follow `docs/claude-md/code-naming-conventions.md`. Tests never touch the real home folder, the real Claude settings, or the real `~/.easy-memory` (use temp dirs and `EASY_MEMORY_HOME` / `CLAUDE_CONFIG_DIR`). Private client repos (Project B, Project A) are read-only benchmark targets: record numbers only, never quote or commit their source.

---

## Edge Case Checklist

- [ ] Settings file missing: create it with only our entries (after backup of nothing).
- [ ] Settings has `hooks` as unexpected type: abort without writing.
- [ ] Module path contains spaces: quote the command.
- [ ] Python path differs between machines: use `sys.executable` at install time and print it.
- [ ] User already has a hook on the same event: append, never replace.
- [ ] Unwritable settings dir: clear error, nothing partial.

---

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| easy_memory.py | add `install`, `uninstall`, settings helpers |
| tests/test_t006_install.py | new |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| The real `~/.claude/settings.json` and `~/.claude-personal/settings.json` | tests never touch them |
| experiments/\*\* | read-only evidence |

---

## Test Plan

Unit tests with temp config dirs and fixtures. HITL step: the Supervisor shows the user the real `install --dry-run` diff; the user approves before the first real install.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (if Medium/High risk)
- [ ] Lint passes (`python3 -m py_compile easy_memory.py` at minimum)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T006.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working by running it
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review