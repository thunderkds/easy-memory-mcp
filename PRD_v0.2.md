# PRD v0.2 (confirmed draft 2) — easy-memory-mcp
**Last updated**: 2026-10-29
**Status**: CONFIRMED by the user on 2026-10-29 ("yes, record it"). Gate 0 is open. `PRD.md` (v0.1) still holds the base requirements until this file is merged into it.
**Owner**: thunderkds / Easy Kit family
**Source**: `BRAINSTORMING_LOG_v0.2.md` (Option B2: redaction only now, everything else gated). Draft 2 replaces draft 1 after a three-agent review on 2026-10-29.

> **Scope of this document**: what changes from `PRD.md` v0.1, and the gates that order the work.
> Every v0.1 FR and NFR not named below carries over unchanged.
> On confirmation, merge this file into `PRD.md` and delete it.

---

## What changed since draft 1

| Draft 1 | Draft 2 | Why |
|---------|---------|-----|
| Safe now: split, portable key, redaction | Safe now: redaction only | The hooks run live from this checkout (`~/.claude-personal/settings.json` lines 56 and 75). Any merge changes the measured hooks on the next prompt. |
| FR-010 portable key in Gate 0 | FR-010 deferred with sync | It moves `config.json`, `prompts.log` and `weights.json`, which are the measured data. A root-commit key can also merge unrelated forks. Its only reason was sync, and sync is deferred. |
| FR-011 split in Gate 0 | FR-011 built in a worktree, merged when Gate 1 opens | A half-merged split breaks live hooks. The split is about 1,500 lines of moved code, not 150. |
| Gate 0 passes when the user confirms | Gate 0 passes on tests and benchmarks | Confirmation is a precondition, not a test. |
| Gate 1 after "2 weeks" | Gate 1 after the sample bar (10 `configured==auto` sessions per group) | The report itself says fewer sessions cannot be compared (`easy_memory.py:1063`). |
| Gate 2 = decay and embedder together | Gate 2a decay, Gate 2b embedder | Decay changes the prompt hook. The embedder changes only `memory_search`. |
| Gate 3: other clients | Removed | The user chose Claude only on 2026-10-28 (`PROJECT_SPEC.md:93`). Other clients would get read-only memory. |

---

## Overview

v0.1 proved the index method in a prototype and started a 2-week on/off measurement. v0.2 must not spoil that measurement. It works in two steps:

1. **Safe now**: one safety fix, secret redaction at save (FR-009). It changes note text only. It does not change ranking, store location, the switch or the report.
2. **Gated**: everything else waits for the sample bar. This covers the package split, bulk forget, decay, the optional embedder. Cross-machine sync and the portable key stay deferred.

**Rule: build is not deploy.** The live hooks run the code in this checkout. Work that must not change the measurement is built on a branch or in a worktree and merged only when its gate opens.

---

## User stories

| ID | Story | Persona | State |
|----|-------|---------|-------|
| US-008 | As P1, I want secrets in my prompts and answers removed before a note is saved, so that a note never holds a key or token. | P1 | Safe now |
| US-010 | As P1, I want the code split into modules with the same behaviour, so that later features stay small and testable. | P1 | Gate 1 |
| US-012 | As P1 or P2, I want to find a note when my prompt uses other words than the note, so that paraphrased questions still hit. | P1, P2 | Gate 2b |
| US-009 | As P1, I want the same repo to have the same store on every machine. | P1 | Deferred with sync |
| US-011 | As P1, I want notes synced between my machines on purpose, per repo. | P1 | Deferred (user, 2026-10-28) |

---

## Functional requirements: changes

| ID | Requirement | Phase | Traces to |
|----|-------------|-------|-----------|
| FR-009 | The Stop hook must redact secrets in the prompt and the answer before the note is written. Each hit becomes `[REDACTED:<kind>]`. The patterns are listed below. A `redact` command must rewrite notes already saved. | Safe now | US-008 |
| FR-011 | The code must be split into modules behind the same entry file `easy_memory.py`, with no change to any command, hook output or stored file. Details below. | Gate 1 (build in a worktree before) | US-010 |
| FR-013 | `memory_search` may use an optional local embedder, installed as an extra. The prompt hook stays keyword-only. A missing extra never breaks a hook or the server. The `Retriever` seam is built with this feature, not before. | Gate 2b | US-012 |
| FR-014 | Decay or automatic expiry of notes. Any rule that changes which notes can rank is a ranking change. Design starts after the report. | Gate 2a | US-004 |
| FR-005 (changed) | `memory_forget` over MCP stays single-id. Bulk forget (by age or query) is a CLI command with `--dry-run`, because the MCP allow rule runs every tool with no prompt. It is user-invoked only. | Gate 1 | US-004 |
| FR-010 (deferred) | Portable store key (root commit, else `origin` URL, else path). Deferred with sync. See "Deferred design notes". | — | US-009 |
| FR-012 (deferred) | Sync `notes/` and `meta.json` of opted-in repos only. Deferred by the user on 2026-10-28. See "Deferred design notes". | — | US-011 |

### FR-009 detail

- **Patterns** (deterministic, no model): private key blocks, AWS access key ids, GitHub tokens (`ghp_`, `gho_`, `github_pat_`), Slack tokens (`xox?-`), `sk-` and `sk-ant-` API keys, JWTs, `Authorization: Bearer ...`, and assignments where the name holds `SECRET`, `TOKEN`, `PASSWORD`, `PASSWD` or `API_KEY`.
- **Private key blocks span many lines.** Use one whole-text regex (DOTALL), run only when the text holds `PRIVATE KEY`. An unterminated `BEGIN` redacts to the end of the text (fail closed). Write the fallback as `|.*`. Do not write it as `|\Z`: that form was quadratic in a test (7 s at 224 KB of repeated `BEGIN`).
- **All other patterns match per line.** Bound the name part, for example `[A-Z0-9_.-]{0,64}`, so a long line cannot slow the match.
- **Restrict the name pattern.** Match `NAME=value`, or `NAME: value` only when the value has 8 or more characters. This keeps lines such as `token: string` in auth code.
- **Tighten `sk-`** with a look-behind `(?<![A-Za-z0-9_-])`, so `risk-…` and `task-…` do not match.
- **Call site**: in `save_stop_note` (`easy_memory.py:299-321`), after `last_user_prompt`, just before the `write_note` dict. Keep the `MIN_ANSWER_CHARS` check and `cited_files()` on the raw answer, so cited-file hashes do not change.
- **Fail closed.** If redaction raises, the hook's existing `except` logs it and writes no note. Do not catch the error inside the redactor.
- **`redact` command**: dry-run by default. `--apply` writes. The dry-run prints note id, kind and count, never the matched text. It works on decoded fields and writes only changed notes, through `_atomic_write`. Running it twice gives the same bytes.
- **Stored text only.** Redaction does not change cited-file hashes or any other field.

### FR-011 detail

- **Package name**: `easy_memory_core/`. A package named `easy_memory/` would shadow the shim `easy_memory.py`.
- **The shim stays `easy_memory.py`.** `OUR_MARKER` (`:740`) matches the shim name, so no installer change is needed.
- **Shim safety.** For `hook-*` subcommands the shim catches `ImportError` and exits 0 (NFR-004). A half-installed package must never break a live prompt.
- **`__file__` use.** Moved code that respawns itself (`:462`, `:755`, `:943`) would point at the new module. Keep a `hook_entries()` wrapper in the shim, or pass the shim path in.
- **Tests.** Of the 24 `patch.object(easy_memory, ...)` sites, 13 patch module attributes and must point at the module that defines the name. A patch left on the shim passes without testing anything. Add a guard test: each patched name must be in its target module's `vars()`. Re-export the 41 `easy_memory.*` names the tests use, one by one, because a star import skips underscore names.
- **Size.** About 1,500 lines move. Estimate: 1.5 to 2 days.
- **No `Retriever` seam yet.** It has one user (today's scorer) until FR-013. Build it with FR-013.
- **Import cost is not a risk.** A tiny shim plus cached modules is net faster. Lazy-import `report`, `mcp` and the installer. Measure with `tests/bench_t004.py`.

## Non-functional requirements: changes

| ID | Change |
|----|--------|
| NFR-002 | Unchanged: no network anywhere (sync is deferred). |
| NFR-005 | Unchanged for the core. A gated extra (the embedder) is optional and imported lazily. |
| NFR-007 | Unchanged. Store format v2 is not needed now (FR-010 is deferred). |
| NFR-008 (new) | Redaction keeps the Stop hook within NFR-001's 2 s. A 1 MB input must pass a ReDoS test. The input cap is `MAX_STDIN_CHARS` (10 MB, `:33`). |

---

## Release gates

| Gate | Opens | Passes when |
|------|-------|-------------|
| Gate 0 | FR-009 | **Precondition**: the user confirms this draft (met 2026-10-29). **Pass**: all 307 v0.1 tests pass with the same names and skips. New redaction tests pass: one fixture per pattern is fully redacted, a no-secret fixture stays byte-identical, a 1 MB input runs under the NFR-008 limit. `tests/bench_t004.py` p95 is not worse. A smoke run adds no line to `hook.log`. The redaction release date is written in `RUNBOOK.md`. |
| Sample bar | — | One repo has at least 10 sessions with `configured == auto` in each group (`REPORT_MIN_SESSIONS`, `easy_memory.py:1063`). The report needs a `configured == auto` filter first, so forced on/off sessions do not enter the comparison. |
| Gate 1 | FR-011 merge, FR-005 bulk forget (CLI) | Sample bar met. FR-009 shipped. The v0.1.0 install date is recorded in `RUNBOOK.md`. |
| Gate 2a | FR-014 decay or expiry, any change to `INDEX_*` constants or the note schema | The report is complete (sample bar met). The result may be positive or negative; a negative result is a reason to fix, not to block. The metric column is named (see Open items). An offline check against experiment 03 answers runs, and the data exists (see Open items). |
| Gate 2b | FR-013 embedder | FR-011 merged. A paraphrase test set exists offline (experiment 04). Recall on that set beats the keyword scorer. A test shows the prompt hook output is byte-identical with and without the extra installed. |

**Gate 3 (other clients) is removed.** Claude only, by the user's choice on 2026-10-28.

---

## Deferred design notes

Kept so a later round does not repeat the analysis.

- **FR-010 portable key.** Risks found on 2026-10-29: (1) it moves `config.json`, `prompts.log` and `weights.json`, so a migration changes the measured data; (2) a repo with no commit has no root, so its key changes after the first commit; (3) `filter-repo`, `rebase --root` and a changed `origin` URL change the key and orphan the store; (4) forks and template repos share a root commit, so unrelated repos can merge notes; (5) `repo_key` already runs `git rev-parse` about 5 times per prompt hook, and `git rev-list` over deep history risks the hook timeout; (6) concurrent hooks may lose `prompts.log` lines during a move. If it returns: compute the key once per process, add a collision guard (store the path in `meta.json` and refuse to merge when paths differ), run git with a timeout under 1 s, copy `config.json` and `prompts.log` instead of moving them, and treat a repo with no `HEAD` as the path key. Required test: 8 simultaneous prompt hooks on a seeded path-keyed store, then check note count, switch state, `prompts.log` line count and exactly one `moved.json`; repeat after `git commit --amend --root`.
- **Opt-in alias (cheaper than FR-010).** An `alias.json` (`{"share_with": "<path-or-key>"}`) inside one store would make that clone read the other store. Nothing moves and nothing is hashed. Use it if clone sharing is wanted before sync.
- **FR-012 sync.** Sync `notes/` and `meta.json` of opted-in repos only. Never `weights.json`, `weights.lock`, `prompts.log`, `hook.log`, `config.json` or temp files, and never inside a hook. Sync needs FR-010 or the alias first, and it must ignore `moved.json`.

---

## Open items

| # | Item | Owner |
|---|------|-------|
| O1 | DONE 2026-10-29. Install time and window start are in `RUNBOOK.md` (Measurement Window). Install: 2026-10-28T07:22:23Z. Window start: 2026-10-29T02:01:36Z, the Supervisor's reading of `prompts.log`. | Supervisor |
| O2 | Experiment 03's `work/` data is not in the repo (`tests/parity_t003.py` needs it). Restore or regenerate it before Gate 2a. | User |
| O3 | Name the metric for the Gate 2a rule. `PRD.md` FR-007 says input + output. The report's verdict line uses all four usage counts (`easy_memory.py:1263-1265`). | User |
| O4 | Hook time grows with the note count (about 1 ms per note; `_index_lines`, `:581`, reads every note). Design the fix (cap or index file) after the report. | Supervisor |
| O5 | Add the `configured == auto` filter to `report` before the sample bar is trusted. | Supervisor |

---

## Out of Scope: changes

Still **out** of scope: cross-machine sync of any kind (deferred 2026-10-28: git remote, folder sync, S3/R2); a portable store key; other MCP clients (Cursor, Codex); an S3/R2 or other cloud backend; any network call inside a hook; local encryption at rest (rely on disk encryption; the key would sit next to the notes); a web or TUI viewer; vector databases (sqlite-vec, LanceDB, Chroma); embeddings in the prompt hook; any model call; a dependency on `easy-context-mcp` (PRD A7).

Moved **into** scope (gated): an optional embedder in `memory_search` only (FR-013, Gate 2b).

---

## Assumptions: changes

| # | Change | Owner | Due |
|---|--------|-------|-----|
| A4 | Retention: still no limit until Gate 1. Bulk forget (manual) arrives with Gate 1. Automatic expiry waits for Gate 2a. | User | after sample bar |
| A6 | REPLACED by FR-009: new answers are redacted at save, then kept with 0600 permissions. Redaction is defense in depth, not a guarantee. A secret in an unlisted shape is saved. A key split over two lines (other than a private key block) is missed. Claude Code's own transcripts under `~/.claude/projects` still hold the original text. If a real secret appears, rotate it. | User | on confirmation |
| A7 | Unchanged: no integration with sibling MCPs. | Supervisor | Gate 2b |
| A8 | REMOVED with FR-010. Two clones of one repo keep two stores. | — | — |
| A9 (new) | The live hooks run the code in this checkout. A merge to this checkout changes measured behaviour on the next prompt. Build gated work on a branch or in a worktree. | Supervisor | always |
| A10 (new) | Redaction during the window is not zero-effect: it removes whole `TOKEN: …` style lines from new notes. The effect on score is expected to be small. The release date is recorded so the report can be read around it. | Supervisor | Gate 0 |

---

## Decision record

| Decision | By | Date | Status |
|----------|----|------|--------|
| Plan first, no code until the plan is confirmed | user | 2026-10-28 | Final |
| Defer the sync feature | user | 2026-10-28 | Final |
| Claude only, no Codex use | user | 2026-10-28 | Final |
| Three-agent review of draft 1 | user asked, Supervisor ran it | 2026-10-29 | Done |
| Minimal Gate 0 (FR-009 only), drop FR-010, gate the split, split Gate 2, remove Gate 3 | Supervisor recommendation; user: "yes, update plan thoroughly", then "yes, record it" after being asked to confirm draft 2 | 2026-10-29 | Final |
| Q1: hold ranking work until the sample bar | user, with the confirmation of draft 2 | 2026-10-29 | Final |
| Q3: `redact` command, dry-run first | user, with the confirmation of draft 2 | 2026-10-29 | Final |
| Package name `easy_memory_core/` | user, with the confirmation of draft 2 | 2026-10-29 | Final |
