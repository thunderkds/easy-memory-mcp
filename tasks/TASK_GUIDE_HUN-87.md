**Date**: 2026-10-29
**Complexity Level**: C1
**Risk Level**: Medium
**Priority**: P0
**Assigned agent**: qa-expert
**Agent guide**: `agents/qa.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/qa.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/qa.md`
6. Read `PRD_v0.2.md` "Release gates" (Gate 0 row) and `RUNBOOK.md`

---

## Requirement (Pillar 1 — Adapt the requirement)

Check every Gate 0 pass condition in `PRD_v0.2.md` on the integrated worktree branch, as an oracle separate from the implementer, before the user merges the redaction release into the live checkout.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> One report shows each Gate 0 condition with pasted evidence: suite green on an odd and an even day with the same names and skips, one redaction fixture per pattern, a byte-identical no-secret fixture, the 1 MB timing, the benchmark p95 before and after, and a smoke run that adds no `hook.log` line. The redaction release date goes into `RUNBOOK.md` when the user merges.

**Out of scope** (what this task explicitly does NOT do):

* Merging (the user merges; the merge changes the live hooks).
* Any code change to `easy_memory.py`. A failed check goes back to the implementer.

**Requirement Refs**:

* PRD_v0.2 Gate 0 row, NFR-008, A10 (release date recorded)

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [ ] All Requirement Refs exist in `PRD_v0.2.md` and are fully covered by the Acceptance Criteria

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: "Stop hook redacts secrets before a note is saved" and "redact command rewrites notes already saved"

**Entry point**: the integrated worktree branch; `python3 easy_memory.py hook-stop` and `redact`

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | Full suite passes on an odd day and an even day; sorted test-name lists and skips are identical (diff pasted). | Gate 0 |
| 2 | Redaction tests pass: one fixture per pattern, no-secret byte identity, 1 MB under the NFR-008 limit (timing pasted). | Gate 0, NFR-008 |
| 3 | `tests/bench_t004.py` p95 on the branch is not worse than on `main` (both numbers pasted). | Gate 0 |
| 4 | A smoke run (`hook-stop` then `hook-prompt` on a temp store, with fake secrets) adds no line to `hook.log`, and the saved note holds no fixture secret. | Gate 0 |
| 5 | A filled `RUNBOOK.md` entry is drafted: "Redaction release (FR-009): <date of merge>", to be committed with the merge. | A10 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The reviewer fills **Evidence** at Stage 4/5 in `tasks/TASK_REVIEW_<ID>.md`, copied from
> `templates/TASK_REVIEW_template.md`. A task is **not done** until every row has evidence.

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | Branch suite, odd and even day | `OK` twice, identical name lists | pasted output |
| 2 | Smoke with a fake `ghp_` token in the answer | `hook.log` line count unchanged; note holds `[REDACTED:github_token]` | pasted output |

### Verification Command (exact, runnable)

```bash
python3 -m unittest discover -s tests -v 2>&1 | tail -5 && python3 tests/bench_t004.py
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-87.md` (review sections are never taken from the board).

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_HUN-87.md` (review sections are never taken from the board).

## Approach

**Pattern reference**: `tests/test_t009_smoke.py` (HUN-82 end-to-end smoke).

**Vital slice**: extend the smoke test with one redaction path; run and paste the Gate 0 checks.
**Cut list**: A CI job; a date-faking dependency.

**Conventions**: `unittest`, `EASY_MEMORY_HOME` temp dirs, fake secrets only. Never run against the real `~/.easy-memory`.

---

## Edge Case Checklist

- [ ] The benchmark is noisy: run it 3 times on each side and compare medians of p95.
- [ ] Smoke run must not use the user's real Claude settings.

---

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| tests/test_t009_smoke.py | add a redaction smoke path |
| RUNBOOK.md | drafted release-date line (committed with the merge) |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| easy_memory.py | QA is the oracle, not the implementer |

---

## Test Plan

Odd/even suite runs, redaction tests, benchmark on both sides, smoke run with `hook.log` line count before and after.

---

## Completion Checklist

- [ ] Checks run and evidence pasted into the TASK_REVIEW Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: Gate 0 ready for the user's merge