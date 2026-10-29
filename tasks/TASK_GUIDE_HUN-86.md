**Date**: 2026-10-29
**Complexity Level**: C2
**Risk Level**: High
**Priority**: P0
**Assigned agent**: backend-developer
**Agent guide**: `agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/backend.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/backend.md`
6. **C2**: read `memory/codebase-map.md` if it exists
7. Read `PRD_v0.2.md` "FR-009 detail", the `redact` command bullet

---

## Requirement (Pillar 1 — Adapt the requirement)

A `redact` command must rewrite notes already saved, using the same patterns as the Stop hook. It is a dry run by default. `--apply` writes. The dry run prints note id, kind and count, never the matched text. It works on decoded fields and writes only changed notes, through `_atomic_write`. Running it twice gives the same bytes. Only stored text changes; cited-file hashes and every other field stay the same.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> The user can see which saved notes hold a secret, without seeing the secret, and then remove it in place with one command. A note with no secret is never rewritten.

**Out of scope** (what this task explicitly does NOT do):

* New patterns (reuse `redact_text` from the previous task).
* Bulk forget or any delete (Gate 1).
* Any MCP tool (the MCP allow rule runs tools with no prompt; this stays CLI only).

**Requirement Refs**:

* US-008, FR-009 (`redact` command), user decision Q3 ("`redact` command, dry-run first", 2026-10-29)

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [ ] All Requirement Refs exist in `PRD_v0.2.md` and are fully covered by the Acceptance Criteria

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: "Stop hook redacts secrets before a note is saved" — `redact_text` must exist.

**Entry point**: `python3 easy_memory.py redact [--repo PATH] [--apply]`

**Build in a worktree** (A9). Nothing merges until the user approves.

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | `redact` with no flag changes no file (mtimes and bytes of every note unchanged) and prints one line per note with a hit: note id, kind, count. | FR-009, Q3 |
| 2 | The dry-run output never contains the matched text (test greps the output for every fixture secret). | FR-009 |
| 3 | `redact --apply` rewrites only notes with a hit; other notes keep their bytes and mtime. | FR-009 |
| 4 | After `--apply`, a second `--apply` gives byte-identical files and reports no hits. | FR-009 |
| 5 | Rewritten notes keep every field except the redacted text (`files`, `time`, `session_id`, ...) and keep mode 0600. | FR-009 |
| 6 | Writes go through `_atomic_write`; a failure mid-run leaves each note either old or new, never partial. | FR-009 |
| 7 | A corrupt note file is reported and skipped; the command goes on with the rest. | robustness |
| 8 | All v0.1 tests still pass. | Gate 0 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The reviewer fills **Evidence** at Stage 4/5 in `tasks/TASK_REVIEW_<ID>.md`, copied from
> `templates/TASK_REVIEW_template.md`. A task is **not done** until every row has evidence.

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | Store with 3 notes, one holding a fake AWS key | dry run lists that note id with `aws_access_key 1`; no file changes | unittest |
| 2 | Same store, `--apply` twice | first run rewrites one note; second run changes nothing | unittest with sha256 of files |
| 3 | A note holding non-ASCII text and a secret | non-ASCII text survives unchanged | unittest |

### Verification Command (exact, runnable)

```bash
python3 -m unittest discover -s tests -v 2>&1 | tail -5
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-86.md` (review sections are never taken from the board).

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_HUN-86.md` (review sections are never taken from the board).

## Approach

**Pattern reference**: the `switch` and `report` subcommands for `--repo` handling; `write_note` / `_atomic_write` for writes.

**Vital slice**: walk the repo's notes folder, decode each note, run `redact_text` on `prompt` and `answer`, print hits, and with `--apply` write the changed notes back.
**Cut list**: A cross-repo `--all` flag; a backup copy of old notes; a JSON output mode.

Re-encode a note exactly the way `write_note` does, so an unchanged note would re-encode to the same bytes. Register the subcommand in `SUBCOMMANDS` and `main` (`easy_memory.py:1537`).

**Conventions**: Python 3, standard library only. `unittest`. `EASY_MEMORY_HOME` temp dirs. Fake fixture secrets only.

---

## Edge Case Checklist

- [ ] Empty store or no notes folder: prints nothing, exit 0.
- [ ] A note being written by a live Stop hook at the same time.
- [ ] Repo with the switch `off`: the command still works (it is not a hook).
- [ ] A note whose text already holds `[REDACTED:...]`.

---

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| easy_memory.py | `redact` subcommand |
| tests/test_t010_redact.py | add command tests |
| README.md | one usage line |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| ranking, index, switch, report code in easy_memory.py | measurement must not change |
| experiments/\*\* | read-only evidence |

---

## Test Plan

Unit tests on a temp store: dry run, apply, idempotency, untouched notes, corrupt note, no secret leak in output. Then the full suite.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Risk High)
- [ ] Lint passes (`python3 -m py_compile easy_memory.py`)
- [ ] Tests written AND pass — output pasted into the TASK_REVIEW Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review