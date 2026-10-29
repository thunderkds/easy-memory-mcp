# TASK_REVIEW — HUN-84: Hook-prompt tests pass on any day

> Sibling of `tasks/TASK_GUIDE_HUN-84.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_t004_hook_prompt.py` (the 19 existing date-dependent tests now run with the switch `on`; no new test file). Odd day 307 tests `OK (skipped=3)`, even day 307 tests `OK (skipped=3)`, sorted name lists `diff` empty. See Demonstration AFTER. |
| Verification command run | ☑ pass | `python3 -m unittest discover -s tests -v 2>&1 | tail -5` on 2026-10-29 (odd): `Ran 307 tests in 24.220s` / `OK (skipped=3)`. |
| Negative cases hold | ☑ pass | `tests/test_t005_switch.py` (auto, off, corrupt config, no config.json written by a read) and `tests/test_t007_report.py` still pass on both days: their base class default is `switch = None`, so they see `auto`. |
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

**BEFORE**: captured 2026-10-29 before any implementation commit (HEAD `ed3e53f`, branch `hun-84`).

```
$ date -u
Thu Oct 29 05:00:04 AM UTC 2026
$ python3 -c "from datetime import date;print('day parity', (date.today().toordinal()-date(1970,1,1).toordinal())%2)"
day parity 1          # 1 = odd day, so `auto` resolves to `off`
$ python3 -m unittest discover -s tests -v 2>&1 | tail -5
----------------------------------------------------------------------
Ran 307 tests in 25.461s

FAILED (failures=7, errors=12, skipped=3)

[NFR-001] 7000 files, 20 runs: min=0.082s p50=0.093s p95=0.121s max=0.164s
```

The 19 failing tests (`-v` lines ending `... FAIL` or `... ERROR`, all in `tests/test_t004_hook_prompt.py`):

```
test_corrupt_and_wrongly_typed_notes_are_skipped (test_t004_hook_prompt.FailureTest.test_corrupt_and_wrongly_typed_notes_are_skipped) ... ERROR
test_corrupt_weights_values_log_one_line (test_t004_hook_prompt.FailureTest.test_corrupt_weights_values_log_one_line) ... FAIL
test_subprocess_stdout_is_one_json_object_or_nothing (test_t004_hook_prompt.FailureTest.test_subprocess_stdout_is_one_json_object_or_nothing) ... FAIL
test_unexpected_error_logs_one_line (test_t004_hook_prompt.FailureTest.test_unexpected_error_logs_one_line) ... FAIL
test_at_most_five_lines_best_score_first (test_t004_hook_prompt.IndexTest.test_at_most_five_lines_best_score_first) ... ERROR
test_cap_drops_whole_lowest_scoring_lines (test_t004_hook_prompt.IndexTest.test_cap_drops_whole_lowest_scoring_lines) ... ERROR
test_changed_cited_file_is_flagged (test_t004_hook_prompt.IndexTest.test_changed_cited_file_is_flagged) ... ERROR
test_deleted_cited_file_is_flagged (test_t004_hook_prompt.IndexTest.test_deleted_cited_file_is_flagged) ... ERROR
test_flags_compare_against_this_worktree (test_t004_hook_prompt.IndexTest.test_flags_compare_against_this_worktree) ... ERROR
test_header_says_data_out_of_date_and_how_to_open (test_t004_hook_prompt.IndexTest.test_header_says_data_out_of_date_and_how_to_open) ... ERROR
test_line_fields_are_truncated (test_t004_hook_prompt.IndexTest.test_line_fields_are_truncated) ... ERROR
test_one_match_of_three_gives_one_line_with_header (test_t004_hook_prompt.IndexTest.test_one_match_of_three_gives_one_line_with_header) ... ERROR
test_ignore_previous_instructions_stays_quoted_inside_frame (test_t004_hook_prompt.InjectionTest.test_ignore_previous_instructions_stays_quoted_inside_frame) ... ERROR
test_output_json_survives_quotes_and_backslashes (test_t004_hook_prompt.InjectionTest.test_output_json_survives_quotes_and_backslashes) ... FAIL
test_tampered_id_and_file_names_are_not_shown (test_t004_hook_prompt.InjectionTest.test_tampered_id_and_file_names_are_not_shown) ... ERROR
test_text_mimicking_frame_and_header_cannot_escape (test_t004_hook_prompt.InjectionTest.test_text_mimicking_frame_and_header_cannot_escape) ... ERROR
test_corrupt_weights_adds_nothing_and_starts_build (test_t004_hook_prompt.NothingAddedTest.test_corrupt_weights_adds_nothing_and_starts_build) ... FAIL
test_empty_and_slash_prompts_add_nothing (test_t004_hook_prompt.NothingAddedTest.test_empty_and_slash_prompts_add_nothing) ... FAIL
test_missing_weights_adds_nothing_and_starts_build (test_t004_hook_prompt.NothingAddedTest.test_missing_weights_adds_nothing_and_starts_build) ... FAIL
```

**AFTER**: same suite, same checkout, after the change. The fake-date runs use a test-only `sitecustomize.py` outside the repo (`PYTHONPATH=<scratchpad>/fakedate`, `FAKE_TODAY=<date>`) that makes `datetime.date.today()` return the fixed date in the test process and in every child `python3`. `faketime` is not installed.

```
$ date -u
Thu Oct 29 05:02:09 AM UTC 2026         # real date, odd day
$ python3 -m unittest discover -s tests -v 2>&1 | tail -5
Ran 307 tests in 24.220s

OK (skipped=3)

[NFR-001] 7000 files, 20 runs: min=0.077s p50=0.079s p95=0.105s max=0.116s

$ FAKE_TODAY=2026-10-29 PYTHONPATH=<scratchpad>/fakedate python3 -m unittest discover -s tests -v   # odd day (parity 1)
Ran 307 tests in 24.781s

OK (skipped=3)

$ FAKE_TODAY=2026-10-30 PYTHONPATH=<scratchpad>/fakedate python3 -m unittest discover -s tests -v   # even day (parity 0)
Ran 307 tests in 25.143s

OK (skipped=3)

$ grep -E " \.\.\. " after_2026-10-29.txt | sort > names_odd.txt   # includes the outcome (ok / skipped '...')
$ grep -E " \.\.\. " after_2026-10-30.txt | sort > names_even.txt
$ wc -l < names_odd.txt; wc -l < names_even.txt
307
307
$ diff names_odd.txt names_even.txt && echo "DIFF EMPTY"
DIFF EMPTY
```

Diff (`git diff --stat -- tests/ easy_memory.py`): `tests/test_t004_hook_prompt.py | 15 +++++++++++++++`, `easy_memory.py` untouched. No line removed.

**DELTA**: The v0.1 suite now gives `OK (skipped=3)` with the same 307 test names on an odd day and on an even day, where it gave `FAILED (failures=7, errors=12, skipped=3)` on odd days.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/HUN-84.jsonl`, never the
implementing agent alone]
