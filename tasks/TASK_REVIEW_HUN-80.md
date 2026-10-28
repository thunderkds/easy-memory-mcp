# TASK_REVIEW — T[NNN]: [Short Title]

> Sibling of `tasks/TASK_GUIDE_T[NNN].md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | `tests/test_t007_report.py` (23 tests, AC1-AC7 and SC1-SC3), fixture `tests/fixtures/report_session_static.jsonl`. Output: `Ran 23 tests in 0.413s` / `OK`. Mutation checks: REPORT_MIN_SESSIONS 10->5 and max->last-wins on duplicate message ids each fail a test. |
| Verification command run | pass | `python3 -m unittest discover -s tests -p 'test_t007*.py' -v` -> 23 tests, each `... ok`, ends `Ran 23 tests in 0.413s` / `OK` (run 2026-10-28, HUN-80 branch) |
| Negative cases hold | pass | missing log folder, no prompts.log, corrupt prompts.log lines, garbage/non-UTF8/truncated JSONL lines, entries without usage, session id `../secret`, 9 per group warns, report writes nothing: all exit 0 and assert. |
| verify | N/A | No Skill tool for the implementing agent. Real run with temp dirs: 24 synthetic sessions printed two rows and exit 0 - pass (output under Demonstration AFTER). Supervisor runs `verify`. [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | pass | Self-review only (no code-review skill available to this agent): one new block in easy_memory.py above `_not_implemented`, plus `import statistics`, a 2-line `--repo` option in `main()`, 1 registration line; 2 stub tests in test_t001_store.py. |
| Full smoke suite still green (no regression) | pass | `python3 -m unittest discover -s tests` -> `Ran 201 tests in 5.983s` / `OK`. Two stub tests in tests/test_t001_store.py edited (report no longer a stub; script test uses `serve`). |
| **UI: Visual regression (diff or verdict pasted)** | N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-10-28T05:44:42Z on main at bc5a509, before any HUN-80 implementation commit (temp EASY_MEMORY_HOME and CLAUDE_CONFIG_DIR):

```
$ EASY_MEMORY_HOME=<tmp>/em CLAUDE_CONFIG_DIR=<tmp>/cc python3 easy_memory.py report
easy-memory report: not implemented          (exit=0)
$ ... python3 easy_memory.py report --repo .
usage: easy_memory [-h]
                   {hook-stop,hook-prompt,serve,report,install,uninstall,build-weights,switch} ...
easy_memory: error: unrecognized arguments: --repo .          (exit=2)
```

**AFTER**: 2026-10-28T05:46:55Z, same command shape, 24 synthetic sessions (12 on, 12 off), temp EASY_MEMORY_HOME and CLAUDE_CONFIG_DIR:

```
$ python3 easy_memory.py report --repo <tmp>/repo          (exit=0)
easy-memory report for <tmp>/repo
sessions logged: 24 | no data: 1 (log file, no prompts.log line) | no Claude log: 0 (prompts.log line, no log file)
state  sessions   tokens incl. cache (headline)  tokens in+out  median turns  note opened
on           12                          92,049          1,050             3  6/12 (50%)
off          12                         221,745          1,750             5  -
Tokens are per session: median over sessions. Headline = tokens including cache (...) ...
on vs off, median headline tokens: -58%
store: 1 notes, 435 bytes (notes folder of this repo)
```
With CLAUDE_CONFIG_DIR pointing at nothing: `No Claude session log found for the logged sessions (...): nothing to compare.` and exit 0. With 3 sessions per group each row ends `too few sessions to compare` (test_3_per_group_warns_next_to_numbers).

**DELTA**: The user can run `easy_memory.py report` and read one table per repo (sessions, median tokens, median turns, note-open rate, store size) with a warning under 10 sessions per group.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
