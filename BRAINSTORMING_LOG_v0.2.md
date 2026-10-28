# BRAINSTORMING_LOG_v0.2.md
**Generated**: 2026-10-28
**Task / Context**: Easy Memory enhancement plan (v0.2 to v0.4), feasibility review against `easy_memory.py` at `36c8ce4`
**Skill**: `Skill({ skill: "brainstorming" })`
**Status**: Draft. User approved "plan first" on 2026-10-28. No code changes until this log and `PRD_v0.2.md` are confirmed.

> The v0.1 log (`BRAINSTORMING_LOG.md`) stays as the record of the prototype decision (Option C). This log covers only the next round.

---

## The Problem Space

The user's plan grows easy-memory from "recent session notes" into a long-term memory layer: vector search, cross-machine sync, note lifecycle, security hardening, multi-client support and better observability. Most of it lies outside the v0.1 PRD (Out of Scope lists vector search, embeddings, cloud sync, other CLIs and a UI).

Non-negotiables that every option must keep:

- NFR-001: prompt hook ≤ 1 s p95 on a 7,000-file repo. Each hook run is a new Python process.
- NFR-002: no network, no model call, no telemetry.
- NFR-004: a hook never blocks or alters the prompt; it exits 0.
- NFR-005: standard library only.
- A5 + PROJECT_SPEC Critical Constraints: no scorer change without an offline check against experiment 03 answers.
- The v0.1.0 `auto` switch started a 2-week on/off comparison (PRD A4, success metrics). A scorer change inside that window mixes two scorers in one result.

The question for this round: which parts of the plan are safe to build **now**, during the measurement, and which must wait for its result?

---

## Verified facts (claim verification gate)

| # | Claim | Evidence |
|---|---|---|
| F1 | The store key depends on the machine. `repo_key()` is `sha256(realpath(git common dir))[:16]`. The same repo at `/home/a/x` and `/Users/a/x` gets two stores, so any folder sync never joins them. | `easy_memory.py` `_identity_path`, `repo_key` |
| F2 | Saved prompts and answers are not scrubbed for secrets. Only 0600 permissions protect them. | PRD A6 (confirmed 2026-10-28), `save_stop_note` |
| F3 | The product is one 1,567-line file. Tests patch module attributes through `mock.patch.object(easy_memory, ...)` (24 call sites). | `easy_memory.py`, `tests/` |
| F4 | Installed hook commands hold the absolute path of `easy_memory.py`, and the installer finds its own hooks by the marker `easy_memory.py`. | `hook_entries`, `OUR_MARKER`, `_is_ours` |
| F5 | The full suite passes on `36c8ce4`: 307 tests, 7 skipped, 34.5 s, Python 3.13. | `python3 -m unittest discover -s tests` |
| F6 | The MCP allow rule `mcp__easy-memory` covers every tool, so `memory_forget` runs with no permission prompt. | `MCP_ALLOW_RULE`, `install_command` |
| F7 | `easy-context-mcp` already embeds with FastEmbed and `sentence-transformers/all-MiniLM-L6-v2`, the model the plan names. | `easy-context-mcp` `pyproject.toml`, `src/easy_context_mcp/embedding.py` |
| F8 | Experiment 03: the index method wins "without needing precise picking"; wrong-topic lines are cheap and the agent ignores them. | `experiments/03-precision/RESULTS.md`, Finding 2 |

---

## Questions for the User

1. Confirm the gate: the scorer, decay and vector work wait until the 2-week v0.1 report is in (approved in principle on 2026-10-28: "plan first").
2. Sync: git-backed `sync` command (opt-in per repo, private remote you own), or Syncthing only with no sync code? Recommendation: decide after R2 and R3 ship; both need them.
3. A6 changes from "not scrubbed" to "redacted at save". Should a one-time `redact` command also rewrite the notes already saved? Recommendation: yes, with `--dry-run`, because v0.1 notes may already hold secrets.

---

## Alternative Paths

| Option | Name | Summary | Invasiveness | Code Volume | Regression Risk | Recommended? |
|--------|------|---------|-------------|------------|----------------|--------------|
| A | Plan as written | Vectors + git sync first (v0.2), then lifecycle and security | High | ~800+ lines plus native deps | High | |
| B | Foundations first, gated features | Safe-now refactors and redaction during the measurement; features after its gate | Medium | ~350 lines for the safe-now slice | Low | ✅ Yes |
| C | Docs only | Syncthing how-to, no code until the report is in | Low | ~0 lines | Low | |

### Option A — Plan as written
**Approach**: add a local embedder and a vector store (sqlite-vec, LanceDB or Chroma), a hybrid re-rank in the prompt hook, then a git sync with pull-before-score.
**Pros**: biggest visible change; follows the plan's order.
**Cons**: breaks NFR-005 (onnxruntime + model, ~100 MB). Model load in every hook process uses most of the 1 s budget (NFR-001). A hybrid score has no meaning against the 0.12 floor (A5). Pull-before-score puts network in the hot path (NFR-002, NFR-004).
**Why it might fail**: sync joins nothing because of F1. The v0.1 measurement is spoiled because the scorer changes inside its window.

### Option B — Foundations first, gated features
**Approach**: three changes with no visible behaviour change land now (R1 package split, R2 portable store key, R3 secret redaction). Feature work waits behind gates (see `PRD_v0.2.md`, Release gates).
**Pros**: every later feature needs R1 to R3. The v0.1 measurement stays clean. Redaction lowers today's risk even if sync never ships.
**Cons**: no new user-facing feature for about 2 weeks.
**Why it might fail**: the package split moves code that 24 test patches point at (F3). A patch on the shim then silently stops reaching the moved code, so tests pass for the wrong reason. Mitigation: re-point each patch, and compare test counts and names before and after. R2 migration could orphan a store; mitigation: move plus a `moved.json` pointer, never delete.

### Option C — Docs only
**Approach**: write a Syncthing how-to and wait.
**Pros**: zero risk.
**Cons**: does not work. Because of F1, Syncthing syncs two stores that never meet. Secrets stay unscrubbed.
**Why it might fail**: it is already known to fail (F1).

---

## 50% Rule Check

Half the code for Option B: skip R1 and put R2 and R3 into the single file. That saves the split (about 150 lines moved, many test edits). It leaves sync, lifecycle, vectors and a second client all landing in a file that is already 1,567 lines. **Cut list for the vital slice**: none of R1 to R3. Cut from the plan overall: S3/R2 backend, pull-before-score in the prompt hook, local encryption at rest, web/TUI viewer, sqlite-vec/LanceDB/Chroma, embeddings in the prompt hook.

---

## Safe-now designs

### R1 — Package split (no behaviour change)

```
easy_memory.py            # entry shim: main(); same file name and path (F4)
easy_memory_core/        # name open (see below): must differ from the shim
  store.py                # repo key, atomic write, read/write notes, FORMAT_VERSION
  retrieve.py             # tokens, score, weights; Retriever seam with one method rank(query, notes)
  index.py                # _index_lines, framing, _quoted, _file_flags
  adapters/claude.py      # hooks, transcript parsing, installer, report
  mcp.py                  # serve + 4 tools
```

- The shim keeps the name `easy_memory.py`, so existing installs and `_is_ours` keep working.
- A module and a package cannot share a name on one import path (`import easy_memory` would load the package, not the shim). The package needs another name (for example `easy_memory_core/`), or the shim moves its code into `easy_memory/__init__.py` and the installer writes `python -m`. Decide at Stage 2; the first keeps F4 with no installer change.
- Standard library only. The Retriever seam has one implementation: today's scorer.
- Acceptance: the same 307 tests pass with the same names and skips; `tests/bench_t004.py` p95 does not get worse.

### R2 — Portable store key (store format v2)

- Identity, in order: (1) the repo's root commit (`git rev-list --max-parents=0 HEAD`, lowest hash if there are several); (2) the normalized `origin` URL; (3) today's path key.
- A shallow clone reports its shallow boundary as the root. When `git rev-parse --is-shallow-repository` is true, skip (1).
- Cache path → key in `<store root>/keys.json` (0600), because the extra git call costs hook time.
- Migration: on first use, move the old path-keyed folder to the new key, write `moved.json` in place of the old one, and log it. Never delete. A v1 reader skips the v2 store marker (NFR-007).
- Two clones of one repo on one machine now share a store. This matches the A1 worktree rule.
- Acceptance: the same repo at two paths gets one key; a shallow clone falls back to (2); migration keeps every note; p95 of the prompt hook within NFR-001.

### R3 — Secret redaction at save

- The Stop hook redacts `prompt` and `answer` before `write_note`. Each hit becomes `[REDACTED:<kind>]`.
- Patterns (deterministic, no model): private key blocks, AWS access key ids, GitHub tokens (`ghp_`, `gho_`, `github_pat_`), Slack tokens (`xox?-`), `sk-` and `sk-ant-` API keys, JWTs, `Authorization: Bearer ...`, and `NAME=value` / `NAME: value` lines where NAME contains `SECRET`, `TOKEN`, `PASSWORD`, `PASSWD` or `API_KEY`.
- Cited-file hashes are unchanged; redaction touches only stored text.
- A one-time `redact [--dry-run]` command rewrites existing notes by temp file + rename (Question 3).
- Effect on the measurement: removed strings are secrets, which almost never match a prompt's words, so the score change is negligible. The log records the redaction release date anyway.
- Acceptance: a fixture set with one sample per pattern is fully redacted; a fixture with no secrets is byte-identical; Stop hook stays ≤ 2 s.

---

## Edge Case Checklist (goes into each task guide)

- E1 Shallow clone: root commit is the shallow boundary; fall back to `origin` (R2).
- E2 Repo with several root commits (merged histories): pick the lowest hash, so every machine agrees (R2).
- E3 No git, or git missing: path key, as today (R2).
- E4 Two machines migrate the same store at once after a later sync: a move is per machine and local; sync code must ignore `moved.json` (R2, sync task).
- E5 A secret split across two lines, or inside a code block: the patterns match per line; a split key is a known miss and stays documented (R3).
- E6 False positive: a normal word line such as `TOKEN_LIMIT=4000` is redacted. Accepted cost: notes are data, and a redacted number does not mislead (R3).
- E7 A test patch that pointed at the old module stops working silently after the split (R1, F3).

---

## Surgical Scope

Should be changed (implementation round, not this PR): `easy_memory.py`, a new package folder, `tests/`.
Must not be touched: `experiments/` (read-only evidence), the scorer's behaviour and the 0.12 floor (gated), any file inside an observed repo (FR-002), the user's settings except through the installer.

---

## Recommended Path

**Option B — Foundations first, gated features.** Build R1, R2 and R3 during the 2-week v0.1 measurement. Start the gated features only after the gates in `PRD_v0.2.md` pass.

## Next Actions for Stage 2

1. User confirms `PRD_v0.2.md` and answers Questions 1 to 3.
2. Create three Linear issues (team HUN, project easy-memory-mcp) for R1, R2 and R3, then `python3 scripts/board_sync.py pull`.
3. Order: R1 → R2 → R3. R3 can run in parallel with R2 after R1 merges.
4. Record the v0.1 measurement window start date (the v0.1.0 install date) in `RUNBOOK.md`.
