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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | `tests/test_t005_switch.py` (28 tests; AC1 to AC6, SC1 to SC3, edge cases: unknown or corrupt config, midnight crossing, worktree-shared config). AC and SC ids are in each test's comment. |
| Verification command run | pass | `python3 -m unittest discover -s tests -p 'test_t005*.py' -v` -> `Ran 28 tests in 0.709s` / `OK` (2026-10-28, backend-developer; full test names in the run output, all `ok`) |
| Negative cases hold | pass | bad state word refused (exit 2, no config written); unwritable store -> exit 1, message, no traceback; `prompts.log` made a folder -> stdout and exit code unchanged (AC6); unreadable stdin -> no prompts.log line, one hook.log line; unknown config value -> auto + one hook.log line |
| verify | N/A | No Skill tool in this agent run. Real run done by hand instead, see Demonstration AFTER: `switch`, `switch off`, `hook-prompt` printed nothing and logged `effective: off`; with `auto` on an even day the log shows `effective: on`. The Supervisor runs `verify`. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | pass | Self-review (no `code-review` skill available) of `git diff`: easy_memory.py (hook_prompt rewritten, 5 new functions, `switch` subparser) and tests/test_t001_store.py (one-line subcommand list). hook-stop untouched. Not reviewed: unrelated modules. |
| Full smoke suite still green (no regression) | pass | `python3 -m unittest discover -s tests` -> `Ran 178 tests in 7.742s` / `OK`; `[NFR-001] 7000 files, 20 runs: p95=0.131s`. One existing test changed: `test_t001_store.py:288` now expects `switch` in `SUBCOMMANDS` (a new subcommand, not a stub that became real). |
| **UI: Visual regression (diff or verdict pasted)** | N/A | No UI. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | N/A | No UI. |
| **UI: Responsiveness at target viewports** | N/A | No UI. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-10-28T05:37Z by backend-developer, before any implementation commit; temp EASY_MEMORY_HOME, removed afterwards):

```
# 2026-10-28T05:37:37Z  cd worktree; EASY_MEMORY_HOME=<temp store> python3 easy_memory.py switch
usage: easy_memory [-h]
                   {hook-stop,hook-prompt,serve,report,install,uninstall,build-weights} ...
easy_memory: error: argument command: invalid choice: 'switch' (choose from hook-stop, hook-prompt, serve, report, install, uninstall, build-weights)
exit=2
# 2026-10-28T05:37:37Z  ... switch off
usage: easy_memory [-h]
                   {hook-stop,hook-prompt,serve,report,install,uninstall,build-weights} ...
easy_memory: error: argument command: invalid choice: 'switch' (choose from hook-stop, hook-prompt, serve, report, install, uninstall, build-weights)
exit=2
# 2026-10-28T05:37:37Z ls store: 0 entries
hook-prompt exit=0; prompts.log present: 0
```

**AFTER** (same kind of capture, 2026-10-28T05:39Z, temp EASY_MEMORY_HOME, removed afterwards; the date is the real local date, day 20754):

```
# 2026-10-28T05:39:42Z  python3 easy_memory.py switch
switch: auto
today: on (day 20754 is even)
exit=0
# 2026-10-28T05:39:42Z  python3 easy_memory.py switch off
switch: off
today: off (set to off)
exit=0
# 2026-10-28T05:39:42Z  hook-prompt with state off
stdout above (empty), exit=0
# 2026-10-28T05:39:42Z  python3 easy_memory.py switch auto
switch: auto
today: on (day 20754 is even)
exit=0
# 2026-10-28T05:39:43Z  store listing and prompts.log
-rw------- 1 hungnguyenhuu hungnguyenhuu  31 Oct 28 12:39 config.json
-rw------- 1 hungnguyenhuu hungnguyenhuu 226 Oct 28 12:39 prompts.log
-rw------- 1 hungnguyenhuu hungnguyenhuu   0 Oct 28 12:39 weights.lock
{"time": "2026-10-28T05:39:42Z", "session_id": "s1", "configured": "off", "effective": "off", "injected": false}
{"time": "2026-10-28T05:39:43Z", "session_id": "s1", "configured": "auto", "effective": "on", "injected": false}
{
  "v": 1,
  "state": "auto"
}
```

**DELTA**: The user can run `easy_memory.py switch on|off|auto` for one repo (default auto: even day on, odd day off), and every prompt now leaves one JSON line in `<store>/prompts.log`.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
