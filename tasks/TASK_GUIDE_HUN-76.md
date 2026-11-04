**Date**: 2026-10-28
**Complexity Level**: C2
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
4. Read `agents/backend.md`
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth) from the Complexity matrix in your role guide (`agents/backend.md`)
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md` if it exists (it does not yet: the repo has only `experiments/` and, from HUN-74 on, `easy_memory.py`)
7. Also read `PRD.md` (the Requirement Refs below) and `BRAINSTORMING_LOG.md` (edge cases E1 to E12)

---

## Requirement (Pillar 1 — Adapt the requirement)

FR-003 scores a prompt against notes using word weights from the repo's own source files. Building them took 16.5 s and gave a 16 MB file on Project B (7,835 files); the prompt hook has a 1 s budget. Build them in a background process, store them compactly, and prove the scores stay close to experiment 03.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> The prompt hook can read a small weights file in well under 0.1 s; a detached process builds and refreshes it; and an offline check shows the compact file ranks notes like experiment 03 did.

**Out of scope** (what this task explicitly does NOT do):

* The index itself (HUN-77).
* Incremental updates.
* Changing the scoring formula.

**Requirement Refs** (FR/NFR/US IDs from `PRD.md` this task satisfies):

* FR-003: word weights from the repo's own source files
* NFR-001: 1 s p95 for the prompt hook
* A5: limits carried over unchanged from experiment 03
* G3 (PRD flag): cache and invalidation rule
* Decision 2026-10-28 in `memory/decisions.md`

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary (`grill-with-docs` run if terminology was fuzzy)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [ ] All Requirement Refs exist in `PRD.md` and are fully covered by the Acceptance Criteria above

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: HUN-74 — repo_key and store layout must exist

**Entry point**: `build-weights` subcommand and `ensure_weights()` in `easy_memory.py`

---

## Acceptance Criteria

> Each criterion must trace back to the Requirement above (Pillar 1 → Pillar 3 link).

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | `easy_memory.py build-weights --repo <path>` writes `<store>/weights.json` atomically from the repo's source files (same extensions, skipped folders and 300 KB limit as `memstore.build_idf`) and drops words found in only one file. | FR-003, G3 |
| 2 | On Project B the file is ≤ 2 MB and loads in ≤ 0.1 s (timings pasted). | NFR-001 |
| 3 | `ensure_weights()` never waits for a build: if the file is missing it starts a detached background build and returns 'not ready'. | NFR-001, edge E1 |
| 4 | If the file is older than 1 day AND the repo HEAD differs from the one recorded in the file, `ensure_weights()` starts a rebuild but still returns the old file. | G3 |
| 5 | Two calls at once start only one build (O_EXCL lock file with a stale-lock timeout of 10 minutes). | G3 |
| 6 | Parity: using experiment 03's saved answers and prompts, the set of notes scoring ≥ 0.12 is identical for ≥ 95% of (prompt, note) pairs between full weights and compact weights, and the top-5 order is identical for ≥ 90% of prompts. Result pasted. If this fails, STOP and report to the Supervisor; do not tune the floor. | A5 |
| 7 | `score(prompt, text)` gives the same result as `memstore.score` when given full weights (port is faithful). | A5 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The reviewer fills **Evidence** at Stage 4/5 in `tasks/TASK_REVIEW_T003.md`, copied from
> `templates/TASK_REVIEW_template.md`. A task is **not done** until every row has evidence.
> The implementing agent must NOT be the sole author of its own acceptance test: the Supervisor
> signs off the Success Criteria below as the oracle.

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | No weights file | `ensure_weights()` returns not-ready within 50 ms and a lock/build process exists | unittest |
| 2 | Full vs compact weights over experiment 03 data | parity thresholds met | script `tests/parity_t003.py` |
| 3 | Two simultaneous `ensure_weights()` | one build process | unittest |

### Verification Command (exact, runnable)

```bash
python3 -m unittest discover -s tests -p 'test_t003*.py' -v && python3 tests/parity_t003.py
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-76.md` (review sections are never taken from the board).

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_HUN-76.md` (review sections are never taken from the board).

## Approach

**Pattern reference**: `experiments/02-auto-memory/memstore.py` (`tokens`, `build_idf`, `score`): port as is, then add the compaction and the background launcher.

**Vital slice**: Compact weights file plus non-blocking `ensure_weights()`.
**Cut list**: Incremental or per-file updates.; Language-specific tokenizers.; Tuning the 0.12 floor.

Port tokenizer and scorer unchanged. Compaction: keep only words with document frequency ≥ 2 and store as one JSON object `{n, head, built_at, df}`. Background build: `subprocess.Popen([sys.executable, __file__, 'build-weights', ...], start_new_session=True, stdin/stdout/stderr=DEVNULL)`. Locate experiment 03's saved answers and prompts under `experiments/03-precision/results` and `work` first; if the data needed for parity is missing, STOP and ask.

**Conventions**: Python 3, standard library only (NFR-005). Tests use `unittest` (pytest is not guaranteed). Follow `docs/claude-md/code-naming-conventions.md`. Tests never touch the real home folder, the real Claude settings, or the real `~/.easy-memory` (use temp dirs and `EASY_MEMORY_HOME` / `CLAUDE_CONFIG_DIR`). Private client repos (Project B, Project A) are read-only benchmark targets: record numbers only, never quote or commit their source.

---

## Edge Case Checklist

- [ ] Repo with no source files: write an empty-but-valid file; do not loop on rebuild.
- [ ] A word dropped for df = 1 appears in the prompt: it simply carries the default weight (document that choice and check parity).
- [ ] Build killed halfway: no partial `weights.json` (temp + rename); stale lock cleared after 10 minutes.
- [ ] Repo is not git: `head` is `null`; refresh on age only.
- [ ] Experiment 03 data quotes private source code: the parity script reads it locally and prints only counts.

---

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| easy_memory.py | add tokenizer, scorer, `build-weights`, `ensure_weights` |
| tests/test_t003_weights.py | new |
| tests/parity_t003.py | new: offline parity check; prints counts only |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| experiments/\*\* | read-only evidence (read it, never write) |
| Any file in Project B or Project A | private client repos: read-only |

---

## Test Plan

Unit tests on a synthetic repo for build, lock and not-ready behavior. Parity script on experiment 03 data. Timing on Project B recorded as numbers only.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (if Medium/High risk)
- [ ] Lint passes (`python3 -m py_compile easy_memory.py` at minimum)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T003.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working by running it
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review