**Date**: 2026-10-28
**Complexity Level**: C1
**Risk Level**: Low
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

A per-repo switch must have three states: on, off, and auto (the default), which alternates on and off by calendar day. When off, saving continues but nothing is injected. Each prompt's state must be logged with its session id.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> The user can turn memory on or off for one repo, and by default gets a fair on/off comparison without effort; every prompt leaves a log line the report can read.

**Out of scope** (what this task explicitly does NOT do):

* The report (HUN-80).
* A global switch for all repos.
* Any UI beyond the CLI.

**Requirement Refs** (FR/NFR/US IDs from `PRD.md` this task satisfies):

* US-006
* FR-006: on / off / auto; off keeps saving; log each prompt's state with session id
* A2: auto is the default (confirmed 2026-10-28)
* G4: even day number = on, odd = off, local time

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary (`grill-with-docs` run if terminology was fuzzy)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [ ] All Requirement Refs exist in `PRD.md` and are fully covered by the Acceptance Criteria above

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: HUN-77 — hook-prompt must exist

**Entry point**: `switch` subcommand of `easy_memory.py`

---

## Acceptance Criteria

> Each criterion must trace back to the Requirement above (Pillar 1 → Pillar 3 link).

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | `easy_memory.py switch on|off|auto` stores the state for the current repo in `<store>/config.json` (0600); `switch` with no argument prints the state and what it means today. | FR-006 |
| 2 | With no config the state is `auto`. | A2 |
| 3 | `auto` is on when the local calendar date's ordinal (days since 1970-01-01) is even and off when odd; the date is injectable in tests. | G4 |
| 4 | When the effective state is off, `hook-prompt` prints nothing and `hook-stop` still saves. | FR-006 |
| 5 | Every `hook-prompt` run appends one JSON line to `<store>/prompts.log` (0600): time, session_id, configured state, effective state, whether an index was injected. | FR-006 |
| 6 | A write failure on the log does not change the hook's output or exit code. | NFR-004 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The reviewer fills **Evidence** at Stage 4/5 in `tasks/TASK_REVIEW_T005.md`, copied from
> `templates/TASK_REVIEW_template.md`. A task is **not done** until every row has evidence.
> The implementing agent must NOT be the sole author of its own acceptance test: the Supervisor
> signs off the Success Criteria below as the oracle.

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | State `auto`, date ordinal even | effective on, index injected if notes match | unittest |
| 2 | State `auto`, date ordinal odd | effective off, empty stdout, log line with `effective: off` | unittest |
| 3 | State `off`, a Stop event | note is still saved | unittest |

### Verification Command (exact, runnable)

```bash
python3 -m unittest discover -s tests -p 'test_t005*.py' -v
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-78.md` (review sections are never taken from the board).

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_HUN-78.md` (review sections are never taken from the board).

## Approach

**Pattern reference**: None — no comparable prior art in this repo (new config handling); keep it a flat JSON file like the notes.

**Vital slice**: Switch state + effective-state function + prompt log line.
**Cut list**: Per-day report columns.; A global default.

`effective_state(config, today)` is a pure function. `hook-prompt` calls it first; if off it logs and exits without scoring (also faster). The log line is written last, in a try/except.

**Conventions**: Python 3, standard library only (NFR-005). Tests use `unittest` (pytest is not guaranteed). Follow `docs/claude-md/code-naming-conventions.md`. Tests never touch the real home folder, the real Claude settings, or the real `~/.easy-memory` (use temp dirs and `EASY_MEMORY_HOME` / `CLAUDE_CONFIG_DIR`). Private client repos (orderly, tapchat) are read-only benchmark targets: record numbers only, never quote or commit their source.

---

## Edge Case Checklist

- [ ] Session crosses midnight: each prompt logs its own effective state; the report picks the first (G4).
- [ ] Unknown value in config.json: treat as `auto` and log.
- [ ] Time zone change: local date is taken at prompt time.
- [ ] Worktrees share the config because they share the store.

---

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| easy_memory.py | add `switch`, `effective_state`, prompt log |
| tests/test_t005_switch.py | new |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| experiments/\*\* | read-only evidence |

---

## Test Plan

Unit tests with an injected date.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (if Medium/High risk)
- [ ] Lint passes (`python3 -m py_compile easy_memory.py` at minimum)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T005.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working by running it
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review