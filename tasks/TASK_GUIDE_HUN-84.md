**Date**: 2026-10-29
**Complexity Level**: C1
**Risk Level**: Low
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
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/backend.md`
6. Also read `PRD_v0.2.md` (Gate 0 row and open item O6)

---

## Requirement (Pillar 1 — Adapt the requirement)

19 tests in `tests/test_t004_hook_prompt.py` fail on odd days (2026-10-29: `FAILED (failures=7, errors=12, skipped=3)`). They never set the per-repo switch, so `auto` resolves to `off` on odd days (`effective_state`, `easy_memory.py:640`) and the prompt hook prints nothing. Make the suite independent of the calendar date. This is the first step of Gate 0.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> The full v0.1 suite gives the same result, with the same test names and the same skips, whether it runs on an odd day or an even day. Only test code changes.

**Out of scope** (what this task explicitly does NOT do):

* Any change to `easy_memory.py` (the live hooks run from this checkout; PRD_v0.2 A9).
* Secret redaction (next task).
* The `configured == auto` report filter (O5).

**Requirement Refs**:

* PRD_v0.2 Gate 0 "First step" and open item O6
* NFR-004 tests stay as they are in intent: no assertion is weakened

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [ ] All Requirement Refs exist in `PRD_v0.2.md` and are fully covered by the Acceptance Criteria

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: None — can start immediately

**Entry point**: `python3 -m unittest discover -s tests -v`

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | With `_today` forced to an odd day, the full suite passes. | O6 |
| 2 | With `_today` forced to an even day, the full suite passes. | O6 |
| 3 | Both runs report the same test names, the same count (307 at v0.1) and the same skips. | Gate 0 pass |
| 4 | Subprocess tests (for example `test_subprocess_stdout_is_one_json_object_or_nothing`) get the switch through the store's `config.json`, because a `mock.patch` does not reach a child process. | O6 |
| 5 | `git diff --stat` shows changes under `tests/` only. No assertion is removed or loosened. | A9 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The reviewer fills **Evidence** at Stage 4/5 in `tasks/TASK_REVIEW_<ID>.md`, copied from
> `templates/TASK_REVIEW_template.md`. A task is **not done** until every row has evidence.

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | Suite run with the system date on an odd day (use `faketime` if installed, else a runner that patches `easy_memory._today` and `datetime.date` for the parent process) | `OK`, same skips as the even run | pasted output |
| 2 | Suite run on an even day | `OK` | pasted output |
| 3 | `diff` of the two sorted `-v` name lists | empty | pasted command and output |

### Verification Command (exact, runnable)

```bash
python3 -m unittest discover -s tests -v 2>&1 | tail -5
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-84.md` (review sections are never taken from the board).

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_HUN-84.md` (review sections are never taken from the board).

## Approach

**Pattern reference**: `tests/test_t005_switch.py` already sets the switch and patches `_today`; follow it.

**Vital slice**: in `PromptHookTestCase.setUp`, write `{"state": "on"}` to the temp store's `config.json` for the test repo. Tests that need `auto` or `off` set it themselves.
**Cut list**: A shared test base class across files; a date-faking dependency.

Prefer writing the switch to `config.json` over patching `_today`: it reaches subprocesses too. Check other test files for the same hidden date dependency (grep for `hook-prompt` and `hook_prompt`) and fix them the same way if found.

**Conventions**: Python 3, standard library only. `unittest`. Tests never touch the real home folder or the real `~/.easy-memory` (use `EASY_MEMORY_HOME` temp dirs).

---

## Edge Case Checklist

- [ ] A test that checks `auto` behaviour must still see `auto`: do not override it.
- [ ] A test that deletes or rewrites `config.json` keeps working.
- [ ] Tests that use a new repo created mid-test also get the switch.

---

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| tests/test_t004_hook_prompt.py | set the switch to `on` in setup |
| tests/test_t009_smoke.py | only if it has the same date dependency |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| easy_memory.py | live hooks run from this checkout (A9) |
| experiments/\*\* | read-only evidence |

---

## Test Plan

Run the full suite twice, odd and even day, and compare the sorted test-name lists.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Tests pass on odd and even days — output pasted into the TASK_REVIEW Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review