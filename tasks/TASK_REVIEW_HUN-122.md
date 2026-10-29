# TASK_REVIEW — HUN-122: Report compares only auto-switch sessions

> Sibling of `tasks/TASK_GUIDE_HUN-122.md`. Everything here is **filled by the reviewer at Stage
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
| ☑ pass | `tests/test_t007_report.py` class `ForcedSwitchTest` (10 tests: AC1-AC6, SC1-SC3, edge cases); pass. `tests/test_t009_smoke.py` adjusted (see below). | [test file path(s) — required before Done] |
| ☑ pass | `python3 -m unittest discover -s tests -v 2>&1 \| tail -5` real day: `OK (skipped=3)`; with FAKE_TODAY=2026-10-29 (odd): `Ran 378 tests in 35.260s / OK (skipped=3)`; FAKE_TODAY=2026-10-30 (even): `Ran 378 tests in 38.359s / OK (skipped=3)`. Before the change the 10 new tests failed 9 times (test-first). | [paste actual output] |
| ☑ pass | configured `maybe`/None/5/list/`AUTO`/missing key: treated as forced (`test_odd_configured_values_count_as_not_auto`); all-forced repo: 0/0 rows, no verdict, no crash; forced session with no Claude log: counted as forced only; forced start stays excluded; auto start stays included; 5 forced do not lift a 9-session group over the bar. | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| ☑ pass | Full suite above incl. `test_t009_smoke`, odd and even day. One adjustment: `tests/test_t009_smoke.py` `run_cycle` used `switch on` (forced) and asserted the session sits in the on group (`^on\s+1\s`, `1/1 (100%)`); it now asserts `forced switch: 1 (left out of the comparison)` and `^on\s+0\s`. Note-open rate stays covered by `test_t007_report.test_note_open_rate_counts_only_sessions_that_got_an_index`. | |
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

**BEFORE**: captured 2026-10-29 08:25:08 UTC (`date -u`), before any implementation commit, on `main` code in worktree `hun-122`. Temp `EASY_MEMORY_HOME` and `CLAUDE_CONFIG_DIR`; `prompts.log` seeded with 2 auto-on, 3 auto-off, 4 forced-on, 1 forced-off sessions, each with a Claude log. Command: `python3 easy_memory.py report --repo <tmp>/repo`.

```
easy-memory report for <tmp>/repo
sessions logged: 10 | no data: 0 (log file, no prompts.log line) | no Claude log: 0 (prompts.log line, no log file)
state  sessions   tokens incl. cache (headline)  tokens in+out  median turns  note opened
on            6                             116            116             1  -  too few sessions to compare
off           4                             114            114             1  -  too few sessions to compare
Tokens are per session: median over sessions. Headline = tokens including cache (input + cache creation + cache read + output), as experiments 01 to 03 counted them; 'in+out' is input + output only (PRD FR-007 wording). Sub-agent work counts with its session. Note opened = share of on sessions that got an index and then ran memory_read or Read on a note.
too few sessions to compare (fewer than 10 sessions in a group): do not read a result into these numbers yet.
store: 0 notes, 0 bytes (notes folder of this repo)
```

Forced sessions sit inside the groups: on shows 6 (2 auto + 4 forced), off shows 4 (3 auto + 1 forced). There is no forced count.

**AFTER**: captured 2026-10-29 08:30:09 UTC (`date -u`), same seed and command, with the change:

```
easy-memory report for <tmp>/repo
sessions logged: 10 | no data: 0 (log file, no prompts.log line) | no Claude log: 0 (prompts.log line, no log file) | forced switch: 5 (left out of the comparison)
state  sessions   tokens incl. cache (headline)  tokens in+out  median turns  note opened
on            2                             110            110             1  -  too few sessions to compare
off           3                             113            113             1  -  too few sessions to compare
Tokens are per session: median over sessions. Headline = tokens including cache (input + cache creation + cache read + output), as experiments 01 to 03 counted them; 'in+out' is input + output only (PRD FR-007 wording). Sub-agent work counts with its session. Note opened = share of on sessions that got an index and then ran memory_read or Read on a note. Only sessions where the switch was auto (the day decided the state) are compared; forced on/off sessions are not.
too few sessions to compare (fewer than 10 sessions in a group): do not read a result into these numbers yet.
store: 0 notes, 0 bytes (notes folder of this repo)
```

**DELTA**: `report` now compares only sessions where the day decided the state (on 2, off 3 instead of 6 and 4) and prints how many forced sessions it left out (5), so the sample bar can be read from the table.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/HUN-122.jsonl`, never the
implementing agent alone]
