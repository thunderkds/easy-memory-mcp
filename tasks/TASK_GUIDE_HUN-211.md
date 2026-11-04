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

> When a prompt has more than `PROMPT_MAX_WORDS` distinct scorable words, the hook and `memory_search` score it on only that many: the highest-weight (rarest) words, ties broken by first appearance. A prompt at or under the cap is scored exactly as today. `PROMPT_MAX_WORDS` is chosen by measurement so a capped prompt on the 4,000-note probe store stays within NFR-001 (1 s).

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

**Merge gate**: ASK THE USER before merge whether PRD v0.2 Gate 2a applies. Ranking changes only for prompts over the cap; those used to time out on large stores, but on small stores some finished under 5 s, so their results can differ. Report the measured cap and how often real prompts exceed it (count from a test corpus, never by reading `~/.easy-memory`).

**Entry point**: `hook_prompt` → `prompt_index` → `_index_lines` → `_prompt_weight`; MCP `memory_search` → `_tool_search` → `_index_lines`.

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | For prompts with ≤ `PROMPT_MAX_WORDS` distinct words, `_index_lines` output equals the HUN-208 golden (`tests/test_prompt_word_split.py` unchanged and green) | under-cap unchanged |
| 2 | For a prompt over the cap, `_prompt_weight` keeps exactly `PROMPT_MAX_WORDS` words: the highest weights, ties by first appearance; deterministic across runs and `PYTHONHASHSEED` values | rule |
| 3 | The 150,000-distinct-word prompt (1.7 MB) on a 4,000-note fixture store: `hook-prompt` subprocess finishes in < 1 s, exits 0 | NFR-001, timeout |
| 4 | `PROMPT_MAX_WORDS` value and the measurement that chose it are in a code comment and the review file | measured, not guessed |
| 5 | `memory_search` with an over-cap query returns within the same bound | both callers |
| 6 | `plugin/easy_memory.py` is byte-identical to `easy_memory.py` | release rule |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| \# | Given | Expect | How it's checked |
| -- | -- | -- | -- |
| 1 | under-cap prompts, golden fixture | identical output | automated test |
| 2 | over-cap prompt, 2 hash seeds | same kept words | automated test |
| 3 | 4,000 notes, 150k-word prompt | < 1 s, rc 0 | opt-in probe test, numbers pasted |

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