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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | `tests/test_t009_smoke.py` (29 tests in 9 classes). AC1+AC2+AC6: `FullCycleTest.test_full_cycle`; AC3: `test_full_cycle_with_sockets_disabled` (socket shim) and `test_no_internet_socket_is_ever_opened_by_hooks_server_or_their_children` (strace -f, no AF_INET); `unshare -rn` variant SKIPS here ("write failed /proc/self/uid_map: Operation not permitted"); AC4: `LatencyTest` (opt-in `EASY_MEMORY_BENCH_REPO`); AC5: `HooksNeverBlockTest`; AC7: whole-suite run below. |
| Verification command run | pass | `python3 -m unittest discover -s tests` (env -i, temp HOME / CLAUDE_CONFIG_DIR / EASY_MEMORY_HOME, fake claude first on PATH), in a fresh `git clone` of commit 45b9185, 2026-10-28T06:14:57Z: `Ran 307 tests in 18.027s` / `OK (skipped=3)`. The 3 skips: unshare variant, orderly latency (opt-in), growth probe (opt-in). |
| Negative cases hold | pass | Garbage stdin (11 shapes x 2 hooks), bad argv, 5 bad transcripts, unwritable store (3 forms), hostile note text, deleted cwd, bare repo, no-commit repo, non-git folder: all exit 0 with empty stdout (`HooksNeverBlockTest`, `RepoShapeTest`). |
| verify | N/A | No Skill tool in this agent. Equivalent done by hand: the full cycle was run for real in subprocesses through the installed hook command strings (`sh -c`), pass. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | pass | Reviewed: all of easy_memory.py (read in full), tests/. Not touched: easy_memory.py, experiments/, PRD, SPEC, KANBAN, memory/. Private repo orderly was only read (see note in report about one `git status`). |
| Full smoke suite still green (no regression) | pass | Same run: 278 earlier tests + 29 new = 307, `OK (skipped=3)`. |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-10-28T06:03:48Z, branch feat/HUN-82, no commit yet; temp CLAUDE_CONFIG_DIR / EASY_MEMORY_HOME / HOME, fake `claude` first on PATH):

```
$ ls tests/test_t009_smoke.py
ls: cannot access 'tests/test_t009_smoke.py': No such file or directory
$ which claude
/tmp/tmp.vHlAFR7vj1/claude            (the fake)
$ python3 -m unittest discover -s tests
Ran 278 tests in 9.943s
OK
[NFR-001] 7000 files, 20 runs: min=0.065s p50=0.067s p95=0.079s max=0.088s   (synthetic repo, from an earlier test)
2026-10-28T06:03:58Z
```

**AFTER** (2026-10-28T06:14:57Z, fresh clone of commit 45b9185):

```
$ python3 -m unittest discover -s tests          (temp HOME / CLAUDE_CONFIG_DIR / EASY_MEMORY_HOME, fake claude)
Ran 307 tests in 18.027s
OK (skipped=3)

$ EASY_MEMORY_BENCH_REPO=<orderly> python3 -m unittest -v tests.test_t009_smoke.LatencyTest    (06:13:11Z)
[HUN-82 NFR-001] tracked_files=7831 weights_files=11380 weights_bytes=1687839 build_seconds=13.0 notes=200
[HUN-82 NFR-001] hook-prompt runs=50 p50=0.202s p95=0.212s max=0.214s runs_with_index=50 max_index_chars=2066
[HUN-82 NFR-001] hook-stop   runs=20 p50=0.061s p95=0.066s max=0.067s
[HUN-82 NFR-001] repo_unchanged=True hook_log_bytes=0
Ran 1 test in 24.935s   OK

$ tests/bench_t004.py --repo <orderly> --notes 200 --runs 50      (cross-check, 06:13:46Z)
notes=200 runs=50 p50=0.202s p95=0.212s max=0.212s mean=0.203s

$ HUN82_GROWTH_PROBE=1 python3 -m unittest tests.test_t009_smoke.StoreGrowthProbeTest     (DEFECT PROBE, fails by design)
[HUN-82 growth probe] notes=4000 hook-prompt p50=1.384s max=1.416s
AssertionError: 1.415597881999929 not less than 1.0 : NFR-001: hook-prompt must add at most 1 s
```

**DELTA**: The owner now has an independent, repeatable end-to-end check of the whole prototype (install, save, inject, MCP read, report, uninstall), of private modes, no network, never-block hooks and an untouched repo, plus measured latency on a 7,835-file private repo.

**WITNESS**: qa-expert agent (did not write easy_memory.py), 2026-10-28, trace file `.claude/hooks/.state/active_task` = HUN-82.
