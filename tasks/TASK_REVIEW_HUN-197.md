# TASK_REVIEW — HUN-197: report --json writes report.json for the easy-personal dashboard

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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_v04_report_json.py` (25 tests, AC1-AC7); `python3 -m unittest tests.test_v04_report_json` → `Ran 25 tests in 1.592s` `OK` (Supervisor, 2026-11-03) |
| Verification command run | ☑ pass | `python3 -m unittest discover -s tests` (Supervisor, worktree, 2026-11-03): `Ran 498 tests in 56.629s` `OK (skipped=3)`, exit=0 |
| Negative cases hold | ☑ pass | fresh/locked/future-mtime → no spawn; spawn failure → exit 0, no output; marker strings absent from report.json; empty store → valid object |
| verify | ☑ pass | /verify run by the Supervisor 2026-11-03T08:45Z, cold start (no verifier skill), real CLI: `report --json` on this repo's store → exit 0, stdout == report.json (cmp), 0600, numbers equal the text report (on 3 / off 5, 15,145,501 / 16,553,412, too_few, pct null); `hook-stop` in a throwaway store → exit 0, no output, 83 ms, report.json written by the detached child with no marker or path; second Stop within the hour → no refresh; aged 2 h → refreshed; aged + fresh lock → no refresh, lock kept; aged + 20-min lock → refreshed, lock removed; future mtime → untouched. Finding: `report --json --repo <missing path>` exits 0 and creates a store folder holding only report.json — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | `git diff main...HEAD` (7 files) + callers `save_stop_note`, `_repo_root`, `write_note`. lane_check: `C2, 6 files, 657 lines, EXCEEDS (lines 657 > 500); unpredicted: tests/test_t002_hook_stop.py, tests/test_t004_hook_prompt.py` (343 lines are the new test file; the two test edits only fake the new spawn). code-review: 0 P0, 0 P1 code, 1 P1 process (startup reads), 1 P2. security-review: no finding ≥ 8 (argv list, no shell; O_EXCL lock; atomic write; numbers-only object) |
| Full smoke suite still green (no regression) | ☑ pass | 498 tests OK (skipped=3), same 3 skips as main |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | no UI (the card is XR-1 in easy-personal-mcp) |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | no UI |
| **UI: Responsiveness at target viewports** | ☑ N/A | no UI |

### Stage 4 findings (Supervisor, 2026-11-03)

- P1 process (confidence 100): the implementing agent's report says it did not open `PROJECT_SPEC.md` or `agents/backend.md` (Permanent-Rule startup reads). Impact checked: the guide quoted the Critical Constraints it needed, and the code follows them (hooks exit 0, no network, 0600/0700, no write in the observed repo). No code change; recorded.
- P2 (confidence 75): `_refresh_report` passes the Stop hook's `cwd` as `--repo`. From a linked worktree, `_report_numbers` counts `no_data` against that worktree's Claude project folder, so `no_data` in report.json depends on which checkout refreshed last. Other fields use the shared store and are stable. Suggestion: pass the main checkout root, or drop `no_data` from the object. Not fixed (text report has the same per-cwd meaning; Gate 2a).
- Agent decisions accepted: medians and `on_vs_off_pct` are ints rounded as the text report shows them (AC1); refresh only after a saved note; no back-off for a failing child (cut list).

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
