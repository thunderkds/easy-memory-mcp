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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | `tests/test_t001_store.py` (31 tests), `tests/__init__.py`. AC1 `RepoKeyTest.test_worktree_shares_key_with_main_checkout`; AC2 `test_non_git_folder_uses_real_path_and_does_not_raise`; AC3 `test_creates_note_file_with_private_modes_and_version`; AC4 `test_no_temp_file_left_and_same_second_ids_differ`, `test_temp_file_removed_when_write_fails`; AC5 `test_skips_newer_version_and_corrupt_json`, `test_skips_other_bad_shapes_and_non_json_files`; AC6 `test_repo_folder_is_byte_identical_after_write_and_read`; AC7 `StoreHomeTest` (3 tests) |
| Verification command run | pass | `python3 -m unittest discover -s tests -p 'test_t001*.py' -v` at 2026-10-28T05:02:54Z: `Ran 31 tests in 0.337s` / `OK`. `python3 -m py_compile easy_memory.py`: exit 0. Stable over 5 repeat runs (a first run caught a mkdir race in `_private_dir` under concurrent writers; fixed with a `FileExistsError` catch). |
| Negative cases hold | pass | `v: 99`, `{broken`, list, no `v`, string `v`, bool `v`, `v: 0`, binary, empty file, `.tmp` file, directory named `*.json`: all skipped, no exception. git missing (empty PATH), missing folder, symlink, permissive umask 0, file-as-store-parent and read-only home (`StoreError`, subclass of `OSError`), write failure at rename (no temp left), 60 concurrent writers (60 unique files). |
| verify | pass | Real run (2026-10-28T05:03:01Z, `EASY_MEMORY_HOME` in scratchpad): `repo_key('.')` in the worktree and `repo_key(<main checkout>)` both printed `c5aa0c6dafcc6672`; `write_note` created `realrun/c5aa0c6dafcc6672/notes/20261028T050301391-9e33fb54.json`; `read_notes(<main>)` returned 1 note; modes 700 (3 folders) / 600 (2 files). `python3 easy_memory.py serve` printed `easy-memory serve: not implemented` (stderr), exit 0. Real `~/.easy-memory` was not created. The `verify` skill itself was not invoked: this agent has no Skill tool. Supervisor to run it. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | pass | New files only (`easy_memory.py`, `tests/`), no importers yet; `git status` shows only those plus this review file. The `code-review` skill was not invoked (no Skill tool); self-review done, Supervisor to run it. Risk Low, so no security-review. |
| Full smoke suite still green (no regression) | pass | The repo had no other tests in this worktree (only `experiments/`, untouched); the T001 suite is the whole suite: 31 tests OK. |
| **UI: Visual regression (diff or verdict pasted)** | N/A | No UI (PRD Out of Scope). |
| **UI: Design-system compliance (tokens/colors/typography verified)** | N/A | No UI. |
| **UI: Responsiveness at target viewports** | N/A | No UI. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-10-28T05:01:27Z, before any implementation commit; `tests/` and `easy_memory.py` do not exist):

```
$ python3 -m unittest discover -s tests -p 'test_t001*.py' -v
...
ImportError: Start directory is not importable: 'tests'
exit=1
$ python3 -m py_compile easy_memory.py
[Errno 2] No such file or directory: 'easy_memory.py'   exit=1
$ python3 easy_memory.py
python3: can't open file '.../easy-memory-mcp-wt-HUN-74/easy_memory.py': [Errno 2] No such file or directory   exit=2
```

**AFTER** (2026-10-28T05:02:54Z):

```
$ python3 -m unittest discover -s tests -p 'test_t001*.py' -v
... (31 tests, all ok)
----------------------------------------------------------------------
Ran 31 tests in 0.337s

OK
$ python3 -m py_compile easy_memory.py   -> exit 0
$ python3 easy_memory.py serve           -> "easy-memory serve: not implemented" (stderr), exit 0
```

**DELTA**: Any folder or git worktree now maps to one stable repo key, and notes can be written to and read from `~/.easy-memory/<key>/notes/` as 0600 versioned JSON, without touching the repo.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
