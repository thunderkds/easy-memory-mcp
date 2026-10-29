# TASK_REVIEW — HUN-86: redact command rewrites notes already saved

> Sibling of `tasks/TASK_GUIDE_HUN-86.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_t010_redact.py` class `RedactCommandTest` (19 tests, AC1 to AC7, Stage 4 findings F1 to F5, plus switch off, placeholder, empty store, fail closed, real process); `tests/test_t001_store.py:288` lists the new `redact` subcommand. Targeted run: `python3 -m unittest discover -s tests -p "test_t010*"` printed `Ran 53 tests in 1.348s` / `OK` |
| Verification command run | ☑ pass | `python3 -m unittest discover -s tests -v 2>&1 \| tail -5` printed: `OK (skipped=3)` and `[NFR-001] 7000 files, 20 runs: min=0.071s p50=0.077s p95=0.085s max=0.089s`; 360 tests `ok` (after the Stage 4 security fixes). `python3 -m py_compile easy_memory.py` clean. Before the change the same suite printed `OK (skipped=3)` (same 3 skips). |
| Negative cases hold | ☑ pass | Corrupt JSON, invalid UTF-8, JSON list, wrong field types: reported by note id and error type, skipped, exit 0. Write failure (OSError, os.replace failure): old bytes kept, no `.tmp` left, exit 1, next note still done. Raising redactor: nothing written, exit 1. Output greps clean of every fixture secret (dry run, apply, second apply). Stage 4 security fixes: note deleted or replaced mid-run is not recreated or overwritten (`skipped (changed)`); skipped notes never give "No secrets found" (`N skipped (unreadable)`); names failing `valid_note_id` print as `ascii()` with `skipped (bad name)` and stay untouched; unreadable notes folder prints `redact: cannot read notes (<ExcType>)` and exits 1 (a missing folder still exits 0); a symlink note is skipped and stays a symlink. |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☑ pass | Full suite `OK (skipped=3)`; the `tests/test_t001_store.py` subcommand-table test needed `redact` added (the only edit to an existing test). |
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

**BEFORE**: captured 2026-10-29 07:18:08 UTC (`date -u`: `Thu Oct 29 07:18:08 AM UTC 2026`), worktree `hun-86` at commit 3d9ccdf, before any implementation commit. Temp `EASY_MEMORY_HOME`, temp git repo, one note whose prompt holds the fake key `AKIAIOSFODNN7EXAMPLE`.

```
$ python3 easy_memory.py redact --repo REPO
usage: easy_memory [-h]
                   {hook-stop,hook-prompt,serve,report,install,uninstall,build-weights,switch} ...
easy_memory: error: argument command: invalid choice: 'redact' (choose from hook-stop, hook-prompt, serve, report, install, uninstall, build-weights, switch)
exit=2
$ grep -c AKIAIOSFODNN7EXAMPLE <note file>
1
```

The command is rejected as unknown (exit 2) and the saved note still holds the secret.

**AFTER**: captured 2026-10-29 07:21:31 UTC (`date -u`), same temp store and note as BEFORE, after the change.

```
$ redact            (dry run)
20261029T071808460-c769bfb7: aws_access_key 1
Found secrets in 1 note(s). Run again with --apply to rewrite them.
exit=0
$ redact --apply
20261029T071808460-c769bfb7: aws_access_key 1
Rewrote 1 note(s).
exit=0
$ redact --apply
No secrets found in 1 note(s).
exit=0
$ redact            (dry run)
No secrets found in 1 note(s).
exit=0
prompt now: deploy with [REDACTED:aws_access_key] please
grep -c AKIAIOSFODNN7EXAMPLE <note>  -> 0
mode: -rw-------
```

**DELTA**: A user can now list which saved notes hold a secret without seeing it, then remove it in place with one `redact --apply`; a second run changes nothing.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/HUN-86.jsonl`, never the
implementing agent alone]
