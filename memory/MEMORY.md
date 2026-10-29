# MEMORY.md — Hot-Tier Memory Index

> **Rules**: Supervisor-only writes. Max 42,000 characters — a ratchet: `/compact-memory` may lower
> it, never raise it to fit growth. One-line summaries + links to cold files.
> Each spawn prompt carries a slice of these lines (craft-spawn-prompt's memory_slice.py) and this
> path to read in full only when the slice falls short; the whole file is not pasted.
> Updated by the Supervisor — prompted by the PostToolUse hook on `git push` / `git merge` (diff-driven pass), or via the `/compact-memory` skill.

---

## Memory Architecture

- [decisions.md](decisions.md) — code + infra architectural decisions (the "why")
- [glossary.md](glossary.md) — canonical biz domain terms and core domain models
- [learnings.md](learnings.md) — specs/requirement clarifications, patterns, gotchas

---

## Index

<!-- Format: - [Title](cold-file.md#section) — one-line summary.
     Target ≤150 chars/entry. Advisory: reported by the size test, never enforced.
     The enforced gate is the 42,000-character whole-file budget above. -->
- [Path C: single-file stdlib prototype](decisions.md#architecture) — hooks + hand-written MCP; weights built in background (16.5 s on orderly)
- [Linear is the source of truth](decisions.md#infrastructure) — tasks HUN-74..82; kanban and tasks/ are a pull cache
- [Board setup without a tty](learnings.md#patterns) — script `init` with a scripted ask; rewrite forward IDs after create
- [Tracked experiment results may leak private code](learnings.md#gotchas) — no .gitignore; open question for the user
- [easy-verifier as scoring MCP](decisions.md#infrastructure) — user's container, HTTP :8766, project-scoped .mcp.json; dev tool only
- [Weights keep words in 3+ files](decisions.md#architecture) — 2 gave 3.6 MB on orderly (limit 2 MB); 3 gives 1.7 MB and passes parity
- [Prototype open defects D1-D3](learnings.md#patterns) — prompt-hook time grows with notes (~1 ms each); big transcripts; uncapped non-git build
- [v0.1.0 released to GitHub](../RUNBOOK.md) — tag v0.1.0 at 7916424, main pushed 2026-10-28; install and the AC6 live check are the user's
- [v0.2 plan: redaction only now](decisions.md#architecture) — FR-009 ships in the window; split gated; key deferred; Gate 3 removed
- [Redaction regex and split test traps](learnings.md#patterns) — `|.*` fallback; patches on the shim pass silently
- [Hook time grows with notes; report pollution](learnings.md#gotchas) — ~1 ms per note; `report` ignores `configured`; window start 2026-10-29T02:01:36Z
- [Hook-prompt tests and the auto switch](learnings.md#gotchas) — fixed by HUN-84; new prompt-hook test classes must set `switch = "on"`
