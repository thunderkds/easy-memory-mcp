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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

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

**AFTER**: same probe, `PROMPT_MAX_WORDS = 300`, 2026-11-04 (machine load average 8-9 on 8 cores, so wall times are pessimistic):

```
$ HUN211_CAP_PROBE=1 HUN211_CAP_NOTES=440 python3 -m unittest tests.test_prompt_word_cap.OverCapProbeTest   (2 runs, OK)
[HUN-211 cap probe] notes=440 words=150,000 hook-prompt p50=0.773s max=0.794s ; memory_search serve session 0.901s
[HUN-211 cap probe] notes=440 words=150,000 hook-prompt p50=0.707s max=0.726s ; memory_search serve session 0.751s
$ HUN211_CAP_PROBE=1 python3 -m unittest tests.test_prompt_word_cap.OverCapProbeTest      (4,000 notes)
[HUN-211 cap probe] notes=4000 words=150,000 hook-prompt p50=1.927s max=2.003s   -> FAILED the < 1 s assertion
```

Measurement (scratch script, 3 runs each, medians, hook-prompt subprocess):

| notes | cap | 150k-word prompt | small prompt (no cap effect) | repo-source prompt (2.0 MB, 8,979 distinct words) |
|---|---|---|---|---|
| 440 | none | 16.3 s | 0.17 s | 0.87 s |
| 440 | 100 | 0.65 s | 0.16 s | 0.36 s |
| 440 | 300 | 0.72 s | 0.17 s | 0.37 s |
| 440 | 1000 | 0.73 s | 0.18 s | 0.35 s |
| 4000 | 100 | 1.29 s | 0.73 s | 1.00 s |
| 4000 | 300 | 1.50 s | 0.70 s | 1.12 s |
| 4000 | 500 | 1.64 s | 0.66 s | 1.22 s |
| 4000 | 1000 | 2.42 s | 0.86 s | 2.50 s |

Why AC3 does not hold at 4,000 notes: the cap removes the notes x words term, but two fixed costs remain. (1) The notes alone: a small prompt takes 0.7 s on 4,000 notes (reading and scoring the store; the known HUN-82 growth defect). (2) Splitting the 150,000-word prompt: `tokens` takes 0.5 s cold (3 us per new word; the 65,536-entry word cache thrashes on 150,000 distinct words), plus about 0.15 s for weights and the sort. So even cap 0 would take about 1.3 s. At 440 notes (the size of the real store) the probe passes at 0.7-0.8 s.

Typical large prompts (this repo, `git ls-files` text files): 245 files, median 295 distinct words, 121 over 300, 24 over 500, 3 over 1,000, max 1,202; all 245 files pasted together (2.0 MB) have 8,979. So a cap of 300 changes the ranking for about half of file-sized pastes; 500 for about 10%.

**DELTA**: A 150,000-word, 1.7 MB prompt on a 440-note store now gets its index in about 0.7 s instead of 16.3 s, inside the 5 s hook timeout; on 4,000 notes 229.8 s becomes about 1.5-1.9 s (still above 1 s).

**WITNESS**: [who ran it and when — derived from `memory/event-trace/HUN-211.jsonl`, never the
implementing agent alone]
