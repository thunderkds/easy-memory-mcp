# TASK_GUIDE — HUN-197: report --json writes report.json for the easy-personal dashboard

**Date**: 2026-11-03
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: backend-developer
**Agent guide**: `agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:

1. Read `PROJECT_SPEC.md` (Critical Constraints: never write inside an observed repo; hooks exit 0; no network; 0600/0700)
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/backend.md` in full
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/backend.md`
6. Read `PRD_v0.4.md` (FR-015, Decision record, XR-1)
7. Read `easy_memory.py` sections: `report_command`, `read_session_usage`, `_first_prompt_lines`, `_median_text`, `_store_size`, `REPORT_MIN_SESSIONS`, `TOO_FEW`, `hook_stop`, `_atomic_write`, `_private_dir`, `_take_build_lock`, `_start_background_build`, `main` (argument parsing)
8. Read `tests/test_t007_report.py` (fixtures and helpers you must reuse)

---

## Requirement (Pillar 1 — Adapt the requirement)

User, 2026-11-03: "as a memory mcp, you can analyze, collect and give the easy-personal the number and analyze number to show on the dashboard", then "yes, let go" to the plan: easy-memory writes the on/off comparison to a file, and easy-personal reads it (no MCP call, metadata only).

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> `easy_memory.py report --json [--repo R]` prints the same comparison the text `report` prints, as one JSON object (FR-015 fields), and writes it to `<store>/report.json` with `_atomic_write` (0600). The text `report` output stays byte-for-byte the same. The Stop hook, after saving the note, starts a detached `report --json` for the repo only when `report.json` is missing or older than 1 hour and it can take `<store>/report.lock` (same O_EXCL + 10-minute-stale rule as the weights lock). The hook never waits for it and still exits 0 on any error.

**Out of scope** (what this task explicitly does NOT do):

* What the report measures: grouping (auto/forced), token sums, the 10-session bar, the "note opened" rule. Gate 2a: measurement code must not change its numbers.
* A new MCP tool or a change to `memory_*` tools.
* Any code in the easy-personal-mcp repo (XR-1 is a separate task on that repo's board).
* `INDEX_*` values, ranking, note schema, `experiments/`, `site/`.

**Requirement Refs**: `PRD_v0.4.md` FR-015; `PRD.md` FR-007.

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [X] Restated intent confirmed to match the user's request (by Supervisor, 2026-11-03; plan approved by the user "yes, let go")
- [X] Every Acceptance Criterion below traces to the requirement

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: none.

**Branch**: `v04-report-json` from `main`.

**Merge gate**: none beyond Stage 4 + `/verify` (additive file; text report unchanged). The user merges.

**Entry point**: `easy_memory.py report --json`; `easy_memory.py hook-stop`.

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | `report --json` prints one JSON object with exactly the FR-015 fields and `v` = 1; each number equals the text report's number for the same fixture store (on/off sessions, medians, turns, note opened, counts, store size) | FR-015 "every number equals" |
| 2 | `report --json` writes `<store>/report.json`, mode 0600, by atomic rename; the printed object and the file are equal | FR-015 |
| 3 | With fewer than 10 sessions in a group, `too_few` is true and `on_vs_off_pct` is null; with 10+ in both, `on_vs_off_pct` equals the text report's `on vs off` value (rounded the same way, as a number) | FR-015, FR-007 |
| 4 | No prompt text, answer text, note text, session id or file path appears in the JSON (test with a fixture whose prompt, answer and session id are unique marker strings; assert none is in the file) | Decision: metadata only |
| 5 | Plain `report` output is byte-identical before and after this change on the test_t007 fixtures | Decision: text output unchanged |
| 6 | `hook-stop` starts a detached `report --json` when `report.json` is missing or older than 1 h; does not start one when it is fresh or `report.lock` is held (and not stale); never waits; exits 0 and prints nothing when the spawn fails | FR-015 refresh rule, NFR-001, NFR-004 |
| 7 | Empty store / no `prompts.log`: `report --json` still prints and writes a valid object (counts 0, medians null, `too_few` true) and returns 0 | FR-015 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | test_t007 fixture store + synthetic Claude logs | JSON numbers = text numbers | automated test |
| 2 | 10 on + 10 off sessions | `too_few` false, `on_vs_off_pct` = text value | automated test |
| 3 | marker strings in prompt/answer/session id | none in `report.json` | automated test |
| 4 | stale / fresh / locked `report.json` | spawn / no spawn / no spawn (Popen mocked) | automated test |
| 5 | real run on this repo's store | `report.json` exists, 0600, valid; text report unchanged | real run, output pasted |

### Verification Command (exact, runnable)

```bash
python3 -m unittest tests.test_v04_report_json && python3 -m unittest discover -s tests
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-197.md` (review sections are never taken from the board).

## Approach

1. Tests first in `tests/test_v04_report_json.py` (reuse `tests/test_t007_report.py` helpers).
2. Split `report_command` into a pure function that returns the numbers (a dict) and the existing printer that formats them. The printer must produce the same text as today.
3. `--json`: build the FR-015 object from that dict, print it, write it with `_atomic_write`.
4. Refresh: a `report.lock` taken like `_take_build_lock`, a `_start_background_report(repo)` like `_start_background_build` (released by the child with a `--release-lock` flag or equivalent), called at the end of `save_stop_note`'s happy path or in `hook_stop` after it, inside the existing try.
5. Copy `easy_memory.py` to `plugin/easy_memory.py` (byte-identical, `tests/test_plugin.py`).
6. README: one short section "report.json (for easy-personal)" listing the fields and the refresh rule.

---

## Edge Case Checklist

- [ ] The child process must not inherit stdin/stdout/stderr (DEVNULL), `start_new_session=True`
- [ ] A dead child leaves a lock: a lock older than 10 minutes is replaced
- [ ] `report.json` older than 1 h by mtime; a future mtime counts as fresh (no spawn loop)
- [ ] JSON numbers are ints (medians may be .5: keep them as the text report computes, a number, not a string)
- [ ] `--repo` path resolution matches the text report (`_repo_root`, `repo_key`)
- [ ] The Stop hook's 2 s budget: the spawn check is one `stat` + one `open`; measure it in a test
- [ ] Every hook path still exits 0 and prints nothing on error (NFR-004)
- [ ] `plugin/easy_memory.py` is byte-identical to `easy_memory.py` in the same commit

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| `easy_memory.py` | report split, `--json`, background refresh |
| `plugin/easy_memory.py` | copy of `easy_memory.py` |
| `tests/test_v04_report_json.py` | new |
| `README.md` | report.json section |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| `experiments/`, `site/`, `docs/RELEASE_*` | out of scope |
| `INDEX_*` values, scorer, note schema, switch code | Gate 2a |
| any real `~/.easy-memory/` store, user's real `~/.claude*` | tests use a throwaway `EASY_MEMORY_HOME` / `CLAUDE_CONFIG_DIR` (the real run in Success Criterion 5 only reads and writes this repo's own `report.json`) |
| `agents/`, `skills/`, `.claude/` | the repo's own dev kit |
| the easy-personal-mcp repo | XR-1, separate board |

## Test Plan

`python3 -m unittest tests.test_v04_report_json`. Then `python3 -m unittest discover -s tests` (full suite).

## Completion Checklist

- [ ] Tests written first and failing, then passing
- [ ] Full suite passes, output pasted
- [ ] README updated
- [ ] Not merged into `main`
- [ ] Report: `Status: done` with commits, or `Status: blocked` + `Question:`

## Demonstration

BEFORE / AFTER command (run in the worktree, against this repo's own store): `python3 easy_memory.py report --json; echo "exit=$?"; ls -l ~/.easy-memory/c5aa0c6dafcc6672/report.json`. BEFORE is expected to show the `--json` flag rejected and no `report.json`.
