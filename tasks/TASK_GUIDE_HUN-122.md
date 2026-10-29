**Date**: 2026-10-29
**Complexity Level**: C1
**Risk Level**: Medium
**Priority**: P0
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
6. Read `PRD_v0.2.md` "Release gates" (Sample bar row) and open item O5, and `PRD.md` FR-007 (the report)

---

## Requirement (Pillar 1 — Adapt the requirement)

`report` groups sessions by the `effective` state of their first `prompts.log` line (`report_command`, `_first_prompt_lines` in `easy_memory.py`). Sessions where the user forced the switch (`configured` is `on` or `off`) enter the on/off comparison, so they pollute it. The sample bar ("10 sessions with `configured == auto` in each group") cannot be read from the report today. Count only sessions whose first `prompts.log` line has `configured == "auto"` in the on/off groups, and show how many were left out.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> The on/off table and its verdict use only sessions where the day decided the state (auto switch). Forced sessions are still counted and shown on one line, but never enter a group. The "too few sessions" rule then measures the sample bar directly.

**Out of scope** (what this task explicitly does NOT do):

* Any hook, ranking, store or switch change (`hook-prompt`, `hook-stop`, `switch`), and any change to what `prompts.log` records.
* A flag to include forced sessions.
* Choosing the Gate 2a metric (open item O3) or changing the verdict line's metric.
* A window-start cut-off by time.

**Requirement Refs**:

* PRD_v0.2 open item O5; Sample bar row of "Release gates"
* PRD.md FR-007 (report: on vs off from Claude session logs)

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [ ] All Requirement Refs exist in the PRDs and are fully covered by the Acceptance Criteria

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: None — can start immediately (Gate 0 is merged).

**Entry point**: `python3 easy_memory.py report [--repo PATH]` → `report_command`

**Build in a worktree.** The live hooks run from the main checkout (PRD_v0.2 A9). `report` is not a hook, but merge only after review.

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | A session whose first `prompts.log` line has `configured: "auto"` is counted in the group of its `effective` state, as today. | O5 |
| 2 | A session whose first line has `configured` `on` or `off` (or missing, or any other value) is in no group: not in the table, not in the medians, not in the "note opened" rate, not in the verdict. | O5 |
| 3 | The grouping still uses the session's FIRST valid line: a session that starts forced and later becomes auto stays excluded, and one that starts auto and is later forced stays included. | O5, G4 rule |
| 4 | The report prints one extra count, for example `forced switch: N (left out of the comparison)`. `sessions logged` still counts every session. | O5 |
| 5 | `no data` (log file with no `prompts.log` line) does not change: a forced session is still "seen" and is not counted as no data. | FR-007 |
| 6 | The "too few sessions" check and the verdict use only the auto groups, so 10 auto sessions per group is the sample bar. | Sample bar |
| 7 | `report` stays read-only, and all existing tests still pass (adjust a test only where it asserted forced sessions inside a group; say which). | FR-007 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The reviewer fills **Evidence** at Stage 4/5 in `tasks/TASK_REVIEW_<ID>.md`, copied from
> `templates/TASK_REVIEW_template.md`. A task is **not done** until every row has evidence.

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | prompts.log with 2 auto-on, 3 auto-off, 4 forced-on, 1 forced-off sessions, each with a Claude log | table shows on 2, off 3; `forced switch: 5` | unittest |
| 2 | a session that starts `configured: on` then has auto lines | excluded | unittest |
| 3 | 10 auto-on and 10 auto-off sessions plus 5 forced-on | no "too few" note; verdict line printed from the auto groups only | unittest |

### Verification Command (exact, runnable)

```bash
python3 -m unittest discover -s tests -v 2>&1 | tail -5
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-122.md` (review sections are never taken from the board).

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_HUN-122.md` (review sections are never taken from the board).

## Approach

**Pattern reference**: `tests/test_t007_report.py` (`log_prompt(..., configured="auto")` helper already exists).

**Vital slice**: in `report_command`, skip sessions whose first line's `configured` is not `"auto"`, count them, and print the count.
**Cut list**: An `--include-forced` flag; per-reason breakdown of excluded sessions; a time-window filter.

Keep `_first_prompt_lines` returning every session so `no data` stays correct; filter in `report_command`. Update the `report_command` docstring and the explanatory print line if it describes grouping.

**Conventions**: Python 3, standard library only. `unittest`. Tests use temp `EASY_MEMORY_HOME` and `CLAUDE_CONFIG_DIR`; never read the real `~/.easy-memory` or `~/.claude`.

---

## Edge Case Checklist

- [ ] Every session is forced: the table shows 0/0 and the forced count; no crash, no verdict.
- [ ] A forced session has no Claude log: it counts as forced, not as "no Claude log" (state which; keep the counts disjoint and documented).
- [ ] `configured` has an unknown value or wrong type: treated as not auto.

---

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| easy_memory.py | `report_command` only |
| tests/test_t007_report.py | new tests; adjust any test that relied on forced sessions in a group |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| hook, switch, store, scorer code in easy_memory.py | measurement must not change |
| experiments/\*\* | read-only evidence |

---

## Test Plan

Unit tests on synthetic `prompts.log` and Claude session logs in temp dirs, then the full suite.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Lint passes (`python3 -m py_compile easy_memory.py`)
- [ ] Tests written AND pass — output pasted into the TASK_REVIEW Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review