**Date**: 2026-10-28
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P0
**Assigned agent**: common-infrastructure
**Agent guide**: `agents/common-infrastructure.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/common-infrastructure.md`
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth) from the Complexity matrix in your role guide (`agents/common-infrastructure.md`)
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md` if it exists (it does not yet: the repo has only `experiments/` and, from HUN-74 on, `easy_memory.py`)
7. Also read `PRD.md` (the Requirement Refs below) and `BRAINSTORMING_LOG.md` (edge cases E1 to E12)

---

## Requirement (Pillar 1 — Adapt the requirement)

Build the base every other task needs: one module `easy_memory.py` with a subcommand table, a unittest runner, a repo key where git worktrees share one store, and a note store under `~/.easy-memory/` that writes atomically with private permissions.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> A test-covered module exists that turns any folder (or git worktree) into a stable repo key, and writes and reads versioned note files outside the repo, safely.

**Out of scope** (what this task explicitly does NOT do):

* Hooks, scoring, weights, MCP, installer, report (later tasks).
* Locking, retention limits, search.

**Requirement Refs** (FR/NFR/US IDs from `PRD.md` this task satisfies):

* FR-002: store under the home folder, one store per repo, nothing written inside a repo
* NFR-003: files 0600, folders 0700
* NFR-006: atomic write, no lock file
* NFR-007: format version on every note
* NFR-005: Python standard library only
* A1: worktrees share the main repo's store (git common dir)

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary (`grill-with-docs` run if terminology was fuzzy)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [ ] All Requirement Refs exist in `PRD.md` and are fully covered by the Acceptance Criteria above

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: None

**Entry point**: `python3 easy_memory.py` (argparse entry point, subcommand table)

---

## Acceptance Criteria

> Each criterion must trace back to the Requirement above (Pillar 1 → Pillar 3 link).

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | `repo_key(path)` returns the same key for a git main checkout and for a `git worktree` of it. | A1, FR-002 |
| 2 | `repo_key` of a folder that is not a git repo is derived from its real path, and does not raise. | FR-002, edge E7 |
| 3 | `write_note(...)` creates `<home>/<key>/notes/<id>.json` with file mode 0600 and folders 0700; the JSON has `"v": 1`. | FR-002, NFR-003, NFR-007 |
| 4 | The write is a temp file in the same folder plus rename; after success no temp file is left, and two writes in the same second get different ids. | NFR-006 |
| 5 | `read_notes()` skips a note whose `v` is higher than supported and a corrupt JSON file, without raising, and returns the rest. | NFR-007, NFR-004 |
| 6 | After write and read, the observed repo folder is byte-identical to before (nothing written inside it). | FR-002 |
| 7 | The store root can be overridden by the env var `EASY_MEMORY_HOME` (tests use it); default `~/.easy-memory`. | testability |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The reviewer fills **Evidence** at Stage 4/5 in `tasks/TASK_REVIEW_T001.md`, copied from
> `templates/TASK_REVIEW_template.md`. A task is **not done** until every row has evidence.
> The implementing agent must NOT be the sole author of its own acceptance test: the Supervisor
> signs off the Success Criteria below as the oracle.

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | A git repo and a worktree of it | same `repo_key` | unittest |
| 2 | A note file with `v: 99` and a file with `{broken` | both skipped, other notes returned, no exception | unittest |
| 3 | Hash of the repo tree before and after a write | equal | unittest |

### Verification Command (exact, runnable)

```bash
python3 -m unittest discover -s tests -p 'test_t001*.py' -v
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-74.md` (review sections are never taken from the board).

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_HUN-74.md` (review sections are never taken from the board).

## Approach

**Pattern reference**: `experiments/02-auto-memory/memstore.py` (`save`, `load`): imitate the record shape and the plain-JSON-file style, but store outside the repo and add atomic write and a version.

**Vital slice**: `repo_key` plus `write_note` / `read_notes` with permissions and atomic rename.
**Cut list**: File locking (atomic rename is enough, NFR-006).; Retention and cleanup (A4).; Any scoring or search.

Create `easy_memory.py` with `main(argv)` and a dict of subcommands (empty handlers for later tasks print 'not implemented' and exit 0). Resolve the repo key with `git rev-parse --git-common-dir` (absolute); fall back to the real path. Hash the resolved path to a short folder name and keep a `meta.json` with the readable path. Use `os.open(..., 0o600)`, `os.makedirs(mode=0o700)` and `os.replace`.

**Conventions**: Python 3, standard library only (NFR-005). Tests use `unittest` (pytest is not guaranteed). Follow `docs/claude-md/code-naming-conventions.md`. Tests never touch the real home folder, the real Claude settings, or the real `~/.easy-memory` (use temp dirs and `EASY_MEMORY_HOME` / `CLAUDE_CONFIG_DIR`). Private client repos (orderly, tapchat) are read-only benchmark targets: record numbers only, never quote or commit their source.

---

## Edge Case Checklist

- [ ] Symlinked repo path resolves to the same key.
- [ ] `git` missing or not a repo: fall back, never raise.
- [ ] `umask` is permissive: modes still 0600/0700 (set explicitly).
- [ ] Home folder not writable: `write_note` raises a clear error (callers decide to swallow it).
- [ ] Two processes write at once: unique ids (timestamp + random suffix).

---

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| easy_memory.py | new: module, subcommand table, store functions |
| tests/test_t001_store.py | new: tests for every AC |
| tests/**init**.py | new, empty |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| experiments/\*\* | read-only evidence |
| PRD.md, PROJECT_SPEC.md, memory/\*\* | Supervisor-owned |
| .claude/**, skills/**, agents/\*\* | kit files |

---

## Test Plan

Unit tests with `tempfile` and `EASY_MEMORY_HOME`; create a real throwaway git repo and worktree in the temp folder.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (if Medium/High risk)
- [ ] Lint passes (`python3 -m py_compile easy_memory.py` at minimum)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T001.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working by running it
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review