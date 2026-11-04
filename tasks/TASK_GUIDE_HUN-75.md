**Date**: 2026-10-28
**Complexity Level**: C2
**Risk Level**: Medium
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
5. Note the **Complexity Level** above and apply the matching process (brainstorm / decompose / verify depth) from the Complexity matrix in your role guide (`agents/backend.md`)
6. **C2/C3 or multi-file tasks only**: read `memory/codebase-map.md` if it exists (it does not yet: the repo has only `experiments/` and, from HUN-74 on, `easy_memory.py`)
7. Also read `PRD.md` (the Requirement Refs below) and `BRAINSTORMING_LOG.md` (edge cases E1 to E12)

---

## Requirement (Pillar 1 — Adapt the requirement)

A Claude Code Stop hook must save each turn's final assistant answer as its own note, with the user prompt it answered, the time, and a sha256 hash of every repo file the answer cites. Answers shorter than 200 characters are not saved. A hook failure never blocks the user.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> After every turn that ends with a real answer, a note appears in the store, without the user doing anything and without output or delay the user can notice.

**Out of scope** (what this task explicitly does NOT do):

* Injecting notes into prompts (HUN-77).
* Secret scrubbing (A6: not in scope).
* A prompt stash fallback (add only if transcript reading proves unreliable in HUN-82).

**Requirement Refs** (FR/NFR/US IDs from `PRD.md` this task satisfies):

* US-001
* FR-001: save each turn's answer with prompt, time, cited-file hashes; skip answers under 200 characters
* NFR-001: Stop hook ≤ 2 s on a 7,000-file repo
* NFR-004: any error exits 0, adds nothing, logs locally
* A6: prompt is the last user prompt before the answer; no secret scrubbing

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary (`grill-with-docs` run if terminology was fuzzy)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [ ] All Requirement Refs exist in `PRD.md` and are fully covered by the Acceptance Criteria above

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: HUN-74 — repo_key and write_note must exist

**Entry point**: `hook-stop` subcommand of `easy_memory.py`

---

## Acceptance Criteria

> Each criterion must trace back to the Requirement above (Pillar 1 → Pillar 3 link).

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | Given Stop-hook JSON on stdin with `last_assistant_message` of ≥200 characters and a transcript, exactly one note is written with `prompt`, `answer`, `time`, `session_id` and `files` ({repo-relative path: sha256}). | FR-001 |
| 2 | `prompt` is the last real user message in the transcript (not a tool result). | FR-001, A6 |
| 3 | An answer under 200 characters writes no note. | FR-001 |
| 4 | Input with `stop_hook_active: true` writes no note. | edge E2 |
| 5 | Only files that exist in the repo are cited: a bare name counts only if it is unique among tracked files; a path that does not exist is ignored. | FR-001 |
| 6 | Bad JSON on stdin, an unreadable transcript or an unwritable store: exit code 0, nothing on stdout, one error line in `hook.log` (0600). | NFR-004 |
| 7 | On a 7,000-file repo the hook finishes in ≤ 2 s at p95 over 20 runs (result pasted). | NFR-001 |
| 8 | The hook prints nothing to stdout in every case. | NFR-004, edge E12 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The reviewer fills **Evidence** at Stage 4/5 in `tasks/TASK_REVIEW_T002.md`, copied from
> `templates/TASK_REVIEW_template.md`. A task is **not done** until every row has evidence.
> The implementing agent must NOT be the sole author of its own acceptance test: the Supervisor
> signs off the Success Criteria below as the oracle.

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | Stop JSON with a 500-character answer citing `src/a.py` that exists | one note; `files` has `src/a.py` with its sha256 | unittest |
| 2 | Stop JSON with a 50-character answer | no note, exit 0 | unittest |
| 3 | stdin is `not json` | exit 0, empty stdout, `hook.log` has one line | unittest |

### Verification Command (exact, runnable)

```bash
python3 -m unittest discover -s tests -p 'test_t002*.py' -v
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-75.md` (review sections are never taken from the board).

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_HUN-75.md` (review sections are never taken from the board).

## Approach

**Pattern reference**: `experiments/02-auto-memory/memstore.py` (`cited_files`, `save`, `REF`): port the citation regex and the sha256 logic. Do NOT port `_file_index` (it walks the whole repo); use `git ls-files` for bare-name lookup.

**Vital slice**: Stop JSON → note on disk with prompt, answer and cited-file hashes.
**Cut list**: Stash fallback for the prompt.; De-duplicating near-identical notes.; Secret scrubbing.

`hook-stop` reads stdin JSON, resolves the repo from `cwd`, reads the transcript JSONL from `transcript_path` to find the last user message whose content is plain text (skip entries that hold only `tool_result`). Study one real transcript under the Claude config dir to learn the line shape, then build SYNTHETIC fixtures (never commit real transcripts). Wrap the whole `main` in try/except → exit 0.

**Conventions**: Python 3, standard library only (NFR-005). Tests use `unittest` (pytest is not guaranteed). Follow `docs/claude-md/code-naming-conventions.md`. Tests never touch the real home folder, the real Claude settings, or the real `~/.easy-memory` (use temp dirs and `EASY_MEMORY_HOME` / `CLAUDE_CONFIG_DIR`). Private client repos (Project B, Project A) are read-only benchmark targets: record numbers only, never quote or commit their source.

---

## Edge Case Checklist

- [ ] Last 'user' entry is a tool result: skip back to the real prompt.
- [ ] Slash commands or system reminders inside the user message: keep the text the user typed if separable, else the whole text.
- [ ] Answer cites a path with `:line` suffix.
- [ ] Cited file is huge or binary: hash in chunks; skip files > 5 MB.
- [ ] Repo has 7,000 files: no full-tree walk.
- [ ] Transcript is being written while read (last line partial): ignore a bad last line.
- [ ] stdout stays empty even on success.

---

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| easy_memory.py | add `hook-stop`, citation and transcript helpers |
| tests/test_t002_stop_hook.py | new |
| tests/fixtures/ | new: synthetic transcripts only |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| experiments/\*\* | read-only evidence |
| Anything outside this repo and `EASY_MEMORY_HOME` temp dirs | tests must not touch the real `~/.easy-memory` or Claude settings |

---

## Test Plan

Unit tests with synthetic transcripts and a throwaway git repo. Latency run on Project B is a manual benchmark: record only timings, never quote its source code.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (if Medium/High risk)
- [ ] Lint passes (`python3 -m py_compile easy_memory.py` at minimum)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T002.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working by running it
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review