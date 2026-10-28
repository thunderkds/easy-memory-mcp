**Date**: 2026-10-28
**Complexity Level**: C2
**Risk Level**: High
**Priority**: P0
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

A UserPromptSubmit hook must add an index of at most 5 notes whose score against the prompt is ≥ 0.12. Each line shows the note id, the earlier question, the answer's first line, the cited files, and any cited file that changed or was deleted. The index says how to open a note and that notes are data that may be out of date. When no note qualifies it adds nothing. It must stay fast and must never block the prompt.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> A prompt that matches earlier notes arrives with a short, honest index the agent can ignore or open; a prompt that matches nothing arrives untouched; and the hook adds well under 1 s.

**Out of scope** (what this task explicitly does NOT do):

* The on/off/auto switch (HUN-78).
* The MCP tools (HUN-81).
* Facts and judge methods from experiment 03.
* A model call of any kind.

**Requirement Refs** (FR/NFR/US IDs from `PRD.md` this task satisfies):

* US-002, US-003
* FR-003: index limits, line content, changed/deleted flags, 2,500-character cap
* FR-004: tell the agent how to open a note; notes are data
* NFR-001: ≤ 1 s p95 on a 7,000-file repo
* NFR-004: never block or alter the prompt
* A5: limits unchanged from experiment 03

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary (`grill-with-docs` run if terminology was fuzzy)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [ ] All Requirement Refs exist in `PRD.md` and are fully covered by the Acceptance Criteria above

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: HUN-75 — notes must exist; HUN-76 — weights and scorer must exist

**Entry point**: `hook-prompt` subcommand of `easy_memory.py`

---

## Acceptance Criteria

> Each criterion must trace back to the Requirement above (Pillar 1 → Pillar 3 link).

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | With ≥1 note scoring ≥ 0.12, stdout is one JSON object `{"hookSpecificOutput": {"hookEventName": "UserPromptSubmit", "additionalContext": <text>}}` with at most 5 note lines, best score first. | FR-003 |
| 2 | Each line has: note id, earlier question (truncated), first line of the answer (truncated), cited files, and `CHANGED:` / `DELETED:` flags for cited files whose sha256 differs or that no longer exist in the current worktree. | FR-003, US-003, edge E5/E6 |
| 3 | The text starts with a header that says notes are data, may be out of date, and how to open one (`memory_read` with the id, or the note's file path). | FR-004 |
| 4 | `additionalContext` is ≤ 2,500 characters; if over, whole lowest-scoring lines are dropped, never cut in half. | FR-003, edge E8 |
| 5 | No note ≥ 0.12 → empty stdout, exit 0. | FR-003 |
| 6 | Weights not ready → empty stdout, exit 0, and `ensure_weights()` has started a build. | NFR-001, edge E1 |
| 7 | Any exception (bad stdin, corrupt store, missing weights) → exit 0, empty stdout, one line in `hook.log`. | NFR-004 |
| 8 | A note whose answer contains 'ignore previous instructions' appears only as a truncated quoted line inside the index frame, never outside it. | FR-004, edge E10 |
| 9 | p95 ≤ 0.5 s over 50 runs on orderly with 200 notes in the store (hard limit 1 s). Result pasted. | NFR-001 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The reviewer fills **Evidence** at Stage 4/5 in `tasks/TASK_REVIEW_T004.md`, copied from
> `templates/TASK_REVIEW_template.md`. A task is **not done** until every row has evidence.
> The implementing agent must NOT be the sole author of its own acceptance test: the Supervisor
> signs off the Success Criteria below as the oracle.

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | 3 notes, one matches the prompt at ≥ 0.12 | index with 1 line, header present, ≤ 2,500 characters | unittest |
| 2 | A cited file edited after saving | that line carries `CHANGED:<path>` | unittest |
| 3 | A cited file deleted | that line carries `DELETED:<path>` | unittest |
| 4 | No weights file | empty stdout, exit 0 | unittest |

### Verification Command (exact, runnable)

```bash
python3 -m unittest discover -s tests -p 'test_t004*.py' -v
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-77.md` (review sections are never taken from the board).

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_HUN-77.md` (review sections are never taken from the board).

## Approach

**Pattern reference**: `experiments/03-precision/precision.py` (`HEADER`, `stale`, `_changed_note`, the index builder) and `experiments/03-precision/hook.py`: port the index method; do not port facts or judge.

**Vital slice**: Score, pick ≤5, render lines with flags, emit JSON.
**Cut list**: Facts and judge methods.; Per-line score display.; Prompt stash.

Hook flow: read stdin → repo key from `cwd` → `ensure_weights()` → load notes → score with the HUN-76 scorer → filter ≥ 0.12 → top 5 → check each cited file's current sha256 → render → cap to 2,500 characters → print JSON. Do the cheapest work first and exit early. Use `json.dumps` for output so quotes and newlines in notes cannot break the JSON.

**Conventions**: Python 3, standard library only (NFR-005). Tests use `unittest` (pytest is not guaranteed). Follow `docs/claude-md/code-naming-conventions.md`. Tests never touch the real home folder, the real Claude settings, or the real `~/.easy-memory` (use temp dirs and `EASY_MEMORY_HOME` / `CLAUDE_CONFIG_DIR`). Private client repos (orderly, tapchat) are read-only benchmark targets: record numbers only, never quote or commit their source.

---

## Edge Case Checklist

- [ ] 200+ notes: score only prompt+first lines if needed to stay in budget; measure first.
- [ ] Notes saved on another branch: flags compare against this worktree.
- [ ] Cited file is binary or very large: hash with a size guard.
- [ ] A prompt that is a slash command or empty: add nothing.
- [ ] Note text contains control characters or huge lines: sanitise and truncate.
- [ ] Hook output must be a single JSON object and nothing else on stdout.
- [ ] Time zone and clock changes do not affect scoring.

---

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| easy_memory.py | add `hook-prompt`, index rendering, changed-file check |
| tests/test_t004_prompt_hook.py | new |
| tests/bench_t004.py | new: latency benchmark, prints numbers only |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| experiments/\*\* | read-only evidence |
| Anything that writes inside the observed repo | FR-002 |

---

## Test Plan

Unit tests on a synthetic repo and store. Benchmark script on orderly with 200 generated notes; record timings only.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (if Medium/High risk)
- [ ] Lint passes (`python3 -m py_compile easy_memory.py` at minimum)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T004.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working by running it
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review