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
6. Read `PRD_v0.3.md` (Decision record row for M3) and `BRAINSTORMING_LOG_v0.3.md` (Edge Case Checklist, M3)
7. Read `easy_memory.py` sections: `_repo_root`, `_head`, `save_stop_note`, `_file_flags`, `_index_line`, `_tool_read`, `GIT_TIMEOUT_SECONDS`

---

## Requirement (Pillar 1 — Adapt the requirement)

Kit list K-R3 (2026-10-30): notes citing a file that exists only on a feature branch show `DELETED:<path>` when read from `main` (e.g. `.claude-plugin/marketplace.json`, only on `feat/t217-easy-memory-plugin-names`). Requirement: record the commit and branch at save; say "not on this branch (saved on <branch>@<sha>)" when that commit still has it; DELETED only when it is gone from the saving branch too.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> At save the note stores `git: {"branch": <name or "">, "commit": <HEAD sha>}` (absent outside git or with no commit). In the index and `memory_read`, a cited file missing from the worktree is `NOT-ON-BRANCH:<path>` followed once per line by `(saved on <branch>@<sha7>)` when the saving branch tip has the path — or, if that branch is gone, when the saved commit has it. Else `DELETED:<path>`. A note without `git` behaves as today.

**Out of scope** (what this task explicitly does NOT do):

* CHANGED across branches (content differs: still CHANGED).
* Citation rule (that is HUN-138).
* Rewriting notes already saved (user, 2026-10-30: old notes are not rewritten).
* `report_command`, the switch, `INDEX_FLOOR` / `INDEX_MAX_NOTES` / `INDEX_MAX_CHARS` values, `experiments/`, `site/`.

**Requirement Refs**: `PRD_v0.3.md` M3; kit K-R3.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [X] Restated intent confirmed to match the user's request (by Supervisor, 2026-10-30; rules fixed with the user in requirement grilling)
- [X] Every Acceptance Criterion below traces to the requirement

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: HUN-138 (stacked: same `save_stop_note`).

**Branch**: `v03-m3-branch-flags` from `v03-m4-touched-cites`.

**Merge gate**: PRD v0.2 Gate 2a — do NOT merge into `main` until the sample bar is met and the report is done (user, 2026-10-30: keep the gates). The live hooks run the `main` checkout (PRD v0.2 A9). Merge after HUN-138.

**Entry point**: `save_stop_note` (writes `git`); `_file_flags` (reads it).

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | A note saved on branch `feat` citing `x.json` (exists only on `feat`), read from `main`: flag `NOT-ON-BRANCH:x.json` with `(saved on feat@<sha7>)`, not `DELETED` | K-R3 acceptance |
| 2 | `x.json` later deleted on `feat` too: `DELETED:x.json` | K-R3 |
| 3 | Branch `feat` deleted, saved commit still has `x.json`: `NOT-ON-BRANCH` | grilling rule |
| 4 | Commit unreachable (gc'd) and branch gone: `DELETED` | grilling rule |
| 5 | Note with no `git` field: flags exactly as today | old notes not rewritten |
| 6 | One `git cat-file --batch-check` call per hook run for all missing files, with `GIT_TIMEOUT_SECONDS`; a git failure or timeout gives `DELETED` and one `hook.log` line, exit 0 | NFR-001, NFR-004 |
| 7 | `tests/bench_t004.py` p95 not worse by more than 10% | NFR-009 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | temp git repo: commit `x.json` on `feat`, save note there, checkout `main` | index line has `NOT-ON-BRANCH:x.json` | automated test (real git in a temp dir) |
| 2 | then `git rm x.json` on `feat` | `DELETED:x.json` | automated test |
| 3 | detached HEAD at save | `git.branch == ""`, commit-only check | automated test |
| 4 | not a git repo | no `git` key; flags as today | automated test |

### Verification Command (exact, runnable)

```bash
python3 -m unittest tests.test_v03_m3_branch_flags && python3 tests/bench_t004.py && python3 -m unittest discover -s tests
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-139.md` (review sections are never taken from the board).

## Approach

1. Tests first (red) in `tests/test_v03_m3_branch_flags.py` with a real temp git repo.
2. Save: `git rev-parse --abbrev-ref HEAD` (`HEAD` → `""`) and `_head(root)`; one extra subprocess in the Stop hook.
3. Read: collect missing paths of all lines first; one `git cat-file --batch-check` with `<branch>:<path>` then `<commit>:<path>` lines as needed; map results back.
4. `_file_flags` signature may take the batch result; keep `_tool_read` and the hook on the same code.

---

## Edge Case Checklist

- [ ] Detached HEAD: branch `""`
- [ ] Shallow clone / gc'd commit: `missing` from batch-check → DELETED
- [ ] Branch names with `/` (`feat/x`) in `<branch>:<path>`
- [ ] The `(saved on …)` text passes through `_quoted`-safe characters only (no `<`, `>`)
- [ ] Worktree of the same repo shares the store: branch of the worktree at save
- [ ] `plugin/easy_memory.py` is byte-identical to `easy_memory.py` in the same commit (`tests/test_plugin.py`)
- [ ] Every hook path still exits 0 and prints nothing on error (NFR-004)

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| `easy_memory.py` | `_git_state`, `save_stop_note`, `_file_flags`, `_index_line`, `_tool_read` |
| `tests/test_v03_m3_branch_flags.py` | new |
| `plugin/easy_memory.py` | copy of `easy_memory.py` |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| `experiments/`, `site/`, `docs/RELEASE_v0.1.0.md` | out of scope |
| `report_command`, switch code, `INDEX_*` values | measurement code (PRD v0.2 Gate 2a) |
| any `~/.easy-memory/` store, user's real `~/.claude*` | tests use a throwaway `EASY_MEMORY_HOME` / config dir |
| `agents/`, `skills/`, `.claude/` | the repo's own dev kit |

## Test Plan

`python3 -m unittest tests.test_v03_m3_branch_flags` and `python3 tests/bench_t004.py`. Then `python3 -m unittest discover -s tests` (full suite, 434 tests at `cb876eb`).

## Completion Checklist

- [ ] Tests written first and failing, then passing
- [ ] Full suite passes, output pasted
- [ ] README updated where an AC says so
- [ ] Not merged into `main` unless the Merge gate above is open
- [ ] Report: `Status: done` with commits, or `Status: blocked` + `Question:`