# decisions.md — Cold Tier: Architectural & Infrastructure Decisions

> **Rules**: Supervisor-only writes. Each entry: `### YYYY-MM-DD — Title`, then **Decision**, **Why**, and **Files** (cite paths — the diff-driven pass greps this file by changed file path).

## Architecture

### 2026-10-28 — Implementation path C: single-file, stdlib-only prototype
**Decision**: Build one Python module with subcommands (`hook-stop`, `hook-prompt`, `serve`, `report`, `install`, `uninstall`). Hand-written stdio MCP server (4 tools). Notes are one JSON file each under `~/.easy-memory/`, written by temp file + atomic rename. Word weights come from the repo's own files (as in experiment 03), built in a background process and read by the hook, never built inside it. One note per Stop turn (answer ≥200 chars). Injected index ≤2,500 characters. Worktrees share the main repo's store.
**Why**: Building weights on orderly (7,835 files) took 16.5 s and gave a 16 MB file that takes 0.3 s to load; NFR-001 allows 1 s. The `mcp` SDK is not installed, and NFR-005 forbids dependencies. Keeping experiment 03's scorer keeps its evidence (−28% tokens, 0 misled) valid. Rejected: A (SDK port, latency and dependency), B (SQLite FTS5, changes the validated scorer).
**Files**: `BRAINSTORMING_LOG.md`, `PRD.md`, `experiments/02-auto-memory/memstore.py` (scorer to port), `experiments/03-precision/precision.py` (index to port)

### 2026-10-28 — Word weights keep words found in at least 3 files
**Decision**: `MIN_FILES_PER_WORD = 3` in `easy_memory.py`, not the guide's 2. On orderly, 2 gave a 3.61 MB `weights.json` (limit 2 MB, AC2); 3 gives 1.69 MB, loads in 0.024 s, and passes the parity check (99.5% of score pairs, 96.3% of top-5 orders).
**Why**: AC1 says drop words found in one file, AC2 caps the file at 2 MB; only 3 meets both. The 0.12 floor was not changed.
**Files**: `easy_memory.py`, `tests/parity_t003.py`, `tasks/TASK_GUIDE_HUN-76.md`

### 2026-10-29 — v0.2 plan: redaction only now, everything else gated (Option B2)
**Decision**: Only FR-009 (secret redaction at save, plus a `redact` command, dry-run by default) ships during the v0.1 on/off measurement. The package split (FR-011, package `easy_memory_core/`) is built in a worktree and merged when Gate 1 opens. The portable store key (FR-010) is deferred with sync. Gate 2 splits into 2a (decay, expiry) and 2b (optional embedder in `memory_search` only). Gate 3 (other clients) is removed.
**Why**: A three-agent review found the hooks run live from this checkout, so a merge changes the measured hooks on the next prompt. A key change moves `config.json`, `prompts.log` and `weights.json`, which are the measured data. Root-commit keys can merge unrelated forks. The user chose Claude only on 2026-10-28.
**Files**: `PRD_v0.2.md`, `BRAINSTORMING_LOG_v0.2.md`, `RUNBOOK.md` (commit 109d96e). Confirmed by the user on 2026-10-29.
**Status**: Gate 0 shipped 2026-10-29T08:03:51Z (merge `0ffe6f2`, HUN-84..87): `redact_text` in `save_stop_note` and the `redact [--repo] [--apply]` command in `easy_memory.py`, tests in `tests/test_t010_redact.py`. Next gate is the sample bar (open item O5 first: `configured == auto` filter in `report`).

## Infrastructure

### 2026-10-28 — easy-verifier registered as the scoring MCP (dev tool)
**Decision**: Register the user's running `easy-verifier` container as a project-scoped HTTP MCP in `.mcp.json` (`http://127.0.0.1:8766/mcp`) for Stage 4/5 scoring. No install: the user already runs it (container `2685b68319b9`, `~/workspace` mounted read-only, reports to `~/.easy-verifier-reports`). Not a product dependency.
**Why**: User request "adding the easy-verifier as a scoring mcp". A `pipx install` from `main` was declined by the user.
**Files**: `.mcp.json`, `PROJECT_SPEC.md`


### 2026-10-28 — Linear is the source of truth for tasks
**Decision**: Tasks `HUN-74`..`HUN-82` live in Linear (team HUN, project easy-memory-mcp). Each issue description is the task guide. `PROJECT_KANBAN.md` and `tasks/TASK_GUIDE_<ID>.md` are a cache rewritten by `python3 scripts/board_sync.py pull`; `PROJECT_SPEC.md` lists no tasks. `.claude/board.json` (board mode `online`) holds no secret; `LINEAR_API_KEY` stays in the shell.
**Why**: User instruction "use Linear as the source of truth, remove the local tasks". Linear assigns the IDs, so the draft `T001`..`T009` labels were replaced.
**Files**: `.claude/board.json`, `scripts/board_sync.py`, `PROJECT_SPEC.md`, `PROJECT_KANBAN.md`, `tasks/`

