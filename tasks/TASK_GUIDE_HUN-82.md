**Date**: 2026-10-28
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: qa-expert
**Agent guide**: `agents/qa.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/qa.md`
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth) from the Complexity matrix in your role guide (`agents/qa.md`)
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md` if it exists (it does not yet: the repo has only `experiments/` and, from HUN-74 on, `easy_memory.py`)
7. Also read `PRD.md` (the Requirement Refs below) and `BRAINSTORMING_LOG.md` (edge cases E1 to E12)

---

## Requirement (Pillar 1 — Adapt the requirement)

Confirm the whole prototype works together and meets the non-functional requirements: the full save → inject → open → report cycle, private file modes, no network, hook latency on a 7,000-file repo, and a clean uninstall.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> Independent evidence, in a context separate from the implementers, that the prototype is safe to install on the user's real repos.

**Out of scope** (what this task explicitly does NOT do):

* New features.
* Fixing defects (report them to the Supervisor with a failing test).

**Requirement Refs** (FR/NFR/US IDs from `PRD.md` this task satisfies):

* NFR-001 latency
* NFR-002 no network
* NFR-003 modes
* NFR-004 hooks never block
* FR-008 clean uninstall
* KPI 'Hook latency' in PRD

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary (`grill-with-docs` run if terminology was fuzzy)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [ ] All Requirement Refs exist in `PRD.md` and are fully covered by the Acceptance Criteria above

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: HUN-80 — report; HUN-81 — MCP server

**Entry point**: `tests/test_t009_smoke.py`

---

## Acceptance Criteria

> Each criterion must trace back to the Requirement above (Pillar 1 → Pillar 3 link).

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | Full cycle in a temp config dir and temp home: `install` → Stop hook with a synthetic transcript → prompt hook returns an index naming that note → MCP `memory_read` returns it → `report` runs → `uninstall` returns the settings JSON to the original. | FR-001..FR-008 |
| 2 | After the cycle every file under the store is 0600 and every folder 0700. | NFR-003 |
| 3 | Hooks and the MCP server run with sockets disabled (patched `socket.socket` raising, or `unshare -n` if available) and still work. | NFR-002 |
| 4 | On Project B with 200 notes: `hook-prompt` p95 < 1 s over 50 runs and `hook-stop` p95 < 2 s over 20 runs; numbers pasted (no source quoted). | NFR-001 |
| 5 | With the store folder made unwritable and with garbage on stdin, each hook exits 0 with empty stdout. | NFR-004 |
| 6 | No file inside the observed repo changed during the whole cycle (tree hash equal). | FR-002 |
| 7 | The repo's test command runs the whole suite green from a clean checkout: `python3 -m unittest discover -s tests`. | Gate 5 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The reviewer fills **Evidence** at Stage 4/5 in `tasks/TASK_REVIEW_T009.md`, copied from
> `templates/TASK_REVIEW_template.md`. A task is **not done** until every row has evidence.
> The implementing agent must NOT be the sole author of its own acceptance test: the Supervisor
> signs off the Success Criteria below as the oracle.

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | Full cycle on a synthetic repo | all steps pass | tests/test_t009_smoke.py |
| 2 | Latency run on Project B | p95 under limits | tests/bench_t004.py plus Stop-hook timing |
| 3 | Unwritable store | exit 0, empty stdout | unittest |

### Verification Command (exact, runnable)

```bash
python3 -m unittest discover -s tests -v
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-82.md` (review sections are never taken from the board).

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_HUN-82.md` (review sections are never taken from the board).

## Approach

**Pattern reference**: `tests/test_t002_stop_hook.py` and `tests/test_t004_prompt_hook.py` (from earlier tasks): reuse their fixtures.

**Vital slice**: One full-cycle test plus the NFR checks.
**Cut list**: Fuzzing.; Cross-OS runs.

You are the Pillar 3 oracle: do not edit implementation code. If something fails, write the failing test, report it to the Supervisor and stop.

**Conventions**: Python 3, standard library only (NFR-005). Tests use `unittest` (pytest is not guaranteed). Follow `docs/claude-md/code-naming-conventions.md`. Tests never touch the real home folder, the real Claude settings, or the real `~/.easy-memory` (use temp dirs and `EASY_MEMORY_HOME` / `CLAUDE_CONFIG_DIR`). Private client repos (Project B, Project A) are read-only benchmark targets: record numbers only, never quote or commit their source.

---

## Edge Case Checklist

- [ ] Tests must not touch the real home, Claude settings or `~/.easy-memory`.
- [ ] Latency numbers vary: report p50, p95 and max.
- [ ] Project B is a private client repo: record numbers only.

---

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| tests/test_t009_smoke.py | new |
| tasks/TASK_REVIEW_T009.md | Evidence table, filled |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| easy_memory.py | QA does not change implementation |
| experiments/\*\* | read-only evidence |

---

## Test Plan

As in Acceptance Criteria; paste the full unittest output.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (if Medium/High risk)
- [ ] Lint passes (`python3 -m py_compile easy_memory.py` at minimum)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T009.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working by running it
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review