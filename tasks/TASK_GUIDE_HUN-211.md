**Date**: 2026-11-04
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P2
**Assigned agent**: backend-developer
**Agent guide**: `agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt; read `memory/MEMORY.md` in full only if your work reaches what the slice does not cover
3. Read this file completely
4. Read `agents/backend.md` in full
5. Apply the C2 process from the Complexity matrix in `agents/backend.md`
6. Read `PRD.md` NFR-001 and FR-003; `PRD_v0.2.md` Gate 2a row; `memory/decisions.md` entry "2026-11-04 — Prompt hook splits each word once per run (HUN-208 merged)"; `tasks/TASK_REVIEW_HUN-208.md` (Negative cases row)
7. Read `easy_memory.py`: `_prompt_weight`, `_score_with`, `_index_lines`, `prompt_index`, `_tool_search`, `MAX_STDIN_CHARS`

---

## Requirement (Pillar 1 — Adapt the requirement)

HUN-208 /verify probe, 2026-11-04, real CLI on a copy of a 440-note store: a 1.7 MB prompt of 150,000 distinct words took 17.4 s on the branch (171.7 s on the old `main`); the hook timeout is 5 s (`HOOK_EVENTS`), so Claude Code kills the hook and nothing is injected. Cause: `_score_with` loops over every distinct prompt word for every note, so time ≈ distinct prompt words × notes. Large pastes (logs, files) are real prompts. Follow-up asked by the user 2026-11-04.

**Restated intent**:

> When a prompt has more than `PROMPT_MAX_WORDS` (1,000) distinct scorable words, the hook and `memory_search` score it on only that many: the highest-weight (rarest) words, ties broken by first appearance. A prompt at or under the cap is scored exactly as today. Target (user, 2026-11-04): the worst-case prompt stays under the 5 s hook timeout on 4,000 notes, and under NFR-001 (1 s) at the real store size (440 notes).

**Out of scope**:

* Any change for prompts at or under the cap (byte-identical output — AC1).
* `INDEX_*` values, `STOP_WORDS`, the score formula, the note schema.
* Faster `read_notes`, a saved cache file, retention.

**Requirement Refs**: HUN-208 verify probe 6 (`tasks/TASK_REVIEW_HUN-208.md`); `PRD.md` NFR-001.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [X] Restated intent confirmed to match the user's request (by Supervisor, 2026-11-04)
- [X] Every Acceptance Criterion below traces to the requirement

---

## Dependencies & Reachability

**Depends on**: HUN-208 (merged).

**Branch**: `prompt-word-cap` from `main`.

**Merge gate**: PRD v0.2 Gate 2a — APPROVED by the user 2026-11-04 for this task, with cap 1,000 ("Cap 1,000, timeout target"). Measured on this repo's 245 text files: 3 of 245 (about 1%) exceed 1,000 distinct words, so only those rank differently. Otherwise none beyond Stage 4/5. Also approved 2026-11-04: `PROMPT_MAX_CHARS` = 200,000 (only prompts over 200,000 characters change).

**Entry point**: `hook_prompt` → `prompt_index` → `_index_lines` → `_prompt_weight`; MCP `memory_search` → `_tool_search` → `_index_lines`.

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | For prompts with ≤ `PROMPT_MAX_WORDS` distinct words, `_index_lines` output equals the HUN-208 golden (`tests/test_prompt_word_split.py` unchanged and green) | under-cap unchanged |
| 2 | For a prompt over the cap, `_prompt_weight` keeps exactly `PROMPT_MAX_WORDS` words: the highest weights, ties by first appearance; deterministic across runs and `PYTHONHASHSEED` values | rule |
| 3 | The 150,000-distinct-word prompt (1.7 MB): `hook-prompt` subprocess exits 0 in < 5 s (hook timeout) on a 4,000-note fixture store, and in < 1 s on a 440-note store | timeout; NFR-001 at real size (user 2026-11-04: 1 s at 4,000 notes is not reachable by a cap — read_notes alone ~0.7 s, prompt split ~0.5 s) |
| 4 | `PROMPT_MAX_WORDS = 1000` (user 2026-11-04); the measurement table (cap vs notes vs time, and the 245-file corpus counts) is in a code comment summary and the review file | measured, user-chosen |
| 5 | `memory_search` with an over-cap query returns within the same bound | both callers |
| 6 | `plugin/easy_memory.py` is byte-identical to `easy_memory.py` | release rule |
| 7 | Only the first `PROMPT_MAX_CHARS` (200,000) characters of a prompt are split and scored, for the hook and `memory_search` (applied inside `_prompt_weight`). A 10 MB prompt (stdin maximum, 1.75M distinct words) exits 0 in < 1 s on 440 notes; prompts of ≤ 200,000 characters rank exactly as before | security review P2 2026-11-04 (10 MB: 3.98 s, 449 MB on 440 notes); user 2026-11-04 "Both fixes", Gate 2a approved |
| 8 | `_word_parts` returns its parts in sorted order, so `_prompt_weight`'s kept set over the cap is identical across `PYTHONHASHSEED` values for prompts with camelCase / underscore words (test: cap 5, `fooBarBazQuxQuuxCorge zq000 zq111 zq222 zq333 zq444`, seeds 0-3 give one set); `tokens()` multiset unchanged | security review P3→P1 (AC2 broken, confirmed by Supervisor: 4 seeds, 4 sets) |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| \# | Given | Expect | How it's checked |
| -- | -- | -- | -- |
| 1 | under-cap prompts, golden fixture | identical output | automated test |
| 2 | over-cap prompt, 2 hash seeds | same kept words | automated test |
| 3 | 4,000 notes / 440 notes, 150k-word prompt | < 5 s / < 1 s, rc 0 | opt-in probe test (`HUN211_CAP_PROBE=1`, two cases: 4,000 and 440 notes), numbers pasted |

### Verification Command (exact, runnable)

```bash
python3 -m unittest tests.test_prompt_word_cap tests.test_prompt_word_split && python3 -m unittest discover -s tests
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-211.md` (review sections are never taken from the board).

## Approach

1. Before any change: time the over-cap probe on `main` (BEFORE).
2. Tests first in `tests/test_prompt_word_cap.py`.
3. In `_prompt_weight`: after building the weight map, if it has more than `PROMPT_MAX_WORDS` entries, keep the top ones by (−weight, first index). Measure to pick the constant.
4. Copy to `plugin/easy_memory.py`; full suite; probe AFTER.

## Edge Case Checklist

- [ ] Ties by first appearance need the prompt's word order, not `set()` order
- [ ] `best` (the denominator) is computed over the kept words only, consistently
- [ ] Every hook path still exits 0 and prints nothing on error (NFR-004)

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| `easy_memory.py` | `_prompt_weight`, one constant |
| `tests/test_prompt_word_cap.py` | new |
| `plugin/easy_memory.py` | copy |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| `INDEX_*`, `STOP_WORDS`, `tokens`, note schema | ranking and schema (Gate 2a) |
| any `~/.easy-memory/` store, user's real `~/.claude*` | tests use a temp `EASY_MEMORY_HOME` |
| `agents/`, `skills/`, `.claude/` | dev kit |

## Test Plan

New test file, HUN-208's golden test unchanged, full suite (510 tests, 3 skipped, at `ada1c48`), then the opt-in probe before and after.

## Completion Checklist

- [ ] BEFORE captured on `main` before the change
- [ ] Tests written first and failing, then passing
- [ ] Full suite passes, output pasted
- [ ] Report: `Status: done` with commits, or `Status: blocked` + `Question:`