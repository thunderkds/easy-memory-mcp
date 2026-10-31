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
- [Experiment results were tracked and pushed](learnings.md#gotchas) — untracked in 649903c; remote history still has them; parity check needs local copies
- [easy-verifier as scoring MCP](decisions.md#infrastructure) — user's container, HTTP :8766, project-scoped .mcp.json; dev tool only
- [Weights keep words in 3+ files](decisions.md#architecture) — 2 gave 3.6 MB on orderly (limit 2 MB); 3 gives 1.7 MB and passes parity
- [Prototype open defects D1-D3](learnings.md#patterns) — prompt-hook time grows with notes (~1 ms each); big transcripts; uncapped non-git build
- [v0.1.0 released to GitHub](../RUNBOOK.md) — tag v0.1.0 at 7916424, main pushed 2026-10-28; install and the AC6 live check are the user's
- [Release page: Graphite Mint family theme](decisions.md#architecture) — HUN-125 spec-driven; `site/theme.css` tokens byte-identical to the spec; HUN-127: 1280px container, pictures first, no task IDs; HUN-130: rev 25 neon layer, `html.no-glow`
- [easy-ui-mcp for page checks](learnings.md#patterns) — JSON-RPC over http://localhost:8765/mcp; no viewport tool, use iframes
- [v0.2 plan: redaction only now](decisions.md#architecture) — Gate 0 (FR-009) shipped 2026-10-29T08:03:51Z; O5 report filter merged (HUN-122); split gated; key deferred; Gate 3 removed
- [Redaction regex and split test traps](learnings.md#patterns) — `|.*` fallback; patches on the shim pass silently
- [Hook time grows with notes; report pollution](learnings.md#gotchas) — ~1 ms per note; `report` ignores `configured`; window start 2026-10-29T02:01:36Z
- [security-review needs `origin`; board has no Ready-for-Review](learnings.md#gotchas) — use an independent agent; mark Done before merge
- [Hook-prompt tests and the auto switch](learnings.md#gotchas) — fixed by HUN-84; new prompt-hook test classes must set `switch = "on"`
- [Ranking stays as main; HUN-140 shelved](decisions.md#architecture) — rare-word gate hid ~1/3 of relevant notes (exp 06 holdout); df cutoff (exp 05) also failed
- [Forget is recoverable (trash + restore)](decisions.md#architecture) — HUN-135 merged 2026-10-31; 30-day trash; redact covers trash; symlinked trash refused
- [Merge gate blocks all merges while any task In Progress](learnings.md#gotchas) — park Gate-2a-held tasks in Todo with the merge condition
- [Review skills can't target worktrees; stop hook 6h window](learnings.md#gotchas) — review/verify by hand in the worktree; kit fix T186 pending
