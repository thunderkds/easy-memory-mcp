**Date**: 2026-10-30
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P2
**Assigned agent**: backend-developer
**Agent guide**: `agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:

1. Read `PROJECT_SPEC.md` (Glossary has the v0.3 terms: Typed prompt, Event, Trigger, Turn, Touched file, Trash)
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/backend.md` in full
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/backend.md`
6. Read `PRD_v0.3.md` (Decision record row for M4) and `BRAINSTORMING_LOG_v0.3.md` (Edge Case Checklist, M4)
7. Read `easy_memory.py` sections: `CITED_PATH`, `cited_files`, `_tracked_files`, `_hash_if_repo_file`, `last_user_prompt`, `save_stop_note` (as changed by HUN-137)

---

## Requirement (Pillar 1 — Adapt the requirement)

Verifier list V-R3 (2026-10-30): note 20261030T135535512-28cf1f25 cites `PRD.md` and `tasks/TASK_GUIDE_T128.md` only because the reply named them as examples; every later edit marks the note CHANGED. Requirement: a precise rule so CHANGED/DELETED mean "the evidence moved". User chose "named and touched" (2026-10-30).

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> A repo file is cited only if the answer names it (today's `CITED_PATH` match) AND the Turn touched it: a `file_path` / `notebook_path` of Read, Edit, Write, MultiEdit or NotebookEdit, a `path` of Grep or Glob, or a path token inside a Bash `command`. Paths are made repo-relative; paths outside the repo root are dropped. Sub-agent (sidechain) tool calls are not counted.

**Out of scope** (what this task explicitly does NOT do):

* Reading sidechain transcripts of sub-agents (accepted gap, grilling).
* The DELETED / NOT-ON-BRANCH flag (that is HUN-139).
* Rewriting notes already saved (user, 2026-10-30: old notes are not rewritten).
* `report_command`, the switch, `INDEX_FLOOR` / `INDEX_MAX_NOTES` / `INDEX_MAX_CHARS` values, `experiments/`, `site/`.

**Requirement Refs**: `PRD_v0.3.md` M4; verifier V-R3.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [X] Restated intent confirmed to match the user's request (by Supervisor, 2026-10-30; rules fixed with the user in requirement grilling)
- [X] Every Acceptance Criterion below traces to the requirement

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: HUN-137 (reuses its Turn boundary).

**Branch**: `v03-m4-touched-cites` from `v03-m2-event-turns`. HUN-139 branches from this branch.

**Merge gate**: PRD v0.2 Gate 2a — do NOT merge into `main` until the sample bar is met and the report is done (user, 2026-10-30: keep the gates). The live hooks run the `main` checkout (PRD v0.2 A9). Merge after HUN-137.

**Entry point**: `save_stop_note` → `cited_files(answer, root, touched)`.

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | An answer that names `a.py` with no tool call on it in the Turn: `files` has no `a.py` | V-R3 "prose only does not cite" |
| 2 | An answer that names `a.py` after a Read of `<root>/a.py` in the Turn: `files` has `a.py` with its sha256 | V-R3 "after Read/Edit does" |
| 3 | Same for Edit, Write, MultiEdit, NotebookEdit, Grep `path`, Glob `path`, and a Bash `command` like `sed -n 1,9p a.py` or `cat "./a.py"` | Bash is 2,721 of \~3,050 file tool calls |
| 4 | A file touched but not named in the answer is not cited | "named and touched" |
| 5 | A tool call before the last Typed prompt does not count | Turn boundary |
| 6 | A path outside the repo root (another worktree, `/tmp`) is not cited | repo-relative only |
| 7 | README states the rule | V-R3 "declared rule" |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | fixture: answer names `a.py`, no tool use | `files == {}` | automated test |
| 2 | fixture: Read `a.py`, answer names it | `files == {"a.py": sha}` | automated test |
| 3 | fixture: Bash `grep -n x src/b.ts`, answer names `b.ts` | `src/b.ts` cited (bare-name rule kept) | automated test |
| 4 | fixture: Read `a.py` before the typed prompt | not cited | automated test |

### Verification Command (exact, runnable)

```bash
python3 -m unittest tests.test_v03_m4_touched_cites && python3 -m unittest discover -s tests
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-138.md` (review sections are never taken from the board).

## Approach

1. Tests first (red) in `tests/test_v03_m4_touched_cites.py`.
2. `_touched_paths(turn_entries, root)` → set of repo-relative paths: tool `input` fields listed above; for Bash, run `CITED_PATH` over the `command` string and normalise each hit.
3. `cited_files(text, root, touched)`: keep today's matching, then keep a hit only if its resolved path is in `touched`. Keep the old signature working for `redact` and any other caller (default `touched=None` = today's rule) — check callers first.
4. README rule paragraph.

---

## Edge Case Checklist

- [ ] Edit/Write paths are absolute: make them repo-relative with `os.path.realpath` on both sides
- [ ] Bash paths quoted, `./x`, `x:12`; globs (`*.py`) touch nothing
- [ ] Bare name in the answer (`b.ts`) resolved by the tracked-file rule, then checked against `touched`
- [ ] A Turn with no tool calls (agent hand-back) cites nothing
- [ ] A large transcript: only the Turn's entries are parsed (NFR-001, 2 s)
- [ ] `plugin/easy_memory.py` is byte-identical to `easy_memory.py` in the same commit (`tests/test_plugin.py`)
- [ ] Every hook path still exits 0 and prints nothing on error (NFR-004)

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| `easy_memory.py` | `_touched_paths`, `cited_files`, `save_stop_note` |
| `tests/test_v03_m4_touched_cites.py` | new |
| `README.md` | citation rule |
| `plugin/easy_memory.py` | copy of `easy_memory.py` |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| `experiments/`, `site/`, `docs/RELEASE_v0.1.0.md` | out of scope |
| `report_command`, switch code, `INDEX_*` values | measurement code (PRD v0.2 Gate 2a) |
| any `~/.easy-memory/` store, user's real `~/.claude*` | tests use a throwaway `EASY_MEMORY_HOME` / config dir |
| `agents/`, `skills/`, `.claude/` | the repo's own dev kit |

## Test Plan

`python3 -m unittest tests.test_v03_m4_touched_cites`. Then `python3 -m unittest discover -s tests` (full suite, 434 tests at `cb876eb`).

## Completion Checklist

- [ ] Tests written first and failing, then passing
- [ ] Full suite passes, output pasted
- [ ] README updated where an AC says so
- [ ] Not merged into `main` unless the Merge gate above is open
- [ ] Report: `Status: done` with commits, or `Status: blocked` + `Question:`