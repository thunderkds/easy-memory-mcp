# BRAINSTORMING_LOG.md
**Generated**: 2026-10-28
**Task / Context**: Phase 0 → Stage 0.5b, easy-memory-mcp prototype (PRD gate PASS 2026-10-28)
**Skill**: `Skill({ skill: "brainstorming" })`
**Tier**: Standard (stack fixed by the PRD; three open design choices)

---

## The Problem Space

Turn experiment 03's "index" method into a real tool: a Stop hook saves one note per turn, a UserPromptSubmit hook injects a ≤2,500-character index, an MCP server gives read/search/list/forget, and a report compares memory on vs off. Hard limits: stdlib only (NFR-005), hook adds ≤1 s p95 on a 7,000-file repo (NFR-001), a hook never blocks the prompt (NFR-004), nothing written inside a repo (FR-002).

Three design choices are open. They are the real content of this log:
1. **D1 Word weights (G3).** FR-003 scores a prompt against notes with word weights from the repo's own files.
2. **D2 MCP server.** FR-005 needs an MCP server, but NFR-005 forbids dependencies except the SDK.
3. **D3 How the agent opens a note (A3).** MCP `memory_read` or plain `Read` (FR-004: no permission prompt).

## Verified facts (claim verification gate)

| Claim | Source | Result |
|---|---|---|
| Building word weights is too slow to run per prompt | Timed `experiments/02-auto-memory/memstore.py:build_idf` on `<Project B checkout>` (7,835 tracked files) | **16.5 s** to build, **16 MB** JSON, **0.3 s** just to load it. NFR-001 is 1 s. |
| Stop hook gets the final answer | code.claude.com/docs/en/hooks | `last_assistant_message` is documented for Stop. Stop input has no user prompt, so the saved prompt must come from `transcript_path` or from a UserPromptSubmit-time stash. |
| UserPromptSubmit gets the prompt and can add context | same | Input has `prompt`. Output `hookSpecificOutput.additionalContext` (cap 10,000 characters per string); plain stdout also becomes context. Default timeout 30 s on this event. |
| Exit codes | same | Exit 0 = success. Exit 2 **blocks** the prompt. Any other non-zero = non-blocking. NFR-004 means: catch everything, exit 0. |
| MCP tools can be pre-approved | code.claude.com/docs/en/permissions.md | Allow rule `mcp__<server>` or `mcp__<server>__*` in `permissions.allow`. The installer (FR-008) writes it. |
| Read in an added directory needs no prompt | same | Read-only tools need no approval inside the working directory and `additionalDirectories`. |
| The MCP SDK is not installed | `python3 -c "import mcp"` → ModuleNotFoundError (Python 3.14.4) | A `pip install mcp` would be a first dependency; the server cannot assume it. |
| Experiment 03 stored full notes inside the repo | `experiments/03-precision/RESULTS.md`: notes in `.agent-memory/` | The prototype stores them in `~/.easy-memory/` (FR-002), so D3 is new, not tested. |

## Questions for the User

1. Which path (A, B or C) do you want? (Asked after this log.)
2. Is it acceptable that the very first prompt in a never-seen repo gets no index while the word weights build in the background? (Recommended: yes; see edge case E1.)

---

## Alternative Paths

| Option | Name | Summary | Invasiveness | Code Volume | Regression Risk | Recommended? |
|--------|------|---------|-------------|------------|----------------|--------------|
| A | Faithful port | Port experiment 03 as is. Official `mcp` SDK. Full word-weight file rebuilt when the repo's `HEAD` changes. | Low | ~700 lines + 1 dependency | Medium (latency) | |
| B | SQLite + FTS5 | Notes and a full-text index in one stdlib `sqlite3` file. BM25 replaces repo-derived word weights. | Medium | ~600 lines | **High** (changes the validated scorer) | |
| C | Single-file, stdlib only | One `easy_memory.py` with subcommands. Hand-written stdio MCP (4 tools). Compact word-weight file built in the background. | Low | ~450 lines | Low | ✅ Yes |

### Option A — Faithful port
**Approach**: Keep `memstore.py` and `precision.py` almost unchanged. Hooks are two scripts. The server uses the `mcp` SDK. Word weights are rebuilt when `HEAD` changes.
**Pros**: Closest to the evidence (−28% tokens). Least new logic.
**Cons**: Breaks NFR-005's spirit: a dependency that must be installed into whatever Python the hook runs on. The 16 MB weight file costs 0.3 s per prompt to load.
**Why it might fail**: Rebuild at 16.5 s runs inside a hook with a 1 s budget. If it runs inline, the first prompt after every commit stalls. If the SDK is missing or its version changes, the MCP server fails to start and US-004 is silently gone.

### Option B — SQLite + FTS5
**Approach**: One database per repo. FTS5 `bm25()` ranks notes. No separate weight file.
**Pros**: Fast queries. Atomic writes and concurrency come free (NFR-006). Easy `memory_list` and `forget`.
**Cons**: The PRD says A5: scoring carried over unchanged. FTS5 BM25 weights words by the *notes*, not the repo, and with few notes the weights are poor. The 0.12 floor has no meaning on a different scale.
**Why it might fail**: All the evidence (−28%, 0 misled) is for the repo-weight scorer. A new scorer needs a new experiment before the numbers can be trusted. FTS5 may also be missing from some Python builds.

### Option C — Single-file, stdlib only
**Approach**: One module, subcommands `hook-stop`, `hook-prompt`, `serve`, `report`, `install`, `uninstall`. Notes are one JSON file each, written by temp file + rename. MCP stdio is hand-written (newline-delimited JSON-RPC: `initialize`, `tools/list`, `tools/call`). Word weights: built in a detached background process, stored compact (words that appear in only one file dropped; target ≤2 MB, to verify), rebuilt when `HEAD` changed **and** the file is more than a day old. The hook only reads the file. If it does not exist yet, the hook adds nothing and starts the build.
**Pros**: Satisfies NFR-005 literally. Same scorer as experiment 03, so A5 holds. The hook cost is one small file read.
**Cons**: The hand-written MCP must track the protocol (small surface: 3 methods, 4 tools). Stale weights for up to a day (harmless: weights change slowly).
**Why it might fail**: Protocol drift in a future Claude Code version. A compact weight file may change scores slightly, so the 0.12 floor must be re-checked against experiment 03 answers (a 30-minute offline test, no new agent runs).

---

## 50% Rule Check

Option C with half the code: drop the MCP server and let the agent open `~/.easy-memory/.../note.md` with `Read` (via `additionalDirectories`). That removes ~150 lines and the protocol risk. It also removes `memory_search`, `memory_list` and `memory_forget` (FR-005, US-004), which the PRD lists as a requirement. **Cut list for the vital slice** (not requirements, so they stay in): none. If the user wants to cut, FR-005 is the candidate: ship hooks + report first, add the server as a later task. I recommend keeping FR-005 but making it its own task, so hooks ship first.

## Edge Case Checklist (goes into each TASK_GUIDE)

- E1 First prompt in a new repo: no weight file yet. Add nothing, start the background build, never block.
- E2 Stop hook with `stop_hook_active: true` or an answer under 200 characters: save nothing (and never loop).
- E3 Prompt text is not in Stop input: read it from `transcript_path`, last real user message; fall back to a stash written by the UserPromptSubmit hook for this `session_id`. Skip the note if neither works.
- E4 Two sessions in one repo write at once: unique file names (timestamp + session id), temp file + atomic rename.
- E5 Cited file deleted or renamed since saving: flag "deleted", not an error.
- E6 Worktree: store key is the git common dir (A1). A note saved on another branch shows changed-file flags against *this* worktree.
- E7 Repo has no git: key by the real path of the folder; log once, do not fail.
- E8 Index text over 2,500 characters: drop the lowest-scoring lines, never cut a line in half.
- E9 `HOME` not writable or store corrupt: hook exits 0, adds nothing, logs to `~/.easy-memory/hook.log`.
- E10 Note content contains text that looks like instructions: index header says notes are data (FR-004); the hook never puts note text outside that frame.
- E11 `auto` day flips while a session is open: the report uses the state logged at the session's first prompt (G4).
- E12 Hook output must be exactly one JSON object or plain text; any stray print corrupts it.

## Surgical Scope

Should be created: `src/easy_memory/` (or single `easy_memory.py`), `tests/`, `PROJECT_SPEC.md`, `PROJECT_KANBAN.md`, `tasks/`.
Must not be touched: `experiments/` (evidence, read-only), the user's other repos, any file inside a repo being observed, `~/.claude*/settings.json` except through the installer's reversible edit (FR-008).
Open for Stage 1: the installer edits the user's real settings files; it needs a dry-run mode and a backup (not yet a requirement; propose adding to FR-008).

---

## Recommended Path

**Option C: single-file, stdlib only.** It keeps the scorer that produced the evidence (A5), meets NFR-005 without a dependency, and removes the one measured threat to NFR-001 (the 16.5 s weight build) by moving it out of the hook. Ship in this order: store + Stop hook → index hook + weight file → installer + switch → report → MCP server.

## Next Actions for Stage 2

1. Offline check: does a compact weight file (≤2 MB) keep scores within tolerance of experiment 03 on its saved answers?
2. Time the `hook-prompt` path on Project B: target p95 < 0.5 s to leave margin for NFR-001.
3. Split FR-005 (MCP server) into its own task after the hooks.
4. Add to FR-008: installer backs up settings and offers `--dry-run`.
5. Decide A3 by test: with the allow rule in place, does `memory_read` run with no prompt in a fresh session?
