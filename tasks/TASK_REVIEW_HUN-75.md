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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | pass | `tests/test_t002_hook_stop.py` (53 tests; AC1-AC8 each tagged in test comments). Against the old stub the same file failed: `FAILED (failures=24, errors=20)`. Also edited `tests/test_t001_store.py`: the stub-loop test now skips `hook-stop` (no longer a stub). |
| Verification command run | pass | 2026-10-28T05:10:28Z `python3 -m unittest discover -s tests -p 'test_t002*.py' -v` ends: `Ran 53 tests in 2.789s` / `OK` / `[NFR-001] 7000 files, 20 runs: min=0.053s p50=0.057s p95=0.063s max=0.063s`. Second run: p95=0.063s. Limit is 2.0 s. |
| Negative cases hold | pass | Covered by tests: answer 199 chars (no note) vs 200 (note); `stop_hook_active`; bad JSON, empty stdin, `[]`; missing/unreadable/folder transcript; `notes` path is a file; read-only store home; `--bogus` arg exits 0 for `hook-stop` but still 2 for `report`; ambiguous bare name; missing path; `../` and symlink out of repo; file > 5 MB; 200,000-char token (regex stays fast). stdout empty on every path (subprocess test, stderr empty on success). |
| verify | pass | The implementing agent had no Skill tool, so `verify` skill was NOT run; a real run was done instead (see Demonstration AFTER): `hook-stop` wrote one note with the right prompt and sha256, stdout empty, exit 0, file mode 0600 — pass. Supervisor still owns `/verify`. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | pass | Self-review only (no `code-review` skill available). Reviewed `easy_memory.py` diff (new helpers + `hook_stop` + `main` argparse guard) and the two test files. `write_note`/`repo_key` unchanged. Not reviewed: other subcommands (still stubs). |
| Full smoke suite still green (no regression) | pass | `python3 -m unittest discover -s tests` -> `Ran 84 tests in 3.107s` / `OK`. `python3 -m py_compile easy_memory.py` ok. |
| **UI: Visual regression (diff or verdict pasted)** | N/A | No UI: backend hook only. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | N/A | No UI. |
| **UI: Responsiveness at target viewports** | N/A | No UI. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-10-28T05:07:50Z, on branch feat/HUN-75 before any implementation commit; synthetic repo with `src/a.py`, a transcript with one user prompt, and a 600-character answer citing `src/a.py`):

```
$ EASY_MEMORY_HOME=<tmp>/before/store python3 easy_memory.py hook-stop < in.json
easy-memory hook-stop: not implemented
exit=0
$ ls -R <tmp>/before/store
ls: cannot access '<tmp>/before/store': No such file or directory
```

The hook is a stub: no note, not even the store folder, is created.

**AFTER** (2026-10-28T05:10:40Z, same input, after the change):

```
$ EASY_MEMORY_HOME=<tmp>/before/store python3 easy_memory.py hook-stop < in.json
(no output)  exit=0
$ find <tmp>/before/store -type f
store/be8f583b66d1af14/meta.json
store/be8f583b66d1af14/notes/20261028T051041014-d9801bc8.json   (mode -rw-------)
note: prompt "what does src/a.py do?", session_id "s1", time "2026-10-28T05:10:41Z",
      files {"src/a.py": "98752ee28d5484bdc2814fb70adb6a0b2fb31f6a9b8ee7ae81fd2fc9cf300b3b"}
$ (cd repo && git status --porcelain)    -> empty (repo untouched)
```

NFR-001: 7,000-file synthetic repo, 2,001-line transcript, answer with 1 direct and 4 bare-name citations (3 need `git ls-files`), 20 subprocess runs: min=0.053s p50=0.057s p95=0.063s max=0.063s (limit 2.0 s).

**DELTA**: After a turn that ends with an answer of 200 or more characters, a Stop hook now saves a note (prompt, answer, time, cited-file hashes) in the store, silently, in about 60 ms.

**WITNESS**: backend-developer agent ran both captures on 2026-10-28 (05:07:50Z and 05:10:40Z); independent witness to be derived from `memory/event-trace/HUN-75.jsonl` by the Supervisor.
