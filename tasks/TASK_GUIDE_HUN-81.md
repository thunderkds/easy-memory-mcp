**Date**: 2026-10-28
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
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

An MCP server must offer memory_search(query), memory_read(id), memory_list() and memory_forget(id). The agent must be able to open a listed note without a permission prompt. The `mcp` SDK is not available, so the server speaks the protocol itself over stdio.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> Inside a Claude Code session the agent (or the user) can search, open, list and forget notes through MCP, and opening a listed note never triggers a permission prompt.

**Out of scope** (what this task explicitly does NOT do):

* Editing notes (PRD Out of Scope).
* Any transport except stdio.
* Resources, prompts, sampling.

**Requirement Refs** (FR/NFR/US IDs from `PRD.md` this task satisfies):

* US-004
* FR-005: four tools
* FR-004: open a listed note without a permission prompt
* A3: decided by test here
* NFR-005: stdlib only
* NFR-004: never crash the session

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary (`grill-with-docs` run if terminology was fuzzy)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [ ] All Requirement Refs exist in `PRD.md` and are fully covered by the Acceptance Criteria above

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: HUN-74 — store; HUN-79 — installer to extend

**Entry point**: `serve` subcommand of `easy_memory.py`

---

## Acceptance Criteria

> Each criterion must trace back to the Requirement above (Pillar 1 → Pillar 3 link).

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | `serve` answers `initialize` (echoing the client's protocol version when supported), accepts `notifications/initialized`, answers `tools/list` with the four tools and JSON schemas, and `tools/call`; an unknown method returns a JSON-RPC error; nothing but JSON-RPC messages is written to stdout. | FR-005 |
| 2 | The repo is the server process's cwd (Claude Code starts the server in the project folder). | FR-005 |
| 3 | `memory_search(query)` returns the same index lines as the prompt hook; `memory_read(id)` returns the full note plus changed/deleted flags; `memory_list()` returns the newest notes (default 20) for this repo; `memory_forget(id)` deletes that note. | FR-005, US-004 |
| 4 | An id with a path separator, `..` or any character outside `[A-Za-z0-9._-]` is rejected for read and forget; nothing outside the notes folder can be read or deleted. | security |
| 5 | `install` also registers the server at user scope (via `claude mcp add --scope user easy-memory -- <python> <path> serve`; `--dry-run` prints the command) and adds the allow rule `mcp__easy-memory` to `permissions.allow`; `uninstall` removes both. | FR-008, A3 |
| 6 | A3 test, pasted as evidence: in a fresh `claude -p` session in a test repo with a saved note, asking the agent to open that note by id ends with the note content in the answer and an empty `permission_denials` list. If it fails, try the alternative (Read of the note path with the store in `permissions.additionalDirectories`) and report which one works. | FR-004, A3 |
| 7 | Malformed JSON-RPC input does not crash the server. | NFR-004 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The reviewer fills **Evidence** at Stage 4/5 in `tasks/TASK_REVIEW_T008.md`, copied from
> `templates/TASK_REVIEW_template.md`. A task is **not done** until every row has evidence.
> The implementing agent must NOT be the sole author of its own acceptance test: the Supervisor
> signs off the Success Criteria below as the oracle.

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | `tools/list` request | four tools with `inputSchema` | unittest (subprocess over pipes) |
| 2 | `memory_read` with id `../../etc/passwd` | error result, no file read | unittest |
| 3 | `memory_forget` of an existing id | note file gone, a second call returns 'not found' | unittest |

### Verification Command (exact, runnable)

```bash
python3 -m unittest discover -s tests -p 'test_t008*.py' -v
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-81.md` (review sections are never taken from the board).

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_HUN-81.md` (review sections are never taken from the board).

## Approach

**Pattern reference**: None — no prior art in this repo. Protocol reference: [https://modelcontextprotocol.io](<https://modelcontextprotocol.io>) (stdio transport: newline-delimited JSON-RPC 2.0); read the current spec for the version you answer with.

**Vital slice**: `initialize`, `tools/list`, `tools/call` for four tools, over stdio.
**Cut list**: Resources and prompts.; Progress notifications.; HTTP transport.

Read lines from stdin, `json.loads`, dispatch, write one JSON line per response with `flush`. Log to a file, never to stdout. Reuse the HUN-77 rendering for search and the HUN-74 store for the rest.

**Conventions**: Python 3, standard library only (NFR-005). Tests use `unittest` (pytest is not guaranteed). Follow `docs/claude-md/code-naming-conventions.md`. Tests never touch the real home folder, the real Claude settings, or the real `~/.easy-memory` (use temp dirs and `EASY_MEMORY_HOME` / `CLAUDE_CONFIG_DIR`). Private client repos (orderly, tapchat) are read-only benchmark targets: record numbers only, never quote or commit their source.

---

## Edge Case Checklist

- [ ] Client sends `ping`: answer with an empty result.
- [ ] Requests with no `id` are notifications: no reply.
- [ ] stdout buffering: flush after each message.
- [ ] Very large note: cap `memory_read` output at 20,000 characters and say so.
- [ ] Two servers (two sessions) at once: safe because notes are separate files.
- [ ] Server started outside a git repo: use the real path key.

---

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| easy_memory.py | add `serve`, tool handlers, extend `install`/`uninstall` |
| tests/test_t008_mcp.py | new |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| The user's real `~/.claude.json` in tests | use a temp config dir and a fake `claude` command |
| experiments/\*\* | read-only evidence |

---

## Test Plan

Subprocess tests that speak JSON-RPC over pipes; installer tests with a stub `claude` on PATH; the A3 test is a real run, evidence pasted.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (if Medium/High risk)
- [ ] Lint passes (`python3 -m py_compile easy_memory.py` at minimum)
- [ ] Tests written AND pass — output pasted into `tasks/TASK_REVIEW_T008.md`'s Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run — feature confirmed working by running it
- [ ] `memory/MEMORY.md` updated (if new patterns or feedback learned)
- [ ] Supervisor notified: task ready for Stage 4 review