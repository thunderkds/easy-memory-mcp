**Date**: 2026-10-30
**Complexity Level**: C2
**Risk Level**: High
**Priority**: P1
**Assigned agent**: backend-developer
**Agent guide**: `agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:

1. Read `PROJECT_SPEC.md` (Glossary has the v0.3 terms: Typed prompt, Event, Trigger, Turn, Touched file, Trash)
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/backend.md` in full
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/backend.md`
6. Read `PRD_v0.3.md` (Decision record row for M6) and `BRAINSTORMING_LOG_v0.3.md` (Edge Case Checklist, M6)
7. Read `easy_memory.py` sections: `MCP_TOOLS`, `MCP_HANDLERS`, `_note_path`, `valid_note_id`, `_tool_forget`, `read_notes`, `_private_dir`, `_atomic_write`, `redact_command`, `_redact_note`, `uninstall_command`, `_purge_target`

---

## Requirement (Pillar 1 — Adapt the requirement)

Verifier list V-R5 (2026-10-30): `memory_forget` was not exercised because it is irreversible (`_tool_forget` is `os.unlink`). Requirement: recoverable or previewable deletion. User chose trash + restore with 30-day retention (2026-10-30). Risk High: the task changes how user data is deleted.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> `memory_forget <id>` moves the note file to `<store>/trash/` (folder 0700, file keeps 0600) and sets its mtime to the move time. Trashed notes are not seen by search, list, read or the hook. New MCP tool `memory_restore <id>` moves it back. Trash files older than 30 days are deleted at the next `memory_forget`. The forget reply names `memory_restore` and the 30 days. `redact --apply` also scans `trash/`.

**Out of scope** (what this task explicitly does NOT do):

* Bulk forget (PRD v0.2 FR-005, Gate 1).
* A CLI restore command.
* Rewriting notes already saved (user, 2026-10-30: old notes are not rewritten).
* `report_command`, the switch, `INDEX_FLOOR` / `INDEX_MAX_NOTES` / `INDEX_MAX_CHARS` values, `experiments/`, `site/`.

**Requirement Refs**: `PRD_v0.3.md` M6; verifier V-R5; PRD v0.2 FR-005 (MCP forget stays single-id).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [X] Restated intent confirmed to match the user's request (by Supervisor, 2026-10-30; rules fixed with the user in requirement grilling)
- [X] Every Acceptance Criterion below traces to the requirement

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: none.

**Branch**: `v03-m6-trash` from `main`.

**Merge gate**: none: merge when Stage 4 and `/verify` pass (does not change which notes rank; user, 2026-10-30).

**Entry point**: `serve` → `_mcp_call_tool` → `_tool_forget` / `_tool_restore`.

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | forget then restore: the note file is back in `notes/` byte-identical, and `memory_read` shows it | V-R5 acceptance |
| 2 | forget of an unknown id: clear error `note not found: <id>`, nothing moved | V-R5 acceptance |
| 3 | after forget the note is absent from `memory_list`, `memory_search`, `memory_read` and the hook index | trash is out of ranking |
| 4 | restore of an id not in the trash, or one whose id already exists in `notes/`: error, nothing changed | grilling rule |
| 5 | a trash file with move time 31 days ago is deleted at the next forget; one at 29 days stays | 30-day retention |
| 6 | `memory_restore` is listed in `tools/list` with a schema like `memory_forget` | MCP |
| 7 | `redact` (dry run and `--apply`) covers `trash/` | secret must not survive a forget |
| 8 | `trash/` is 0700, a trashed file 0600; `uninstall --purge` removes it | NFR-003 |
| 9 | README: forget is recoverable for 30 days with `memory_restore` | V-R5 "stated retention" |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | note in store; MCP `memory_forget` then `memory_restore` | file restored, bytes equal | automated test (MCP over stdio subprocess) |
| 2 | `memory_forget` unknown id | `isError`, message names the id | automated test |
| 3 | trash file aged with `os.utime` | purged at next forget | automated test |
| 4 | secret in a trashed note | `redact --apply` rewrites it | automated test |

### Verification Command (exact, runnable)

```bash
python3 -m unittest tests.test_v03_m6_trash && python3 -m unittest discover -s tests
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-135.md` (review sections are never taken from the board).

## Approach

1. Tests first (red) in `tests/test_v03_m6_trash.py`.
2. `_tool_forget`: validate id, `_private_dir(trash)`, `os.replace(note, trash/name)`, `os.utime(now)`, then purge files older than 30 days (`TRASH_KEEP_DAYS = 30`).
3. `_tool_restore`: reverse move; refuse an existing target (`os.link` + unlink, or check then `os.replace` — no overwrite).
4. Add the tool to `MCP_TOOLS` / `MCP_HANDLERS`; `redact` iterates `notes/` and `trash/`. 5. README.

---

## Edge Case Checklist

- [ ] `os.replace` keeps mtime: set it to the move time, or the purge counts from save time
- [ ] Restore must never overwrite an existing note (race with a new note of the same id is near-impossible, but the check is required)
- [ ] Purge errors (permission) are ignored and logged; forget still succeeds
- [ ] Id validation as `_note_path` (no path traversal into or out of `trash/`)
- [ ] Old MCP clients that do not know `memory_restore` keep working
- [ ] `plugin/easy_memory.py` is byte-identical to `easy_memory.py` in the same commit (`tests/test_plugin.py`)
- [ ] Every hook path still exits 0 and prints nothing on error (NFR-004)

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| `easy_memory.py` | `_tool_forget`, new `_tool_restore`, `MCP_TOOLS`, `MCP_HANDLERS`, `redact_command`, `TRASH_KEEP_DAYS` |
| `tests/test_v03_m6_trash.py` | new |
| `README.md` | forget / restore |
| `plugin/easy_memory.py` | copy of `easy_memory.py` |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| `experiments/`, `site/`, `docs/RELEASE_v0.1.0.md` | out of scope |
| `report_command`, switch code, `INDEX_*` values | measurement code (PRD v0.2 Gate 2a) |
| any `~/.easy-memory/` store, user's real `~/.claude*` | tests use a throwaway `EASY_MEMORY_HOME` / config dir |
| `agents/`, `skills/`, `.claude/` | the repo's own dev kit |

## Test Plan

`python3 -m unittest tests.test_v03_m6_trash`, plus `tests/test_t008_mcp.py` and `tests/test_t010_redact.py` unchanged. Then `python3 -m unittest discover -s tests` (full suite, 434 tests at `cb876eb`).

## Completion Checklist

- [ ] Tests written first and failing, then passing
- [ ] Full suite passes, output pasted
- [ ] README updated where an AC says so
- [ ] Not merged into `main` unless the Merge gate above is open
- [ ] Report: `Status: done` with commits, or `Status: blocked` + `Question:`

## Questions Log

* 2026-10-30 DEBATE Should redact (dry run and --apply) also cover <store>/trash/ once memory_forget moves notes there? → Yes, redact scans and rewrites trash/ like notes/ (rule 1: necessary — tasks/TASK_GUIDE_HUN-135.md:73 "| 7 | `redact` (dry run and `--apply`) covers `trash/` | secret must not survive a forget |"). Advocate 1: yes, rewrite trash (medium); Advocate 2: leave trash alone (low); Advocate 3: list trash in dry run, apply notes only (low). Decided by the Supervisor in auto mode — please review. ⚠ decided for you — please review (Linear comment on HUN-135)