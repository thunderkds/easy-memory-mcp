# PRD v0.2 (draft) — easy-memory-mcp
**Last updated**: 2026-10-28
**Status**: DRAFT, not confirmed. `PRD.md` (v0.1, confirmed 2026-10-28) stays in force until the user confirms this file.
**Owner**: thunderkds / Easy Kit family
**Source**: `BRAINSTORMING_LOG_v0.2.md` (Option B: foundations first, gated features)

> **Scope of this document**: what changes from `PRD.md` v0.1, and the gates that order the work.
> Every v0.1 FR and NFR not named below carries over unchanged.
> On confirmation, merge this file into `PRD.md` and delete it.

---

## Overview

v0.1 proved the index method in a prototype and started a 2-week on/off measurement. v0.2 prepares easy-memory to become long-term memory across machines and clients, without spoiling that measurement. It does that in two steps:

1. **Safe now** (during the measurement): changes with no visible behaviour change, plus one safety fix. These are a package split, a portable store key and secret redaction at save.
2. **Gated** (after the measurement): features that change ranking, storage location or the hosts that see notes. These are sync, lifecycle, semantic search and other clients.

---

## New user stories

| ID | Story | Persona |
|----|-------|---------|
| US-008 | As P1, I want secrets in my prompts and answers removed before a note is saved, so that a note never holds a key or token. | P1 |
| US-009 | As P1, I want the same repo to have the same store on every machine, so that notes can later follow me between laptop and desktop. | P1 |
| US-010 | As P1, I want the code split into modules with the same behaviour, so that later features stay small and testable. | P1 |
| US-011 (gated) | As P1, I want notes synced between my machines on purpose, per repo, so that a second machine starts with what the first learned. | P1 |
| US-012 (gated) | As P1 or P2, I want to find a note when my prompt uses other words than the note, so that paraphrased questions still hit. | P1, P2 |

---

## Functional requirements: changes

| ID | Requirement | Phase | Traces to |
|----|-------------|-------|-----------|
| FR-009 | The Stop hook must redact secrets in the prompt and the answer before the note is written. Each hit becomes `[REDACTED:<kind>]`. Patterns are deterministic (no model) and listed in `BRAINSTORMING_LOG_v0.2.md` R3. A `redact [--dry-run]` command must rewrite notes already saved, by temp file and atomic rename. | Safe now | US-008 |
| FR-010 | A store must be keyed by the repo's identity: its root commit, else its normalized `origin` URL, else its real path (today's key). A shallow clone skips the root commit. The first run must move an existing path-keyed store to the new key and leave a pointer; it never deletes notes. | Safe now | US-009 |
| FR-011 | The code must be split into modules behind the same entry file `easy_memory.py`, with no change to any command, hook output or stored file. A `Retriever` seam must hold today's scorer as its only implementation. | Safe now | US-010 |
| FR-012 (gated) | A `sync` command must sync `notes/` and `meta.json` of opted-in repos only. It must never sync `weights.json`, `weights.lock`, `prompts.log`, `hook.log`, `config.json` or temp files. It never runs inside a hook. Mechanism (git remote or folder sync only) is open: Question 2 of the brainstorming log. | Gate 1 | US-011 |
| FR-013 (gated) | `memory_search` may use an optional local embedder through the Retriever seam, installed as an extra. The prompt hook stays keyword-only. A missing extra never breaks a hook or the server. | Gate 2 | US-012 |
| FR-005 (changed, gated) | `memory_forget` over MCP stays single-id. Bulk forget (by age or query) is a CLI command with `--dry-run`, because the MCP allow rule runs every tool with no prompt. | Gate 1 | US-004 |

## Non-functional requirements: changes

| ID | Change |
|----|--------|
| NFR-002 | Unchanged for every hook and for `serve`. Only the gated `sync` command may use the network, only when the user runs it, only for opted-in repos. |
| NFR-005 | Unchanged for the core. Gated extras (an embedder) are optional and imported lazily; the core never needs them. |
| NFR-007 | Store format v2 for the new key layout (FR-010). A v1 reader skips a v2 marker and never fails on it. |
| NFR-008 (new) | Redaction (FR-009) keeps the Stop hook within NFR-001's 2 s. |

---

## Release gates

| Gate | Opens | Passes when |
|------|-------|-------------|
| Gate 0 | Safe-now work (FR-009 to FR-011) | User confirms this draft. FR-011 lands first. All 307 v0.1 tests pass with the same names and skips. |
| Gate 1 | Sync (FR-012), lifecycle, bulk forget | FR-009 and FR-010 shipped. 2 weeks of `report` data exist. |
| Gate 2 | Any ranking change: decay, embedder (FR-013) | v0.1 report shows on vs off median ≤ −15% (v0.1 target). A paraphrase test set exists offline (experiment 04). An offline check against experiment 03 answers meets the HUN-76 parity bar. |
| Gate 3 | Other clients (Cursor, Codex) | FR-011 shipped. `serve` takes the repo from `--repo` or MCP roots, not only `cwd`. |

---

## Out of Scope: changes

Moved **into** scope (gated): cross-machine sync of opted-in repos (FR-012), an optional embedder in `memory_search` (FR-013), other MCP clients (Gate 3).

Still **out** of scope: an S3/R2 or other cloud backend; any network call inside a hook (including pull-before-score); local encryption at rest (rely on disk encryption; the key would sit next to the notes); a web or TUI viewer; vector databases (sqlite-vec, LanceDB, Chroma); embeddings in the prompt hook; any model call; a dependency on `easy-context-mcp` (PRD A7: plug-ins stay independent).

---

## Assumptions: changes

| # | Change | Owner | Due |
|---|--------|-------|-----|
| A4 | Retention: still no limit until Gate 1. Lifecycle design starts after the 2-week report. | User | after 2 weeks |
| A6 | REPLACED by FR-009: answers are redacted at save, then kept with 0600 permissions. | User | on confirmation |
| A7 | Unchanged: no integration with sibling MCPs. A shared embedder is a generic optional setting, not a dependency on `easy-context-mcp`. | Supervisor | Gate 2 |
| A8 (new) | Two clones of one repo on one machine share one store after FR-010, the same as worktrees (A1). | User | on confirmation |
