**Date**: 2026-10-30
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P2
**Assigned agent**: qa-expert
**Agent guide**: `agents/qa.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:

1. Read `PROJECT_SPEC.md` (Glossary has the v0.3 terms: Typed prompt, Event, Trigger, Turn, Touched file, Trash)
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/qa.md` in full
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/qa.md`
6. Read `PRD_v0.3.md` (Decision record row for M7) and `BRAINSTORMING_LOG_v0.3.md` (Edge Case Checklist, M7)
7. Read `easy_memory.py` sections: `hook_stop`, `save_stop_note`, `write_note`, `_atomic_write`, `serve_command`, `_tool_search`, `_index_lines`

---

## Requirement (Pillar 1 — Adapt the requirement)

Kit list K-R4 (2026-10-30): in a plugin-only run (T217 record, 10:18Z) a note did not show 3 s after the turn ended; it appeared during the next run. Requirement: find the cause and make save → search consistent, or document the delay. Code check 2026-10-30: the Stop hook writes synchronously (temp file + rename) and search reads note files directly, with no index; `~/.easy-memory/hook.log` does not exist.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> A scripted test runs `easy_memory.py hook-stop` as a subprocess with a fixture Stop input, and as soon as it returns runs `memory_search` through `easy_memory.py serve` (subprocess, JSON-RPC over stdio) and finds the note within 1 s. If it passes, the delay is outside easy-memory's write path: record the likely causes (Claude Code firing the Stop hook late, a query under the 0.12 floor, the plugin deferring to old hooks) in the README. If it fails, STOP and report — the fix becomes a new task.

**Out of scope** (what this task explicitly does NOT do):

* Any change to `easy_memory.py` (unless the test fails — then report, do not fix).
* Rewriting notes already saved (user, 2026-10-30: old notes are not rewritten).
* `report_command`, the switch, `INDEX_FLOOR` / `INDEX_MAX_NOTES` / `INDEX_MAX_CHARS` values, `experiments/`, `site/`.

**Requirement Refs**: `PRD_v0.3.md` M7; kit K-R4.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [X] Restated intent confirmed to match the user's request (by Supervisor, 2026-10-30; rules fixed with the user in requirement grilling)
- [X] Every Acceptance Criterion below traces to the requirement

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: none.

**Branch**: `v03-m7-save-search` from `main`.

**Merge gate**: none: merge when Stage 4 and `/verify` pass (test + README only).

**Entry point**: `hook-stop` subprocess, then `serve` subprocess.

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | The test saves a turn via `hook-stop` and `memory_search` finds its id within 1 s of the hook process exiting; timing asserted | K-R4 acceptance |
| 2 | The same with `CLAUDE_PLUGIN_ROOT` set to `plugin/` (plugin path, no old hooks in a throwaway settings file) | "plugin-only run" |
| 3 | README Known limits names the result: either "saved notes are searchable at once" with the likely outside causes, or the measured delay | K-R4 "or document" |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | throwaway `EASY_MEMORY_HOME`, fixture transcript + Stop input | note id in the search reply, elapsed < 1 s | automated test |
| 2 | same with plugin env | same | automated test |

### Verification Command (exact, runnable)

```bash
python3 -m unittest tests.test_v03_m7_save_search && python3 -m unittest discover -s tests
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-136.md` (review sections are never taken from the board).

## Approach

1. Write `tests/test_v03_m7_save_search.py` (reuse fixtures/helpers of `tests/test_t009_smoke.py` and `tests/test_t008_mcp.py`).
2. Query with distinctive words from the fixture answer, and a weights file present, so the floor is not the reason for a miss.
3. README line.

---

## Edge Case Checklist

- [ ] The switch: `memory_search` does not depend on it, but set `on` in the store config to match a live run
- [ ] Measure from hook exit, not from test start
- [ ] No weights file: search uses `n = 0` plain match — test both
- [ ] `plugin/easy_memory.py` is byte-identical to `easy_memory.py` in the same commit (`tests/test_plugin.py`)
- [ ] Every hook path still exits 0 and prints nothing on error (NFR-004)

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| `tests/test_v03_m7_save_search.py` | new |
| `README.md` | Known limits line |
| `plugin/easy_memory.py` | copy of `easy_memory.py` |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| `experiments/`, `site/`, `docs/RELEASE_v0.1.0.md` | out of scope |
| `report_command`, switch code, `INDEX_*` values | measurement code (PRD v0.2 Gate 2a) |
| any `~/.easy-memory/` store, user's real `~/.claude*` | tests use a throwaway `EASY_MEMORY_HOME` / config dir |
| `agents/`, `skills/`, `.claude/` | the repo's own dev kit |

## Test Plan

`python3 -m unittest tests.test_v03_m7_save_search`. Then `python3 -m unittest discover -s tests` (full suite, 434 tests at `cb876eb`).

## Completion Checklist

- [ ] Tests written first and failing, then passing
- [ ] Full suite passes, output pasted
- [ ] README updated where an AC says so
- [ ] Not merged into `main` unless the Merge gate above is open
- [ ] Report: `Status: done` with commits, or `Status: blocked` + `Question:`