# TASK_REVIEW — HUN-87: Gate 0 pass check before the redaction release

> Sibling of `tasks/TASK_GUIDE_HUN-87.md`. Everything here is **filled by the reviewer at Stage
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

Oracle run 2026-10-29 07:27 to 07:45 UTC by qa-expert on branch `hun-87` (base commit 1e8f58c plus the HUN-87 test and RUNBOOK changes), compared with `main`. Day forcing: `FAKE_TODAY=<date> PYTHONPATH=<scratchpad>/fakedate` (a `sitecustomize.py` that patches `datetime.date.today`, also in child pythons). The guide's verification command `python3 tests/bench_t004.py` has no `--repo`, which the script requires; `--repo <worktree>` was used.

### Gate 0 conditions

| # | Gate 0 condition (PRD_v0.2) | Verdict | Evidence |
|---|---|---|---|
| 1 | Suite passes on an odd day and an even day, same names and skips | PASS | odd (2026-10-29): `Ran 368 tests in 24.625s / OK (skipped=3)`. even (2026-10-30): `Ran 368 tests in 24.642s / OK (skipped=3)`. A per-test outcome list (name + ok/skipped), sorted, `diff` of the two: empty ("DIFF EMPTY: identical names and outcomes"). Skips on both days: `FullCycleTest.test_hooks_and_server_work_without_a_network_namespace` (no `unshare -rn`), `LatencyTest.test_latency_on_private_repo` (opt-in), `StoreGrowthProbeTest.test_prompt_hook_p95_stays_under_1_second_with_4000_notes` (opt-in). |
| 1b | "All 307 v0.1 tests" still present | PASS (1 intended rename) | `main`: 307 tests, OK (skipped=3) on both days. Branch has 368 = 307 - 1 + 62 added. The one name in `main` and not on the branch: `test_t009_smoke.PrivacyProbeTest.test_secret_in_prompt_and_answer_is_stored_in_clear_but_only_in_private_note_files`, renamed by HUN-85 to `..._is_redacted_and_the_note_file_is_private` (it asserted the old no-redaction behavior). |
| 2a | One fixture per pattern fully redacted | PASS | `tests/test_t010_redact.py` `RedactTextTest.test_each_kind_is_replaced_and_secret_is_gone` loops `PER_KIND` = anthropic_key, api_key, aws_access_key, bearer_token, github_token, jwt, secret_assignment, slack_token; `private_key` has `test_private_key_block_multi_line`. That is all 9 kinds in `_REDACT_PATTERNS` + private_key. `python3 -m unittest discover -s tests -p test_t010_redact.py -v`: `Ran 59 tests in 1.399s / OK`. |
| 2b | No-secret fixture byte-identical | PASS | `RedactTextTest.test_no_secret_text_is_byte_identical`, `HookStopRedactionTest.test_no_secret_note_is_byte_identical`, `RedactCommandTest.test_second_apply_is_byte_identical_and_reports_no_hit`: all ok. My own smoke test also asserts the clean note file bytes unchanged after `redact --apply`. |
| 2c | 1 MB input under the NFR-008 limit | PASS | NFR-008 limit is 2 s (the test asserts < 1.0 s). Worst of 26 adversarial 1 MB inputs: `redact 1MB long TOKEN run: 0.187s`; `repeated BEGIN: 0.007s`; `hook-stop with 1MB repeated BEGIN: 0.059s` (whole hook). |
| 3 | `tests/bench_t004.py` p95 not worse than `main` | **FAIL if read literally; within noise** (Supervisor decides) | Even day forced (2026-10-30, so the scorer runs), same repo `--repo <worktree>`, 8 interleaved pairs. p95 main: 0.202 0.193 0.195 0.198 0.195 0.199 0.203 0.233 -> median **0.1985 s**. p95 hun-87: 0.217 0.204 0.255 0.225 0.222 0.200 0.204 0.197 -> median **0.2105 s** (+12 ms, +6%). p50 median main 0.184, branch 0.189. Not clearly separable from noise: control, main vs a byte-identical copy of main in another folder, p95 pairs 0.201/0.205, 0.206/0.199, 0.217/0.224, 0.232/0.218 (single-run spread up to 14 ms); import time of the module measured 40.2 ms (main) vs 41.2 ms (branch). Absolute p95 ~0.21 s against a 1 s budget (NFR-001). hook-prompt code is unchanged by Gate 0. |
| 4 | Smoke run adds no `hook.log` line; note holds no fixture secret | PASS | New tests `RedactionSmokeTest` (2 tests) ok. Manual run in temp dirs (switch on, weights built, real Stop with a transcript, then prompt hook): `hook.log lines before: 0`, `hook-stop exit=0`, `hook-prompt exit=0`, `hook.log lines after: 0`, `files holding the fake token: 0`, `2 [REDACTED:github_token]` (prompt and answer). |
| 5 | RUNBOOK line drafted | PASS (draft) | `RUNBOOK.md` Measurement Window row now reads `Redaction release (FR-009): YYYY-MM-DD`; the Supervisor replaces both placeholders at merge. |

### TASK_REVIEW Evidence rows

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | `tests/test_t009_smoke.py` class `RedactionSmokeTest`: `test_stop_redacts_the_token_and_adds_no_hook_log_line` (AC4) and `test_redact_dry_run_shows_id_and_kind_only_apply_removes_it_and_a_second_apply_is_quiet`. `python3 -m unittest tests.test_t009_smoke.RedactionSmokeTest -v` -> `Ran 2 tests in 0.595s / OK`. Negative control: the same tests run against `main`'s pre-redaction `easy_memory.py` -> `FAILED (failures=2)` (`'[REDACTED:github_token]' not found in 'token ghp_abc...'`). AC1-3 are covered by existing suites (`tests/test_t010_redact.py`, `tests/bench_t004.py`), run as above. |
| Verification command run | fail (AC3 literal) / pass (AC1, 2, 4, 5) | Suite: `Ran 368 tests ... OK (skipped=3)` on both forced days. Benchmark: median p95 0.2105 s branch vs 0.1985 s main (see row 3 above). The guide's bench command lacks `--repo`. |
| Negative cases hold | pass | Dry run leaves the old-style note unchanged and prints only id and `aws_access_key 1`; second `--apply` prints `No secrets found in 2 note(s).` and `Rewrote` is absent; a note with no secret is byte-identical. Smoke for hostile input already in `HooksNeverBlockTest`. |
| verify | N/A | The `Skill` tool is not available to this agent. The equivalent check was run by hand: the running hooks and `redact` command on temp stores (output above). Supervisor to run `/verify`. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | pass | Changed only `tests/test_t009_smoke.py` (new test class) and `RUNBOOK.md` (one row). `easy_memory.py` not touched. Ran the whole suite (368) because redaction touches the Stop hook and the note format. |
| Full smoke suite still green (no regression) | pass | `tests.test_t009_smoke` before: `Ran 29 tests / OK (skipped=3)`; full suite after: 368 tests OK on both days. |
| **Companion score (easy-verifier)** | N/A | Not run: easy-verifier server is a Docker tool needing the user's approval of the project-scoped server; the merge gate blocks on fail only. |
| **UI: Visual regression** | N/A | No UI. |
| **UI: Design-system compliance** | N/A | No UI. |
| **UI: Responsiveness** | N/A | No UI. |

---


## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-10-29 07:27:26 UTC on branch `hun-87` (HEAD 53e8ff7), before any HUN-87 implementation commit:

```
$ date -u && python3 -m unittest tests.test_t009_smoke -v 2>&1 | tail -5
Thu Oct 29 07:27:26 AM UTC 2026

----------------------------------------------------------------------
Ran 29 tests in 10.641s

OK (skipped=3)
```
The smoke suite has 29 tests and no test of the `redact` command; `grep -n redact -i tests/test_t009_smoke.py` shows only the HUN-85 privacy probe (lines 801-815).

**AFTER**: captured 2026-10-29 ~07:35 UTC, same command plus the added tests (full suite 368 tests, OK, skipped=3, see Evidence). Smoke class after:

```
$ python3 -m unittest tests.test_t009_smoke.RedactionSmokeTest -v
test_redact_dry_run_shows_id_and_kind_only_apply_removes_it_and_a_second_apply_is_quiet ... ok
test_stop_redacts_the_token_and_adds_no_hook_log_line ... ok
Ran 2 tests in 0.595s
OK
```

**DELTA**: The release now has one report that checks each Gate 0 condition with pasted evidence; the smoke suite now covers redaction at save and the `redact` command, and the RUNBOOK has the release-date line ready.

**WITNESS**: qa-expert (independent of the HUN-85/86 implementer), 2026-10-29; trace in `memory/event-trace/HUN-87.jsonl` (main checkout).
