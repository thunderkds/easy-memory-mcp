**Date**: 2026-10-30
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P2
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
6. Read `PRD_v0.3.md` (Decision record row for M5) and `BRAINSTORMING_LOG_v0.3.md` (Edge Case Checklist, M5)
7. Read `easy_memory.py` sections: `tokens`, `score`, `_index_lines`, `prompt_index`, `_tool_search`, `load_weights`, `INDEX_*` constants

---

## Requirement (Pillar 1 — Adapt the requirement)

Verifier list V-R4 (2026-10-30): note 20261030T115937407-fc608eed appeared in the index for almost every prompt. Check 2026-10-30: for "wanna check if the memory mcp work or not" it scores 0.238 and 8 of 13 notes pass the 0.12 floor — the cause is common-word prompts plus no length term in `score`. User chose: BM25 length adjustment and a rare-word rule.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> `score` gains BM25 length adjustment (`b = 0.75`, average length = mean token count of the repo's notes read in the same pass). A note is a candidate only if it contains at least one rare prompt word: a word missing from the weights `df`, or with `df <= RARE_SHARE * n`. `RARE_SHARE` is one constant set on a fixture set in this task. Floor, 5-line and 2,500-character caps unchanged; the README states the cap and the rule.

**Out of scope** (what this task explicitly does NOT do):

* Changing `INDEX_FLOOR`, `INDEX_MAX_NOTES`, `INDEX_MAX_CHARS`.
* Weighting the question over the answer (option 3, not chosen).
* Embeddings (FR-013).
* Rewriting notes already saved (user, 2026-10-30: old notes are not rewritten).
* `report_command`, the switch, `INDEX_FLOOR` / `INDEX_MAX_NOTES` / `INDEX_MAX_CHARS` values, `experiments/`, `site/`.

**Requirement Refs**: `PRD_v0.3.md` M5; verifier V-R4; PROJECT_SPEC Critical Constraints (no scorer change without an offline check against experiment 03).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [X] Restated intent confirmed to match the user's request (by Supervisor, 2026-10-30; rules fixed with the user in requirement grilling)
- [X] Every Acceptance Criterion below traces to the requirement

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: none (parallel with the HUN-137 stack).

**Branch**: `v03-m5-ranking` from `main`.

**Merge gate**: PRD v0.2 Gate 2a — do NOT merge into `main` until the sample bar is met and the report is done (user, 2026-10-30: keep the gates). The live hooks run the `main` checkout (PRD v0.2 A9). Also needs the offline check against experiment 03 answers; that data is missing (`experiments/03-precision/work/`, PRD v0.2 O2, owner: user) — report it as the open blocker for merge, not for the build.

**Entry point**: `_index_lines` (shared by the prompt hook and `memory_search`).

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | Fixture: 10 short notes + 1 note 10× longer sharing only common words with an unrelated prompt: the long note is not in the result | V-R4 acceptance |
| 2 | Same fixture, a prompt that shares a rare word with the long note: it is in the result | V-R4 "related prompt still does" |
| 3 | A prompt with no rare word returns no lines; `memory_search` replies "No matching notes." | rare-word rule |
| 4 | `memory_search` with no weights file (`n = 0`): results identical to today on the existing tests | edge |
| 5 | Deterministic: same notes + prompt → same lines and order (ties keep oldest first) | V-R4 |
| 6 | `RARE_SHARE` value and how it was chosen are written in the test file and the README | V-R4 "state the rule" |
| 7 | `tests/bench_t004.py` p95 not worse by more than 10% | NFR-009 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | long-note fixture, unrelated common-word prompt | long note absent | automated test |
| 2 | same, related rare-word prompt | long note present | automated test |
| 3 | existing `tests/test_t004_hook_prompt.py` | adjusted only where a fixture relied on the old score; each change listed in the report | automated test |

### Verification Command (exact, runnable)

```bash
python3 -m unittest tests.test_v03_m5_ranking && python3 tests/bench_t004.py && python3 -m unittest discover -s tests
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-140.md` (review sections are never taken from the board).

## Approach

1. Tests first (red) in `tests/test_v03_m5_ranking.py`; build the fixture so it mirrors the verifier case (note lengths 500–6,300 characters, one 3,500-character pasted question).
2. `score(prompt, text, weights, avg_len)`: BM25 `k1 * (1 - b + b * len/avg_len)`; keep the 0..1 share normalisation.
3. Rare-word gate in `_index_lines` before scoring. 4. Pick `RARE_SHARE` from the fixture; record the value and the reason.
4. Any existing test that changes: list it with the reason in the report — never silently re-baseline.

---

## Edge Case Checklist

- [ ] `n = 0` weights: every word is rare, so the gate is a no-op
- [ ] Average length over zero notes: no division by zero
- [ ] Prompt words dropped by `STOP_WORDS` or length < 3 do not count as rare
- [ ] Average computed in the same pass as `read_notes` — no extra file reads (prompt-hook latency is a High-risk area)
- [ ] `plugin/easy_memory.py` is byte-identical to `easy_memory.py` in the same commit (`tests/test_plugin.py`)
- [ ] Every hook path still exits 0 and prints nothing on error (NFR-004)

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| `easy_memory.py` | `score`, `_index_lines`, new `RARE_SHARE`, `BM25_B` |
| `tests/test_v03_m5_ranking.py` | new |
| `README.md` | cap and ranking rule |
| `plugin/easy_memory.py` | copy of `easy_memory.py` |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| `experiments/`, `site/`, `docs/RELEASE_v0.1.0.md` | out of scope |
| `report_command`, switch code, `INDEX_*` values | measurement code (PRD v0.2 Gate 2a) |
| any `~/.easy-memory/` store, user's real `~/.claude*` | tests use a throwaway `EASY_MEMORY_HOME` / config dir |
| `agents/`, `skills/`, `.claude/` | the repo's own dev kit |

## Test Plan

`python3 -m unittest tests.test_v03_m5_ranking` and `python3 tests/bench_t004.py`. Then `python3 -m unittest discover -s tests` (full suite, 434 tests at `cb876eb`).

## Completion Checklist

- [ ] Tests written first and failing, then passing
- [ ] Full suite passes, output pasted
- [ ] README updated where an AC says so
- [ ] Not merged into `main` unless the Merge gate above is open
- [ ] Report: `Status: done` with commits, or `Status: blocked` + `Question:`