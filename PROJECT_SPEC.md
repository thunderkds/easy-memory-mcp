# PROJECT_SPEC.md
**Last updated**: 2026-10-28
**Version**: 1.0

> **Scope of this document**: *How* to build it safely — architecture, agent config, constraints, risk areas, task state, and accumulated learnings.
> Product intent (personas, user stories, FR/NFR, success metrics) lives in `PRD.md`.
> If Critical Constraints here conflict with Out of Scope in `PRD.md`, resolve before Stage 2.

---

## Project Identity

- **Name**: easy-memory-mcp
- **Repo**: `/home/hungnguyenhuu/workspace/pets/hungnguyen111/easy-memory-mcp` (member of the Easy Kit family; core: `thunderkds/easy-kit`; siblings: `easy-ui-mcp`, `easy-verifier-mcp`, separate repos and boards)
- **Primary tech**: Python 3.14, standard library only (no MCP SDK)
- **Type**: CLI tool with two Claude Code hooks and a stdio MCP server
- **Deployment target**: the user's machine only; installed into the user-level Claude Code settings
- **Key stakeholders**: thunderkds (owner and only user)

---

## Architecture Summary

One Python module with subcommands: `hook-stop`, `hook-prompt`, `serve`, `report`, `install`, `uninstall` (decision of 2026-10-28, `memory/decisions.md`). The Stop hook saves one note per turn as a JSON file under `~/.easy-memory/<repo-key>/`, written by temp file and atomic rename. The UserPromptSubmit hook scores the prompt against saved notes and adds an index of at most 5 notes, 2,500 characters. Word weights come from the repo's own files, are built by a background process and only read by the hook. A hand-written stdio MCP server offers `memory_search`, `memory_read`, `memory_list`, `memory_forget`.

Port from evidence: `experiments/02-auto-memory/memstore.py` (tokens, cited files, scoring, word weights) and `experiments/03-precision/precision.py` (index). `experiments/` is read-only evidence.

---

## Glossary

| Term | Meaning |
|---|---|
| Note | One saved turn: prompt, final answer, time, and a sha256 hash of each repo file the answer cites. |
| Index | The short list of up to 5 notes the prompt hook adds to a prompt. |
| Word weights | Per-repo table of how rare each word is in the repo's source files. Used to score a prompt against notes. |
| Store | The folder `~/.easy-memory/<repo-key>/` with a repo's notes. Worktrees share the main repo's store. |
| Switch | Per-repo state `on`, `off` or `auto` (even day = on, odd day = off, local time). |
| Typed prompt | A transcript `type: user` entry the user wrote: not `isMeta`, not a sidechain, not an event. (v0.3, `PRD_v0.3.md`) |
| Event | A `type: user` entry the user did not type: a task notification (`origin.kind == "task-notification"`), `!` command output (`<bash-input>`, `<bash-stdout>`, `<bash-stderr>`), `[Request interrupted`, or a compaction summary (`isCompactSummary`). Never a note's question. (v0.3) |
| Trigger | Note field naming the event that set off the reply: `task-notification`, `bash` or `compact`. Absent when a typed prompt did. (v0.3) |
| Turn | The transcript entries after the last typed prompt. (v0.3) |
| Touched file | A repo file the turn opened, edited, wrote, searched, or named inside a Bash command. A note cites a file only if its answer names it and the turn touched it. (v0.3) |
| Trash | `<store>/trash/`: forgotten notes, restorable with `memory_restore` for 30 days. (v0.3) |

---

## Critical Constraints

- Never write inside an observed repo (FR-002). Only `~/.easy-memory/` and the installer's reversible edit of user-level Claude Code settings.
- A hook never blocks or alters the prompt: catch everything, exit 0, log to `~/.easy-memory/hook.log` (NFR-004). Exit code 2 blocks a prompt, so never use it.
- No network, no model call, no telemetry (NFR-002). Store files 0600, folders 0700 (NFR-003).
- The prompt hook must not build word weights. Building took 16.5 s on Project B; the budget is 1 s (NFR-001).
- Do not edit anything under `experiments/`. Do not change the scorer's behavior without a new offline check against experiment 03 answers (A5).
- The installer edits the user's real settings: back up first, support `--dry-run`, and `uninstall` must restore cleanly (FR-008).

---

## Scoring Tool: easy-verifier

`easy-verifier` (MCP, HTTP, `http://127.0.0.1:8766/mcp`, registered in `.mcp.json`) scores the code and the agents' results at Stage 4/5: `score`, one tool per dimension, `write_report`. It runs as the user's local Docker container `easy-verifier`, read-only on `~/workspace`; reports go to `~/.easy-verifier-reports`, not into this repo. It is a development tool only. It is not part of the product (PRD A7: no integration between the memory tool and its sibling MCPs in v1). The first use in a Claude Code session needs the user's approval of the project-scoped server.

---

## Known Risk Areas

| Area | Risk Level | Reason | Files |
|------|-----------|--------|-------|
| Prompt-hook latency | High | 7,835-file repo; weights build 16.5 s, 16 MB file loads in 0.3 s | `hook-prompt` module |
| Installer edits user settings | High | A bad edit breaks every Claude Code session; wrong allow rule hides or grants access | `install` / `uninstall` |
| Hand-written MCP protocol | Medium | No SDK; future Claude Code versions may change the handshake | `serve` |
| Compact word weights | Medium | Smaller table may shift scores near the 0.12 floor | scorer module |
| Stale or misleading notes | Medium | Index must always flag changed or deleted cited files | `hook-prompt`, `memory_read` |

---

## Sub-Agent Team

| Agent | Role | CLI Spawn Command |
|---|---|---|
| Common-Infrastructure-Agent | Package skeleton, test runner, worktrees | `Agent({ subagent_type: "common-infrastructure", prompt: "..." })` |
| Backend-Implementer | All Python code (hooks, store, scorer, MCP, installer, report) | `Agent({ subagent_type: "backend-developer", prompt: "..." })` |
| Frontend-Implementer | Not used: no UI (PRD Out of Scope). The report is CLI text. | — |
| QA-Automation-Agent | Tests, latency benchmark, A3 permission test, regression check | `Agent({ subagent_type: "qa-expert", prompt: "..." })` |

---

## CLI Model Table

> Filled at Stage 1. One row per authenticated CLI, one column per Complexity level. At spawn
> time, `craft-spawn-prompt` looks the task's Complexity Level up in the row for the CLI that will
> run it and reports `<cli> · <Cn> → <model>`. No row for the CLI, or an empty cell → STOP and ask
> the user; never fall back to another CLI's model, never invent one.

| CLI | Run command | C0 | C1 | C2 | C3 |
|---|---|---|---|---|---|
| claude | `claude` | haiku-5-5 | sonnet-5-5 | sonnet-5-5 | opus-5-5 |

(`codex` is installed but not used: user chose Claude only on 2026-10-28.)

---

## Tasks

Linear is the source of truth: team `HUN`, project **easy-memory-mcp** (https://linear.app/thunderkds/project/easy-memory-mcp-ddcf0593772a). Tasks started at `HUN-74`; v0.3 tasks come from `PRD_v0.3.md` and `BRAINSTORMING_LOG_v0.3.md`; each issue description is its task guide. Do not list tasks here. `PROJECT_KANBAN.md` and `tasks/TASK_GUIDE_<ID>.md` are a cache that `python3 scripts/board_sync.py pull` rewrites from Linear.

---

## Memory / Insights

| Date | Insight | Source Task |
|------|---------|------------|
| 2026-10-28 | Building word weights on Project B: 16.5 s, 16 MB, 0.3 s to load. They cannot be built inside a hook. | Stage 0.5 |
| 2026-10-28 | Stop hook input has `last_assistant_message` but no user prompt; the prompt comes from the transcript or a stash. | Stage 0.5 |
