# TASK_REVIEW — HUN-211: A very long prompt is scored on a capped set of its words, inside the hook timeout

> Sibling of `tasks/TASK_GUIDE_HUN-211.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_prompt_word_cap.py` (AC1 under-cap identical, AC2/AC8 kept set across seeds 0,1,2,3,4,12345 in subprocesses incl. camelCase repro, AC7 only first 200,000 chars scored + exactly-200,000 unchanged, AC5 memory_search, AC6 plugin copy; 4 opt-in probe cases). Supervisor run 2026-11-04: `Ran 535 tests in 45.088s` / `OK (skipped=7)` — pass |
| Verification command run | ☑ pass | Supervisor 2026-11-04 (load 4.2-4.9): full suite `Ran 535 tests` `OK (skipped=7)`; `HUN211_CAP_PROBE=1 python3 -m unittest tests.test_prompt_word_cap` → `Ran 18 tests` `OK`: 10 MB 4,000 notes p50 1.100 s max 1.165 s (limit 5 s); 10 MB 440 notes max 0.352 s (1 s); 1.7 MB 4,000 notes max 1.138 s; 1.7 MB 440 notes max 0.234 s — pass |
| Negative cases hold | ☑ pass | seeds 0-3 on `fooBarBazQuxQuuxCorge zq000 … zq444` with cap 5 → one set (before fix: 4 sets); 10 MB prompt (stdin max) rc 0; weights odd values raise as before and the hook stays silent (security review check 4) — pass |
| verify | ☑ pass | Supervisor real-CLI run 2026-11-04 (user `/verify` not run for this task) on a copy of the real 440-note store under a temp `EASY_MEMORY_HOME`: 4 real prompts (6 / 360 / 800 / 1,195 distinct words) byte-identical to main; 150k-word prompt main 171.7 s → branch 0.27 s (38 MB); 10 MB prompt 3.98 s / 449 MB (before AC7) → 0.44 s / 55 MB — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | `_word_parts`, `PROMPT_MAX_WORDS`, `PROMPT_MAX_CHARS`, `_prompt_weight`; callers `_index_lines` (hook + `memory_search`), `score`, `_count_words` (tokens multiset unchanged). lane_check `C2, 4 files, 274 lines, FITS; unpredicted: tasks/TASK_GUIDE_HUN-211.md`. Code review: 0 P0; P1 AC8 hash-seed order (security review, confirmed) — fixed `215b5e6`; P2 10 MB prompt 4 s / 449 MB — fixed by AC7 `215b5e6` (user approved, Gate 2a); P1 process: first pass skipped required startup reads, done after resume; P3 accepted: over the cap the denominator covers kept words only (large pastes may clear `INDEX_FLOOR` a bit more easily; injected text still bounded). AC3 re-scoped by the user 2026-11-04 (1 s at 4,000 notes unreachable by a cap). Security review: independent read-only agent — pass |
| Full smoke suite still green (no regression) | ☑ pass | 517 pre-task tests pass unedited inside the 535 (HUN-208 golden and HUN-210 tests unchanged) — pass |
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

**BEFORE**: captured on unchanged `easy_memory.py` (`920b706`, no `PROMPT_MAX_WORDS`), before any implementation commit.

```
$ date -u +%FT%TZ; HUN211_CAP_PROBE=1 HUN211_CAP_NOTES=4000 python3 -m unittest tests.test_prompt_word_cap.OverCapProbeTest
2026-11-04T11:13:39Z
[HUN-211 cap probe] notes=4000 prompt=1,642,889 chars words=150,000 hook-prompt p50=229.795s max=251.336s
FAIL: test_150k_word_prompt_finishes_under_1_second ... AssertionError: 251.33571903900156 not less than 1.0 : NFR-001: hook-prompt must add at most 1 s
Ran 1 test in 705.360s
FAILED (failures=1)
2026-11-04T11:25:25Z
```

3 runs of `hook-prompt` subprocess (rc 0 each): p50 229.8 s, max 251.3 s on 4,000 notes (hook timeout is 5 s). The `memory_search` half of the probe did not run (the assertion on the hook time failed first). Probe: `tests/test_prompt_word_cap.py` `OverCapProbeTest` (fixture as in `StoreGrowthProbeTest`: 4,000 notes of about 2.5 KB, 3,000-word vocabulary; prompt = 3,000 vocabulary words + 147,000 unique `pay0000000`-style words, shuffled).

**AFTER**: same probe with the user's cap `PROMPT_MAX_WORDS = 1000` (2026-11-04). `HUN211_CAP_PROBE=1 python3 -m unittest tests.test_prompt_word_cap.OverCapProbeTest` has two cases: 4,000 notes < 5 s (hook timeout), 440 notes < 1 s (NFR-001 at the real store size). Both ran twice, `OK`. Load average (1 min, `os.getloadavg()` at print time) is beside each number:

```
$ uptime -> load average 3.33     (run 1)
[HUN-211 cap probe] notes=4000 words=150,000 hook-prompt p50=1.353s max=1.385s limit=5.0s load=3.31
[HUN-211 cap probe] notes=4000 memory_search serve session 1.299s load=3.44
[HUN-211 cap probe] notes=440  words=150,000 hook-prompt p50=0.552s max=0.613s limit=1.0s load=3.44
[HUN-211 cap probe] notes=440  memory_search serve session 0.630s load=3.44
$ uptime -> load average 3.44     (run 2)
[HUN-211 cap probe] notes=4000 words=150,000 hook-prompt p50=1.315s max=1.422s limit=5.0s load=3.57
[HUN-211 cap probe] notes=4000 memory_search serve session 1.307s load=3.57
[HUN-211 cap probe] notes=440  words=150,000 hook-prompt p50=0.537s max=0.575s limit=1.0s load=3.52
[HUN-211 cap probe] notes=440  memory_search serve session 0.547s load=3.52
```

Earlier runs at the same code path under load average 8-9 (8 cores) were slower; cap 300 gave 1.5-1.9 s at 4,000 notes and 0.71-1.12 s at 440 notes then. Cap-versus-time table (cap 300 and others, scratch script, medians of 3, load 8-9, so pessimistic):

| notes | cap | 150k-word prompt | small prompt | repo-source prompt (2.0 MB, 8,979 distinct words) |
|---|---|---|---|---|
| 440 | none | 16.3 s | 0.17 s | 0.87 s |
| 440 | 100 | 0.65 s | 0.16 s | 0.36 s |
| 440 | 300 | 0.72 s | 0.17 s | 0.37 s |
| 440 | 1000 | 0.73 s | 0.18 s | 0.35 s |
| 4000 | 100 | 1.29 s | 0.73 s | 1.00 s |
| 4000 | 300 | 1.50 s | 0.70 s | 1.12 s |
| 4000 | 500 | 1.64 s | 0.66 s | 1.22 s |
| 4000 | 1000 | 2.42 s | 0.86 s | 2.50 s |

Fixed costs a cap cannot remove: the notes alone take about 0.7 s at 4,000 notes (HUN-82 growth defect); splitting a 150,000-word prompt takes about 0.5 s cold (the 65,536-entry word cache thrashes). 1 s at 4,000 notes is therefore not reachable by a cap; the user accepted a 5 s target there.

Corpus (this repo, `git ls-files` text files, never `~/.easy-memory`): 245 files, median 295 distinct words, max 1,202; 121 over 300, 24 over 500, 3 over 1,000. All 245 pasted together (2.0 MB): 8,979 distinct words. With cap 1,000 only 3 of 245 files (about 1%) rank differently.

**AFTER (Stage 4 fixes AC7 and AC8, 2026-11-04)**: `PROMPT_MAX_CHARS = 200_000` (only the first 200,000 characters of a prompt are split and scored) and `_word_parts` returns sorted parts. `HUN211_CAP_PROBE=1 python3 -m unittest tests.test_prompt_word_cap.OverCapProbeTest`, 4 cases, `Ran 4 tests` / `OK`, run twice; load is the 1-minute load average at print time:

```
run 1 (uptime load 2.69)
[HUN-211 cap probe] notes=4000 prompt=10,000,003 chars hook-prompt p50=1.138s max=1.192s limit=5.0s load=2.64
[HUN-211 cap probe] notes=440  prompt=10,000,003 chars hook-prompt p50=0.320s max=0.344s limit=1.0s load=2.64
[HUN-211 cap probe] notes=4000 prompt=1,642,889 chars  hook-prompt p50=1.356s max=1.585s limit=5.0s load=2.58 ; memory_search 1.520s
[HUN-211 cap probe] notes=440  prompt=1,642,889 chars  hook-prompt p50=0.235s max=0.276s limit=1.0s load=2.62 ; memory_search 0.232s
run 2 (uptime load 3.22)
[HUN-211 cap probe] notes=4000 prompt=10,000,003 chars hook-prompt p50=1.482s max=1.865s limit=5.0s load=3.52 ; memory_search 1.136s
[HUN-211 cap probe] notes=440  prompt=10,000,003 chars hook-prompt p50=0.392s max=0.482s limit=1.0s load=3.64 ; memory_search 0.407s
[HUN-211 cap probe] notes=4000 prompt=1,642,889 chars  hook-prompt p50=1.763s max=2.265s limit=5.0s load=4.47 ; memory_search 1.156s
[HUN-211 cap probe] notes=440  prompt=1,642,889 chars  hook-prompt p50=0.263s max=0.281s limit=1.0s load=4.35 ; memory_search 0.266s
```

- The 10 MB prompt (about 2 million distinct 4- and 5-letter words, under the 10 MiB stdin limit) on 440 notes: 0.32-0.39 s p50, limit 1 s. On 4,000 notes: 1.14-1.48 s p50, limit 5 s. All rc 0.
- `memory_search` takes lines of at most 4 MiB (`MCP_MAX_LINE`), so for the 10 MB cases it gets the first 3.5 million characters, still far over the cap.
- The 150,000-word 1.7 MB prompt is now also cut to its first 200,000 characters (about 18,000 words), so it is faster than the cap-1,000-only numbers above (440 notes: 0.24-0.26 s was 0.55 s). The 10 MB case is the worst case now.
- Memory: `_prompt_weight` on the 10 MB prompt in a scratch process kept peak RSS at the baseline of 124 MB (the baseline is the test's own word list) and took 0.077 s; the finding was 449 MB for the whole hook before the fix.
- AC8: `tests/test_prompt_word_cap.py::test_kept_words_with_camel_and_underscore_parts_do_not_depend_on_hash_seed` runs the reviewer's repro (cap 5, `fooBarBazQuxQuuxCorge zq000 ...`) in subprocesses with `PYTHONHASHSEED` 0, 1, 2, 3, 4, 12345 and gets one result. The test failed before the fix.
- Full suite: `Ran 535 tests` / `OK (skipped=7)`. HUN-208 golden and HUN-210 tests pass unedited.

**DELTA**: Hook-prompt no longer takes more than 0.5 s on 440 notes (1.9 s on 4,000 notes) even for a 10 MB prompt of distinct words, down from 3.98 s (440 notes, Stage 4 finding) and from 229.8 s (150,000-word prompt on 4,000 notes, BEFORE); and which words a capped prompt keeps no longer changes between runs.

**WITNESS**: Supervisor, 2026-11-04: re-ran suite and all 4 probe cases in the worktree, seed check, and the real CLI on a store copy (temp `EASY_MEMORY_HOME`); security review by an independent read-only agent; independent of the implementing agent.
