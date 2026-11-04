**Date**: 2026-11-04
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P2
**Assigned agent**: backend-developer
**Agent guide**: `agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt; read `memory/MEMORY.md` in full only if your work reaches what the slice does not cover
3. Read this file completely
4. Read `agents/backend.md` in full
5. Apply the C1 process from the Complexity matrix in `agents/backend.md`
6. Read `memory/decisions.md` entry "2026-11-04 — Prompt hook splits each word once per run (HUN-208 merged)" and `tasks/TASK_REVIEW_HUN-208.md` (Review scope row)
7. Read `easy_memory.py`: `_word_parts`, `tokens`, `serve_command`; `tests/test_prompt_word_split.py`

---

## Requirement (Pillar 1 — Adapt the requirement)

HUN-208 Stage 4, P2 accepted at merge (user 2026-11-04, "merge it as is"), follow-up asked by the user 2026-11-04. `_word_parts` is cached with `functools.lru_cache(maxsize=1 << 16)`. That bounds entries, not bytes: a full cache of ordinary words measured 28.6 MB (tracemalloc, Supervisor 2026-11-04), and the comment at its definition says "a few MB". A word is any match of `[A-Za-z][A-Za-z0-9_]*` with no length cap, so in the long-running MCP `serve` process (lines up to `MCP_MAX_LINE`, 4M characters) 65,536 very long words could pin GBs. Security review (independent agent, 2026-11-04): P3, confidence 75.

**Restated intent**:

> Words longer than a fixed limit (`WORD_CACHE_MAX_CHARS`, about 64) are split without the cache; shorter words use it as today. `tokens()` output is unchanged for every input. The code comment states the real bound (entries × max key size) with a measured number.

**Out of scope**:

* Any change to `tokens()` output, scoring or ranking.
* Prompt-length limits (that is the long-prompt follow-up task).
* A saved cache file.

**Requirement Refs**: HUN-208 review P2 (`tasks/TASK_REVIEW_HUN-208.md`); `memory/decisions.md` 2026-11-04 entry.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [X] Restated intent confirmed to match the user's request (by Supervisor, 2026-11-04)
- [X] Every Acceptance Criterion below traces to the requirement

---

## Dependencies & Reachability

**Depends on**: HUN-208 (merged).

**Branch**: `word-cache-byte-bound` from `main`.

**Merge gate**: none beyond Stage 4/5 (no ranking change).

**Entry point**: `tokens` → `_word_parts` (prompt hook, `memory_search`, weights build).

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | `tokens(text)` equals the frozen old `tokens` (as Counters) for the existing AC1 fixtures plus words of length limit-1, limit, limit+1 and 100,000 characters | output unchanged |
| 2 | After `tokens()` on a text with 1,000 distinct 10,000-character words, no cached key is longer than the limit (inspect via a test hook or `cache_info().currsize` delta of 0) | byte bound |
| 3 | The comment at `_word_parts` states the bound as entries × limit and a measured MB number for a full cache | doc fix |
| 4 | `plugin/easy_memory.py` is byte-identical to `easy_memory.py` | release rule |
| 5 | `tests/test_prompt_word_split.py` still passes unchanged (golden sha256) | ranking unchanged |

---

## Evaluation & Acceptance

### Success Criteria (observable, pass/fail)

| \# | Given | Expect | How it's checked |
| -- | -- | -- | -- |
| 1 | AC1 fixtures | same multiset of tokens | automated test |
| 2 | 1,000 long distinct words | cache does not grow | automated test |
| 3 | full suite | green | `python3 -m unittest discover -s tests` |

### Verification Command (exact, runnable)

```bash
python3 -m unittest tests.test_word_cache_bound tests.test_prompt_word_split && python3 -m unittest discover -s tests
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-210.md` (review sections are never taken from the board).

## Approach

1. Tests first in `tests/test_word_cache_bound.py`.
2. In `tokens`: `out.extend(_word_parts(word) if len(word) <= WORD_CACHE_MAX_CHARS else _word_parts.__wrapped__(word))`, or an equivalent two-line split. Fix the comment.
3. Copy to `plugin/easy_memory.py`; full suite.

## Edge Case Checklist

- [ ] A long word with camelCase parts still yields its short parts
- [ ] Every hook path still exits 0 and prints nothing on error (NFR-004)

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| `easy_memory.py` | `tokens`, `_word_parts` comment, one constant |
| `tests/test_word_cache_bound.py` | new |
| `plugin/easy_memory.py` | copy |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| `score`, `_score_with`, `_index_lines`, `INDEX_*`, `STOP_WORDS` | ranking (Gate 2a) |
| any `~/.easy-memory/` store, user's real `~/.claude*` | tests use a temp `EASY_MEMORY_HOME` |
| `agents/`, `skills/`, `.claude/` | dev kit |

## Test Plan

New test file, then the full suite (510 tests, 3 skipped, at `ada1c48`).

## Completion Checklist

- [ ] Tests written first and failing, then passing
- [ ] Full suite passes, output pasted
- [ ] Report: `Status: done` with commits, or `Status: blocked` + `Question:`