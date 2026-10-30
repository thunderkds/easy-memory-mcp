# TASK_REVIEW — HUN-136: A saved note is found by memory_search within 1 s of the Stop hook

> Sibling of `tasks/TASK_GUIDE_HUN-136.md`. Filled by the reviewer at Stage 4/5.

---

## Auto decisions

Mode: auto
1. Spawn model sonnet for this task — FACT: PROJECT_SPEC.md:97 "| claude | `claude` | haiku-5-5 | sonnet-5-5 | sonnet-5-5 | opus-5-5 |"
2. Not merged to `main` by the Supervisor although the request said "merge to main after done" — RULE: `docs/claude-md/tracks.md` `### Never in auto mode` "merge or push"
Checks: tests `python3 -m unittest tests.test_v03_m7_save_search` — `Ran 6 tests` `OK`, save->search 0.077–0.109 s; full suite `python3 -m unittest discover -s tests` — `Ran 440 tests` `OK (skipped=3)`; reviews code-review — 0 P0, 1 P1 (process: partial startup read of `agents/qa.md`, no code change), 0 P2, 1 P3; lane check `lane: C1, 2 files, 173 lines, FITS`; real run: the test itself runs `easy_memory.py hook-stop` then `easy_memory.py serve` as subprocesses (auto-checked, not /verify)
Not done: merge (yours); auto verify: running (T182)

## Code review (Stage 4)

`lane: C1, 2 files, 173 lines, FITS`. Entry point `hook-stop` subprocess: found in the test (`run_tool("hook-stop", …)`).

- P0: none. P2: none.
- P1 (process, confidence 100): the agent's `Startup reads` line says `agents/qa.md (first 60 lines, not all)` — a Permanent-Rule read was partial. No code change follows; recorded.
- P3 (confidence 75): `test_a_query_with_no_shared_word_does_not_find_the_note` does not assert that `hook-stop` saved the note first, so a silent save failure would also pass. Suggestion: assert one note file exists before the search.

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_v03_m7_save_search.py` (new, 6 tests): `SaveSearchTest` (AC1, with and without weights, plus a no-shared-word negative), `PluginSaveSearchTest` (AC2, plugin path, plus old-hooks-defer negative). `Ran 6 tests in 2.256s` `OK` (Supervisor, 2026-10-30T15:48:17Z) |
| Verification command run | ☑ pass | `python3 -m unittest tests.test_v03_m7_save_search && python3 -m unittest discover -s tests` → `Ran 6 tests` `OK`; `Ran 440 tests in 36.878s` `OK (skipped=3)` |
| Negative cases hold | ☑ pass | a query sharing no word returns `No matching notes.`; plugin with old hooks in settings saves no note |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | reviewed `tests/test_v03_m7_save_search.py` and the README paragraph; `easy_memory.py` unchanged (empty diff vs `main`), so no callers to review |
| Full smoke suite still green (no regression) | ☑ pass | `Ran 440 tests` `OK (skipped=3)` (434 before + 6 new) |
| **Companion score (easy-verifier)** | ☑ N/A | not run: test-only change, Risk Low |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | no UI |
| **UI: Responsiveness at target viewports** | ☑ N/A | no UI |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-10-30T15:44:22Z in the worktree, before the test file existed:

```
$ python3 -m unittest tests.test_v03_m7_save_search
    module = __import__(module_name)
ModuleNotFoundError: No module named 'tests.test_v03_m7_save_search'

Ran 1 test in 0.000s
FAILED (errors=1)
```

Prior README "Known limits" paragraph (verbatim): "Known limits: the prompt hook gets slower as notes pile up (about 1 ms per note), and the live check that opening a note causes no permission prompt has not run yet. See [the release page](docs/RELEASE_v0.1.0.md) for the install steps, the rollback plan and the full list."

**AFTER**: run by the Supervisor 2026-10-30T15:48:17Z in the worktree:

```
$ python3 -m unittest tests.test_v03_m7_save_search
test_plugin_note_is_found_at_once_with_word_weights: save->search 0.109 s
test_plugin_note_is_found_at_once_without_word_weights: save->search 0.087 s
test_note_is_found_at_once_with_word_weights: save->search 0.077 s
test_note_is_found_at_once_without_word_weights: save->search 0.078 s
Ran 6 tests in 2.256s
OK
```

**DELTA**: A test now proves a note saved by the Stop hook is found by `memory_search` about 0.1 s later (limit 1 s), on the plain and plugin paths; the README names the outside causes of a late note.

**WITNESS**: Supervisor, 2026-10-30T15:48:17Z (AFTER run above), separate from the implementing qa-expert agent (BEFORE at 15:44:22Z).
