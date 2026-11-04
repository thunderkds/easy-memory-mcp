**Date**: 2026-11-04
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
4. Read `agents/backend.md` in full
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/backend.md`
6. Read `PRD.md` NFR-001 and FR-003; `memory/learnings.md` entry 2026-10-28 (QA HUN-82, defect D1)
7. Read `easy_memory.py` sections: `tokens`, `score`, `_index_lines`, `_tool_search`, `prompt_index`; `tests/test_t003_weights.py` (`test_tokens_match_memstore`, the `memstore.score` parity test); `tests/test_t009_smoke.py` `StoreGrowthProbeTest`

---

## Requirement (Pillar 1 — Adapt the requirement)

Defect D1 (QA HUN-82, 2026-10-28): `hook-prompt` time grows about 1 ms per saved note, and there is no retention limit, so NFR-001 (prompt hook ≤ 1 s p95) breaks as a store grows. Supervisor measurement 2026-11-04 on the largest real store (`personal-agentic-claude`, 423 notes, 972 KB): `prompt_index` end to end 0.47 s; `read_notes` 0.12 s; scoring 0.37 s. cProfile: `tokens()` is \~97% of scoring time (846 calls for 423 notes — the prompt is re-tokenized inside every `score` call; `re.sub` runs once per word occurrence, 141,518 calls). A prototype with a per-run word cache (`functools.lru_cache` on the split of one word) plus one prompt split per run scored the same 423 notes in 0.13 s in a fresh process (5,841 distinct words), with every score equal to today's within 1e-12. User choice 2026-11-04: build this fix only; no saved cache file; no retention limit.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> The prompt hook and `memory_search` rank notes exactly as today, but faster: the prompt's words are split once per call of `_index_lines`, not once per note, and the split of each distinct word is computed once per process. Nothing new is written to disk; the note format, the weights file and every `INDEX_*` value stay the same.

**Out of scope** (what this task explicitly does NOT do):

* A saved word-count cache file, an inverted index, or any new file in the store (user, 2026-11-04: rejected for now).
* A retention limit, decay or expiry of notes (user, 2026-11-04: not now; PRD v0.2 FR-014 / Gate 2a).
* Faster `read_notes` (JSON parse, 0.12 s at 423 notes) — not asked; measure and report only.
* Any change to ranking: `score` formula, `k1`, `INDEX_FLOOR`, `INDEX_MAX_NOTES`, `INDEX_MAX_CHARS`, `STOP_WORDS`, tokenizer rules.
* `report_command`, the switch, `experiments/`, `site/`.

**Requirement Refs**: `PRD.md` NFR-001; QA HUN-82 defect D1 (`memory/learnings.md` 2026-10-28); user decision 2026-11-04.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [X] Restated intent confirmed to match the user's request (by Supervisor, 2026-11-04; scope picked by the user from three options)
- [X] Every Acceptance Criterion below traces to the requirement

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: none.

**Branch**: `prompt-hook-word-split` from `main` (`0bbf1cb` or later).

**Merge gate**: none beyond Stage 4/5. PRD v0.2 Gate 2a holds back changes to `INDEX_*` constants, the note schema and decay/expiry; this task changes none of them and keeps ranking identical (AC1–AC3 prove it). If any AC1–AC3 test needs a tolerance looser than `places=12`, STOP — that is a ranking change and falls under Gate 2a.

**Entry point**: `hook_prompt` → `prompt_index` → `_index_lines` → `score` → `tokens`; also MCP `memory_search` → `_tool_search` → `_index_lines`.

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | `tokens(text)` returns the same multiset of words as today for the existing fixtures (`test_tokens_match_memstore`) and for new cases: camelCase, `snake_case`, digits, words < 3 chars, stop words, the same word repeated, mixed case of one word (`Auth`, `auth`, `AUTH`) | intent "exactly as today" |
| 2 | `score(prompt, text, weights)` keeps its signature and returns the same value (`assertAlmostEqual`, `places=12`) as before for the existing `memstore.score` parity test | intent; NFR-001 must not cost ranking |
| 3 | `_index_lines` returns byte-identical lines, in the same order, as the pre-change code for a fixture store of at least 50 varied notes and at least 5 prompts (golden output captured from `main` before the change and committed as test data or computed in-test from a frozen copy of the old functions) | intent; FR-003 unchanged |
| 4 | Inside one `_index_lines` call the prompt is split once, not once per note (test counts calls with a wrapper/patch on the defining module, not on a shim — see `memory/learnings.md` package-split gotcha) | D1 root cause |
| 5 | `StoreGrowthProbeTest` (4,000 notes, opt-in `HUN82_GROWTH_PROBE=1`): record p50/max before and after in the review file. Pass bar: max at least 2× lower than the before value measured on the same machine in the same session. The probe's own 1 s assertion is NOT changed and may still fail; report its number, do not loosen it | NFR-001, D1 |
| 6 | No new file is written under `EASY_MEMORY_HOME` by `hook-prompt` or `memory_search` (test lists the store tree before and after; `prompts.log` append is today's behaviour and allowed) | user 2026-11-04 "no saved cache" |
| 7 | `plugin/easy_memory.py` is byte-identical to `easy_memory.py` (`tests/test_plugin.py`) | release rule |
| 8 | The word cache is bounded: memory use of the cache cannot grow without limit in the long-running `serve` (MCP) process — either a `maxsize` on the cache or a cache scoped to one `_index_lines` call. State the bound in a code comment | `serve` is a long-lived process |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | fixture texts from AC1 | same sorted token list as the frozen old `tokens` | automated test |
| 2 | ≥ 50-note fixture store, ≥ 5 prompts | `_index_lines` output equals the golden output exactly | automated test |
| 3 | one `_index_lines` call over N notes | prompt split counted once | automated test |
| 4 | 4,000-note probe, same machine, before vs after | max time ≥ 2× lower; both numbers in the review file | `HUN82_GROWTH_PROBE=1` run, pasted |
| 5 | real store `personal-agentic-claude` (423 notes), read-only | `prompt_index` end-to-end time before and after, pasted (Supervisor's before: 0.47 s) | manual timing, read-only — never write to `~/.easy-memory/` |

### Verification Command (exact, runnable)

```bash
python3 -m unittest tests.test_prompt_word_split && python3 -m unittest discover -s tests && HUN82_GROWTH_PROBE=1 python3 -m unittest tests.test_t009_smoke.StoreGrowthProbeTest
```

The last command may exit non-zero on its unchanged 1 s assertion; its printed `p50`/`max` line is the evidence for AC5.

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-208.md` (review sections are never taken from the board).

## Approach

1. Before any code change: run the growth probe on `main` and save the `p50`/`max` line (AC5 "before"). Capture the golden `_index_lines` output for the AC3 fixture from the unchanged code.
2. Tests first (red) in `tests/test_prompt_word_split.py`: AC1, AC3 (golden), AC4 (prompt split once), AC6 (no new store file), AC8 (bound).
3. In `easy_memory.py`: precompile the two regexes used by `tokens`; move the per-word split into a small cached helper (`functools.lru_cache(maxsize=...)` or a dict local to one `_index_lines` call — pick one, say why in the commit); keep `tokens(text)` and `score(prompt, text, weights, k1=1.2)` signatures for existing callers and tests; let `_index_lines` compute the prompt's weight map once and score each note with it (a private helper such as `_score_with(weight, best, text, k1)`; `score` becomes a thin wrapper over it).
4. Copy to `plugin/easy_memory.py`. Run the full suite, then the probe (AC5 "after"), then the read-only real-store timing.
5. Keep the diff small: target well under 40 changed lines in `easy_memory.py`. No other refactor.

---

## Edge Case Checklist

- [ ] The split of one word uses a `set` today (`{word.lower(), *parts}`), so the order of words within one source word is not stable — compare as sorted lists / Counters, never as raw lists
- [ ] Empty prompt and a prompt with no scorable words still give 0.0 / no lines (existing tests)
- [ ] A word that appears in the prompt but not in `df` still gets the rarest weight
- [ ] Non-ASCII text: the regex only matches `[A-Za-z]` starts, unchanged
- [ ] `memory_search` (MCP `serve`) gets the same speed-up and the same results
- [ ] Every hook path still exits 0 and prints nothing on error (NFR-004)
- [ ] Python 3.11+ only features are allowed (already required by the redaction regex)

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| `easy_memory.py` | `tokens` (cached word split, precompiled regexes), `score` (thin wrapper), `_index_lines` (prompt weights once) |
| `tests/test_prompt_word_split.py` | new |
| `plugin/easy_memory.py` | copy of `easy_memory.py` |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| `INDEX_*`, `STOP_WORDS`, `k1`, `read_notes`, note schema | ranking and schema (PRD v0.2 Gate 2a) |
| `tests/test_t009_smoke.py` probe's 1 s assertion | evidence, not a target to move |
| `experiments/`, `site/`, `report_command`, switch code | out of scope |
| any `~/.easy-memory/` store, user's real `~/.claude*` | tests use a throwaway `EASY_MEMORY_HOME` / config dir; real-store timing is read-only |
| `agents/`, `skills/`, `.claude/` | the repo's own dev kit |

## Test Plan

`python3 -m unittest tests.test_prompt_word_split`, plus the existing `tests/test_t003_weights.py` unchanged. Then `python3 -m unittest discover -s tests` (full suite: 499 tests, 3 skipped, at `0bbf1cb`). Then the opt-in growth probe, before and after.

## Completion Checklist

- [ ] Before numbers (probe, golden output) captured on `main` before the change
- [ ] Tests written first and failing, then passing
- [ ] Full suite passes, output pasted
- [ ] Probe and real-store timings, before and after, pasted
- [ ] Report: `Status: done` with commits, or `Status: blocked` + `Question:`