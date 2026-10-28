# decisions.md — Cold Tier: Architectural & Infrastructure Decisions

> **Rules**: Supervisor-only writes. Each entry: `### YYYY-MM-DD — Title`, then **Decision**, **Why**, and **Files** (cite paths — the diff-driven pass greps this file by changed file path).

## Architecture

### 2026-10-28 — Implementation path C: single-file, stdlib-only prototype
**Decision**: Build one Python module with subcommands (`hook-stop`, `hook-prompt`, `serve`, `report`, `install`, `uninstall`). Hand-written stdio MCP server (4 tools). Notes are one JSON file each under `~/.easy-memory/`, written by temp file + atomic rename. Word weights come from the repo's own files (as in experiment 03), built in a background process and read by the hook, never built inside it. One note per Stop turn (answer ≥200 chars). Injected index ≤2,500 characters. Worktrees share the main repo's store.
**Why**: Building weights on orderly (7,835 files) took 16.5 s and gave a 16 MB file that takes 0.3 s to load; NFR-001 allows 1 s. The `mcp` SDK is not installed, and NFR-005 forbids dependencies. Keeping experiment 03's scorer keeps its evidence (−28% tokens, 0 misled) valid. Rejected: A (SDK port, latency and dependency), B (SQLite FTS5, changes the validated scorer).
**Files**: `BRAINSTORMING_LOG.md`, `PRD.md`, `experiments/02-auto-memory/memstore.py` (scorer to port), `experiments/03-precision/precision.py` (index to port)

## Infrastructure
