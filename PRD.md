# PRD — easy-memory-mcp
**Last updated**: 2026-10-25
**Status**: Confirmed by user 2026-10-28 (A2, A6 accepted)
**Owner**: thunderkds / Easy Kit family

> **Scope of this document**: *What* to build and *why* — product intent, user stories, requirements, success metrics.
> Technical decisions, architecture, agent config, and task state live in `PROJECT_SPEC.md`.
> If Out of Scope here conflicts with Critical Constraints there, resolve the conflict before Stage 2.
> Evidence: `experiments/01..03/RESULTS.md` (282 real agent runs, 2026-10-23..25).

---

## Overview

Coding agents pay again for what an earlier session already worked out. A new session reads the same files again to rediscover a flow that was explained yesterday. easy-memory-mcp saves what each Claude Code session concluded. When a later prompt arrives, it shows the agent a short index of the earlier notes that may be relevant, and the agent opens one only if it helps. In experiment 03 this index method cut model tokens by 29% on one repo and 27% on another, at the same accuracy, and no out-of-date note misled an agent. This prototype makes that method real: real hooks, a local store, an MCP server for direct memory access, and a way to measure the effect on the owner's everyday work.

---

## Personas

| ID | Name | Role | Pain Point |
|----|------|------|-----------|
| P1 | Agent-user developer | Uses Claude Code daily on several local repos, including private client repos | Each new session re-explores the same code; long sessions grow expensive; resuming carries stale context |
| P2 | The coding agent | Claude Code session that receives the index | Needs a small, trustworthy hint about earlier findings, with a clear warning when the code has changed since |

---

## User Stories

| ID | Story | Persona |
|----|-------|---------|
| US-001 | As P1, I want every session's conclusion saved automatically, so that I never have to remember to save anything. | P1 |
| US-002 | As P2, I want a short index of earlier notes that may fit my prompt, so that I can open one instead of exploring again. | P2 |
| US-003 | As P2, I want each note to say which of its cited files changed since it was saved, so that I re-check those claims instead of trusting them. | P2 |
| US-004 | As P1 or P2, I want MCP tools to search, read, list and forget notes, so that memory can also be used on purpose. | P1, P2 |
| US-005 | As P1, I want memory kept on my machine, outside my repos, so that private client code never leaves it or gets committed. | P1 |
| US-006 | As P1, I want to turn memory on or off per repo and see a report comparing real token use, so that I know whether it pays off. | P1 |
| US-007 | As P1, I want to install it once for all my repos, so that setup is not a per-repo chore. | P1 |

---

## Functional Requirements

| ID | Requirement | Traces to |
|----|-------------|-----------|
| FR-001 | A Claude Code **Stop** hook must save each turn's final assistant answer as its own note (one note per turn), with the user prompt it answered, the time, and a sha256 hash of every repo file the answer cites. Answers shorter than 200 characters are not saved. <!-- RESOLVED G1 2026-10-28: user chose one note per turn. --> | US-001 |
| FR-002 | Notes must be stored under the user's home folder (default `~/.easy-memory/`), one store per repo, outside every repository. Nothing is written inside a repo. | US-005 |
| FR-003 | A **UserPromptSubmit** hook must add an index of at most 5 notes whose score against the prompt is ≥ 0.12. The score uses word weights from the repo's own source files. Each line shows the note id, the earlier question, the answer's first line, the cited files, and any cited file that changed or was deleted since saving. The injected text is at most 2,500 characters. When no note qualifies, it adds nothing. <!-- RESOLVED G2 2026-10-28 (Supervisor default): 2,500-character cap, just above exp 03's range of 1,500 to 2,300. FLAGGED G3: word weights over a 7,000-file repo cannot be recomputed per prompt inside NFR-001 (1 s); needs a cache and an invalidation rule (design, Stage 0.5b). --> | US-002, US-003 |
| FR-004 | The index must tell the agent how to open a note (by MCP `memory_read` or by file path) and that notes are data that may be out of date. The agent must be able to open a listed note without a permission prompt. | US-002 |
| FR-005 | An MCP server must offer `memory_search(query)` (same index lines), `memory_read(id)` (full note plus changed-file flags), `memory_list()` (newest notes for this repo) and `memory_forget(id)`. | US-004 |
| FR-006 | A per-repo switch must have three states: `on`, `off`, and `auto`, the default, which alternates on and off by calendar day for a fair comparison. When `off`, saving continues but nothing is injected. Each prompt's state must be logged with its session id. <!-- RESOLVED G4 2026-10-28 (Supervisor default): the day is the local-time calendar day. Even day-number since 1970-01-01 = on, odd = off. The report assigns each session the state logged at its first prompt. --> | US-006 |
| FR-007 | A report command must read Claude Code's own session logs and compare sessions with memory on against sessions with it off, per repo. It shows: session count, median tokens (input + output) per session, median turns, and how often a listed note was opened. | US-006 |
| FR-008 | One install command must register both hooks and the MCP server in the user-level Claude Code settings for all repos, and an uninstall command must remove them cleanly. | US-007 |

---

## Non-Functional Requirements

| ID | Requirement | Category |
|----|-------------|----------|
| NFR-001 | The UserPromptSubmit hook must add ≤ 1 s at p95 on a 7,000-file repo (Project B); the Stop hook ≤ 2 s. | Performance |
| NFR-002 | No network traffic: no model calls, no telemetry, nothing leaves the machine. | Privacy |
| NFR-003 | Store files are readable only by the user (0600 files, 0700 folders). | Security |
| NFR-004 | A hook failure must never block or alter the user's prompt: on any error the hook exits 0 and adds nothing, and it logs the error locally. | Reliability |
| NFR-005 | Python standard library only (plus the MCP SDK for the server), so it works in any repo without its own dependencies. | Portability |
| NFR-006 | A note is written as one new file, by write-to-temp then atomic rename, so two sessions in one repo never corrupt each other. No lock file. | Reliability |
| NFR-007 | Every note and the store carry a format version number. A reader skips a note with a newer version and never fails on it. | Maintainability |
<!-- RESOLVED G5 2026-10-28 (Supervisor default): NFR-006 and NFR-007 added. Store growth stays unlimited per A4; the report shows store size so the user can judge. -->
<!-- RESOLVED G6 2026-10-28: A1 confirmed by user. A3 is an implementation test for Stage 0.5b; FR-004 already states the outcome (no permission prompt). A4 has a user owner and a review date (after 2 weeks). A5 comes from experiment 03 data. A7 was stated to the user before sign-off with no objection. -->
<!-- PRD gate: PASS 2026-10-28. 8 FRs validated (all trace to a user story), 7 NFRs (2 added), G1 to G6 resolved, 0 items flagged for the user. G3 (word-weight cache) goes to Stage 0.5b brainstorming. -->


---

## Success Metrics / KPIs

| Metric | Baseline | Target | How measured |
|--------|----------|--------|--------------|
| Median tokens per session, memory on vs off | off-days median per repo | ≥ 15% lower on on-days (experiment 03: −28%) | FR-007 report after ≥ 2 weeks of normal use |
| Index usefulness | — | a listed note is opened in ≥ 25% of sessions that get an index (experiment 03: ≥ 33%) | FR-007 report |
| Misleading memory | — | 0 known cases where an answer repeats a claim the code no longer supports | user reports, plus a spot check of sessions with changed-file flags |
| Hook latency | — | NFR-001 met | timing in the hook log |

---

## Out of Scope

- Other CLIs (Codex, Gemini, Cursor). This is Claude Code only.
- Team sharing, committed memory, cloud sync or a hosted service.
- Vector search, embeddings, or any model call (summarising, judging).
- A user interface beyond the CLI report.
- Editing notes. Notes can be read and forgotten, not edited.

---

## Open Questions / Assumptions

| # | Question / Assumption | Owner | Due |
|---|----------------------|-------|-----|
| A1 | CONFIRMED 2026-10-28: git worktrees share their main repo's store, keyed by the git common dir. Changed-file flags compare against the current worktree's files. | User | done |
| A2 | CONFIRMED 2026-10-28: `auto` (alternate by day) is the default switch state, so the comparison needs no effort from you. | User | done |
| A3 | OPEN (implementation, Stage 0.5b): the agent opens notes through MCP `memory_read`, or through Read with the store added to `additionalDirectories`. Either must avoid permission prompts (FR-004). | Supervisor | Stage 0.5 |
| A4 | ASSUMPTION (revisit): there is no retention limit in the prototype; `memory_forget` and deleting the folder are the controls. | User | after 2 weeks |
| A5 | ASSUMPTION: index limits (5 notes, floor 0.12, word weights from repo files) are carried over unchanged from experiment 03. | Supervisor | Stage 0.5 |
| A6 | CONFIRMED 2026-10-28: the saved prompt is the last user prompt before the final answer, and saved answers are not scrubbed for secrets beyond the 0600 permissions (NFR-003). | User | done |
| A7 | ASSUMPTION: this is a standalone member of the Easy Kit family (core: `personal-agentic-claude`; siblings: `easy-ui-mcp`, `easy-verifier-mcp`). No integration with the siblings in v1; each has its own repo and board. | Supervisor | Stage 0.5 |
