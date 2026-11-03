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

**BEFORE**: captured 2026-11-03T08:01:50Z in the worktree on branch `v04-report-json` (no implementation commit yet), by backend-developer:

```
$ python3 easy_memory.py report --json; echo "exit=$?"; ls -l ~/.easy-memory/c5aa0c6dafcc6672/report.json
usage: easy_memory [-h]
                   {hook-stop,hook-prompt,serve,report,install,uninstall,build-weights,switch,redact} ...
easy_memory: error: unrecognized arguments: --json
exit=2
ls: cannot access '/home/hungnguyenhuu/.easy-memory/c5aa0c6dafcc6672/report.json': No such file or directory
```

**AFTER**: captured 2026-11-03T08:11:36Z (backend-developer, same worktree, after the change), against this repo's own store:

```
$ python3 easy_memory.py report --json; echo "exit=$?"; ls -l ~/.easy-memory/c5aa0c6dafcc6672/report.json
{
  "v": 1,
  "generated": "2026-11-03T08:11:36Z",
  "min_sessions": 10,
  "sessions_logged": 9,
  "no_data": 0,
  "no_claude_log": 1,
  "forced": 0,
  "groups": {
    "on": {"sessions": 3, "tokens_all_median": 11518487, "tokens_io_median": 98007, "turns_median": 123},
    "off": {"sessions": 5, "tokens_all_median": 16553412, "tokens_io_median": 100808, "turns_median": 169}
  },
  "note_opened": {"opened": 0, "indexed": 3},
  "too_few": true,
  "on_vs_off_pct": null,
  "store": {"notes": 135, "bytes": 266483}
}
exit=0
-rw------- 1 hungnguyenhuu hungnguyenhuu 601 Nov  3 15:11 /home/hungnguyenhuu/.easy-memory/c5aa0c6dafcc6672/report.json
```

(The printed object is shown with the group objects on one line each; the real output is indented one key per line.) Plain `report` output on the same store: `cmp` of `main`'s `easy_memory.py report` and this branch's `report` run back to back: identical.

**DELTA**: a user (and easy-personal) can now read the memory-on versus memory-off comparison as a JSON file at `<store>/report.json`, refreshed at most hourly by the Stop hook, without running `report` or calling an MCP tool.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/HUN-197.jsonl`, never the
implementing agent alone]
