# PRD v0.4 — easy-memory-mcp: report numbers for the easy-personal dashboard

**Date**: 2026-11-03 · **Owner**: thunderkds · **Status**: requirement locked (user "yes, let go", 2026-11-03)

## Why

easy-personal 0.4.0 already draws the easy-memory store in its Memory view (its FR-051..FR-053, HUN-184/185): notes per day, injection hit rate, cited files and stale marks. It reads `~/.easy-memory/` files directly, metadata only, and never calls the easy-memory MCP (its DDR-0002).

It cannot show whether memory saves tokens. Only `report_command` computes that: it joins `prompts.log` with Claude Code's session logs and compares memory-on sessions with memory-off sessions (FR-007). Copying that logic into easy-personal would give two copies of the on/off rules that drift apart.

## Decision record

| Decision | By | Date |
|---|---|---|
| easy-memory computes the on/off comparison and writes it to a file; easy-personal reads the file and draws a card. easy-personal does not copy the join logic. | user | 2026-11-03 |
| This supersedes PRD.md A7 ("no integration with the siblings in v1") for this one file. The integration is a read-only file contract, not an MCP call, so easy-personal's DDR-0002 and metadata-only rule hold. | user | 2026-11-03 |
| The file holds counts, medians, rates, flags and a time only: never prompt, answer, note text, session id or file path. | Supervisor default (easy-personal's metadata-only rule) | 2026-11-03 |
| The Stop hook refreshes the file in a detached background process, at most once per hour. A full report reads every session log, so it cannot run inside the 2 s Stop budget (NFR-001). | Supervisor default | 2026-11-03 |
| The text output of `report` does not change. | Supervisor default (Gate 2a: measurement code must not move) | 2026-11-03 |

## Functional requirement

| ID | Requirement | Traces to |
|---|---|---|
| FR-015 | `report --json` must print the comparison as one JSON object, and also write it to `<store>/report.json` (0600, atomic). Fields (format `v` 1): `v`, `generated` (UTC ISO time), `min_sessions` (10), `sessions_logged`, `no_data`, `no_claude_log`, `forced`, `groups.on` and `groups.off` each with `sessions`, `tokens_all_median`, `tokens_io_median`, `turns_median` (null when the group is empty), `note_opened` with `opened` and `indexed`, `too_few` (true when a group has fewer than `min_sessions`), `on_vs_off_pct` (median headline tokens on vs off, in percent; null when `too_few` or the off median is 0), `store` with `notes` and `bytes`. Every number equals the one the text report prints for the same store. The Stop hook starts a detached `report --json` for the repo when `report.json` is missing or older than 1 hour, and no other refresh holds the lock. | user 2026-11-03; FR-007 |

## Cross-repo dependency

| ID | Repo | What | Waits for |
|---|---|---|---|
| XR-1 | easy-personal-mcp | Read `<store>/report.json` (format `v` 1; abstain on a newer `v`) and add a "memory on vs off" card to the Memory panel. When `too_few` is true, it says "too few sessions" and shows no saving. | this FR merged |

## Out of scope

- A new MCP tool for the numbers (easy-personal's DDR-0002).
- Changing what the report measures, or the 10-session bar.
- Any change in the easy-personal repo from this board (rule 4: one project per board).
