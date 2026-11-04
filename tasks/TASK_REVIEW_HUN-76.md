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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_t003_weights.py` (42 tests: AC1 to AC5, AC7, edge cases), `tests/parity_t003.py` (AC6). Run 2026-10-28T05:19:42Z: `Ran 42 tests in 1.028s` / `OK`; parity script: `PARITY PASS` (numbers below). |
| Verification command run | ☑ pass | `EASY_MEMORY_EXP03_DIR=<scratch>/exp03/experiments/03-precision python3 -m unittest discover -s tests -p 'test_t003*.py' -v && python3 tests/parity_t003.py` -> 42 tests OK, then: `stores: 18, min-df: 3, floor: 0.12` / `other: floor-set identical for 1290/1296 pairs (99.5%, need 95%); top-5 order identical for 156/162 prompts (96.3%, need 90%); index pick identical for 153/162 prompts; PASS` / `earlier: floor-set identical for 647/648 pairs (99.8%, need 95%); top-5 order identical for 140/144 prompts (97.2%, need 90%); index pick identical for 139/144 prompts; PASS` / `PARITY PASS`, exit 0. (With min-df 2 the same script gave 1295/1296 and 159/162, 648/648 and 143/144.) Without the data folder the script exits 2 with a `data missing` message. |
| Negative cases hold | ☑ pass | Tests: corrupt, newer-version and wrong-shape weights file counts as missing; spawn failure frees the lock and logs; unwritable store returns not-ready and starts nothing; build failure exits 0 and prints nothing on stdout; killed write leaves no partial file; lock of 590 s is respected, lock of 601 s is replaced; 8 threads and 4 processes at once start one build. |
| verify | ☐ N/A | The `verify` skill is not available to this agent (no Skill tool). Real run instead: Project B benchmark (numbers below) and `build-weights` on a synthetic repo, exit 0, file 0600. The Supervisor must run `verify`. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Self-review (no `code-review` skill): `easy_memory.py` (new weights section, `main()` parser for `build-weights`), `tests/test_t001_store.py` (one assertion: the subcommand table now lists `build-weights`). No other caller of the changed code exists yet. |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m unittest discover -s tests` -> `Ran 126 tests` / `OK`. |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | No UI. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | No UI. |
| **UI: Responsiveness at target viewports** | ☐ N/A | No UI. |

**AC2 on Project B** (numbers only; temp `EASY_MEMORY_HOME`; Project B `git status` showed 0 changes before and after): 11,380 source files read. Background build 14.8 s. With `MIN_FILES_PER_WORD = 2` (the rule in the guide's Approach): 3.61 MB, load 0.054 s, which FAILS the 2 MB limit. With `MIN_FILES_PER_WORD = 3` (shipped): 1.688 MB, 107,542 words, load 0.0236 s median (min 0.0213, max 0.0297), `ensure_weights()` with a fresh file 0.023 s median, `ensure_weights()` with no file returned not-ready in 3.4 ms and started the detached build.

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-10-28T05:12:57Z by backend-developer, on branch feat/HUN-76 at main's HEAD, before any implementation commit; temp EASY_MEMORY_HOME, synthetic repo):

```
$ EASY_MEMORY_HOME=<tmp> python3 easy_memory.py build-weights --repo <synthetic repo>
usage: easy_memory [-h]
                   {hook-stop,hook-prompt,serve,report,install,uninstall} ...
easy_memory: error: argument command: invalid choice: 'build-weights' (choose from hook-stop, hook-prompt, serve, report, install, uninstall)
exit=2
(store folder: empty, no weights.json)
$ python3 -c 'import easy_memory; print(hasattr(easy_memory,"ensure_weights"), hasattr(easy_memory,"score"))'
False False
```

**AFTER** (2026-10-28T05:19:53Z, same command, temp EASY_MEMORY_HOME):

```
$ EASY_MEMORY_HOME=<tmp> python3 easy_memory.py build-weights --repo <synthetic repo>
exit=0
-rw------- 1 user user 63 weights.json
{"v":1,"n":1,"head":null,"built_at":1793164793.4667146,"df":{}}
$ python3 -c 'import easy_memory as e; print(hasattr(e,"ensure_weights"), hasattr(e,"score"))'
True True
```

**DELTA**: `build-weights` now writes a compact, atomic weights file (1.7 MB on Project B, loads in 0.024 s) and `ensure_weights()` returns at once while a detached process builds or refreshes it.

**WITNESS**: backend-developer ran both captures on 2026-10-28 (05:12:57Z and 05:19:53Z); Supervisor to confirm from `memory/event-trace/HUN-76.jsonl`.
