**Date**: 2026-10-28
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
4. Read `agents/backend.md`
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth) from the Complexity matrix in your role guide (`agents/backend.md`)
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md` if it exists (it does not yet: the repo has only `experiments/` and, from HUN-74 on, `easy_memory.py`)
7. Also read `PRD.md` (the Requirement Refs below) and `BRAINSTORMING_LOG.md` (edge cases E1 to E12)

---

## Requirement (Pillar 1 — Adapt the requirement)

A report command must read Claude Code's own session logs and compare sessions with memory on against sessions with it off, per repo. It shows session count, median tokens (input + output) per session, median turns, and how often a listed note was opened.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> After a few weeks of normal use the user can read one table per repo and see whether memory saved tokens, with an honest warning when there is too little data.

**Out of scope** (what this task explicitly does NOT do):

* Charts, CSV, HTML.
* Statistical tests.
* Anything outside the CLI.

**Requirement Refs** (FR/NFR/US IDs from `PRD.md` this task satisfies):

* US-006
* FR-007: per repo, on vs off: sessions, median tokens, median turns, note-open rate
* KPI table in PRD: median tokens, index usefulness
* G4: a session takes the state logged at its first prompt

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary (`grill-with-docs` run if terminology was fuzzy)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [ ] All Requirement Refs exist in `PRD.md` and are fully covered by the Acceptance Criteria above

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: HUN-78 — prompt log with switch state must exist

**Entry point**: `report` subcommand of `easy_memory.py`

---

## Acceptance Criteria

> Each criterion must trace back to the Requirement above (Pillar 1 → Pillar 3 link).

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | `report` finds Claude session logs for the repo under `$CLAUDE_CONFIG_DIR/projects/` (default `~/.claude/projects/`) and joins them to `prompts.log` by session id. | FR-007 |
| 2 | Each session is placed in the on or off group by the effective state logged at its first prompt; sessions with no log line are counted as 'no data' and excluded. | G4 |
| 3 | For each group it prints: session count, median tokens, median turns, and (on group only) the share of sessions that got an index and then opened a listed note (a `memory_read` call or a Read of a listed note path). | FR-007 |
| 4 | Token definition: read how `experiments/*/harness.py` counted tokens, report that as the headline, and print the 'input + output' and 'including cache' figures as separate columns. State in the output which one is the headline. | FR-007, PRD ambiguity |
| 5 | With fewer than 10 sessions in either group it prints 'too few sessions to compare' next to the numbers. | honest metric |
| 6 | No data, a missing log folder or malformed JSONL lines: exits 0 with a plain message; bad lines are skipped. | NFR-004 |
| 7 | It prints the store size (notes count and bytes) for the repo. | A4 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The reviewer fills **Evidence** at Stage 4/5 in `tasks/TASK_REVIEW_T007.md`, copied from
> `templates/TASK_REVIEW_template.md`. A task is **not done** until every row has evidence.
> The implementing agent must NOT be the sole author of its own acceptance test: the Supervisor
> signs off the Success Criteria below as the oracle.

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | Fixture with 12 on-sessions and 12 off-sessions | two groups with medians and counts | unittest |
| 2 | Fixture with 3 sessions per group | 'too few sessions' warning | unittest |
| 3 | Log folder missing | exit 0 and a message | unittest |

### Verification Command (exact, runnable)

```bash
python3 -m unittest discover -s tests -p 'test_t007*.py' -v
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-80.md` (review sections are never taken from the board).

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_HUN-80.md` (review sections are never taken from the board).

## Approach

**Pattern reference**: `experiments/01-memory-vs-cold/harness.py` and `grade.py` for how tokens were counted; no prior art for reading Claude's JSONL logs.

**Vital slice**: One table per repo: count, median tokens, median turns, note-open rate.
**Cut list**: Charts and exports.; Confidence intervals.; Per-day breakdown.

Study one real session log to learn the line shape (`usage` fields on assistant entries, tool_use entries). Build SYNTHETIC fixtures; never commit real logs. Median via `statistics.median`.

**Conventions**: Python 3, standard library only (NFR-005). Tests use `unittest` (pytest is not guaranteed). Follow `docs/claude-md/code-naming-conventions.md`. Tests never touch the real home folder, the real Claude settings, or the real `~/.easy-memory` (use temp dirs and `EASY_MEMORY_HOME` / `CLAUDE_CONFIG_DIR`). Private client repos (Project B, Project A) are read-only benchmark targets: record numbers only, never quote or commit their source.

---

## Edge Case Checklist

- [ ] Resumed sessions that append to an old log file.
- [ ] Sub-agent (sidechain) entries: decide, document, and count them with their parent.
- [ ] Sessions in a worktree map to the main repo's store.
- [ ] Logs with missing `usage`: skip the entry, not the session.
- [ ] Large log folders: stream line by line.

---

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| easy_memory.py | add `report` and log readers |
| tests/test_t007_report.py | new |
| tests/fixtures/ | synthetic Claude logs |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| The real `~/.claude*/projects/**` | read-only at runtime; tests use fixtures |
| experiments/\*\* | read-only evidence |

---

## Test Plan

Unit tests on fixtures. One manual run on the user's real logs, output reviewed by the Supervisor (numbers only).

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (if Medium/High risk)
- [ ] Lint passes (`python3 -m py_compile easy_memory.py` at minimum)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T007.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working by running it
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review