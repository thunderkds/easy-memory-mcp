# TASK_REVIEW — HUN-210: Word cache skips long words, so its memory has a byte bound

> Sibling of `tasks/TASK_GUIDE_HUN-210.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

<!-- Optional: the final report, only for a task run in auto mode (the user's `[auto]` tag,
`docs/claude-md/tracks.md` `## Auto mode`). To use it, copy the block below out of this comment, to this
place, and replace every <...>. Keep `Mode: auto` as its first line, exactly as written: T182's hook reads
it. Write it to this file before the run ends; the chat message is a copy, not the report. The same
block is the Supervisor's final chat message. It is not the `delivery-report` page and not
Evidence. A taste decision (what the user wants) also ends with the flag. Write `DEBATED` only when ≥2
Advocate `Agent` calls ran for that question, naming each Advocate's option. A decision with no Advocates is
labelled `RULE`, `FACT` or `SAFER OPTION`, never `DEBATED`. A decision flagged `⚠ decided for you` is a choice, and is never labelled `FACT`. A
safety action a rule requires (for example the backup before a delete) is `RULE` without the flag.
At Risk Medium or High, a `RULE:` counts only when it names a written rule (`path:line`,
`path § <heading>`, or `docs/claude-md/tracks.md` `### <section>`), and a `FACT:` needs a Citation
(`path:line "quoted text"`); without one it is a choice and must be `DEBATED`. Good: `2. backed up the CSV
— RULE: `docs/claude-md/tracks.md` `### Stops that stay``. Bad: `1. kept recurring.csv — RULE: Surgical Changes`.

## Auto decisions

Mode: auto
1. <what was decided> — RULE: <the rule>
2. <what was decided> — FACT: <path>:<line> "<quoted text>"
3. <what was decided> — DEBATED: <option> (Advocate 1: <its option>; Advocate 2: <its option>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
Checks: tests `<command>` — <result>; reviews <skill — result>; real run `<command>` — printed `<what it printed>` (auto-checked, not /verify)
Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>

-->

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_word_cache_bound.py` (7 tests: AC1 lengths 63/64/65/100,000 vs frozen `old_tokens`; AC2 1,000 long words leave `currsize == 0`, short words still hit; AC4 plugin copy). Supervisor run 2026-11-04: `Ran 517 tests in 69.057s` / `OK (skipped=3)` — pass |
| Verification command run | ☑ pass | Supervisor 2026-11-04: `python3 -m unittest discover -s tests` → `Ran 517 tests` `OK (skipped=3)` (510 + 7 new); `tests/test_prompt_word_split.py` unedited and green — pass |
| Negative cases hold | ☑ pass | words of length 65 and 100,000 split as before (AC1); camelCase long word still yields short parts; lane_check `C1, 3 files, 81 lines, FITS` — pass |
| verify | ☑ pass | Supervisor real-surface run 2026-11-04 (user `/verify` not run for this task): MCP `serve` on a copy of the real 440-note store under a temp `EASY_MEMORY_HOME`, 40 `memory_search` calls with 1,600 distinct 20,000-char words: main RSS 27 → 95 MB, branch 27 → 35 MB; 0 errors; normal query 5 hits on both — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | `tokens`, `_word_parts`, `WORD_CACHE_MAX_CHARS`; callers `_prompt_weight`, `_score_with`, `_count_words` unchanged. Code review (inline): 0 P0, 0 P1, 0 P2; P3 tests reach `_word_parts.__wrapped__`/`cache_info` (lru internals, stable stdlib API) — accepted. Startup reads complete (PROJECT_SPEC, guide, `agents/backend.md`). Security review not required (Risk Low) — pass |
| Full smoke suite still green (no regression) | ☑ pass | 510 baseline tests pass inside the 517 — pass |
| **Companion score (easy-verifier)** | ☑ N/A | not run for this task |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | backend only |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | backend only |
| **UI: Responsiveness at target viewports** | ☑ N/A | backend only |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (2026-11-04T10:42:50Z, unchanged code at `0d3304d`, `python3 -I` with the worktree on `sys.path`; probe: 1,000 distinct 10,000-character words, `tokens()` under tracemalloc):

```
$ python3 -I probe210.py
CacheInfo(hits=0, misses=1000, maxsize=65536, currsize=1000)
tracemalloc current bytes: 20219266 = 20.2 MB
```

So 1,000 long words are all cached (currsize=1000), about 20 KB each (key + the lower-cased copy in the cached tuple). At 65,536 entries of 10,000 characters that would be about 1.3 GB.

Comment at `_word_parts` (`easy_memory.py:416`):
`@functools.lru_cache(maxsize=1 << 16)  # bound: at most 65,536 distinct words (a few MB) in a long `serve``

**AFTER** (2026-11-04T10:44:44Z, same probe, changed code):

```
$ python3 -I probe210.py
CacheInfo(hits=0, misses=0, maxsize=65536, currsize=0)
tracemalloc current bytes: 362 = 0.0 MB
```

New comment at `_word_parts`: "Bound: 65,536 entries x words of at most WORD_CACHE_MAX_CHARS (64) characters; tokens() does not cache longer words. Measured with tracemalloc: a full cache of 65,536 camelCase-rich 64-character words is about 46 MB."

**DELTA**: A long-running `serve` no longer keeps very long words in memory: 1,600 distinct 20,000-character query words leave it at 35 MB instead of 95 MB, with the same search results.

**WITNESS**: Supervisor, 2026-11-04: re-ran the suite in the worktree and drove MCP `serve` on main vs branch (store copy, temp `EASY_MEMORY_HOME`); independent of the implementing agent.
