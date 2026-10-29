# BRAINSTORMING_LOG_v0.2.md
**Generated**: 2026-10-28
**Task / Context**: Easy Memory enhancement plan (v0.2 to v0.4), feasibility review against `easy_memory.py` at `36c8ce4`
**Skill**: `Skill({ skill: "brainstorming" })`
**Status**: Draft 2 (round 2 review on 2026-10-29, see "Round 2" at the end). User approved "plan first" on 2026-10-28. No code changes until this log and `PRD_v0.2.md` are confirmed.
**Round 1 below is kept as history.** Where round 2 contradicts it, round 2 wins. Superseded: R1 and R2 as "safe now", the order R1 → R2 → R3, edge case E5, and the claim that the split moves "about 150 lines".

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

1. Confirm the gate: the scorer, decay and vector work wait until the v0.1 report is in. Round 2: the gate is the sample bar (10 `configured==auto` sessions per group), not "2 weeks". ANSWERED yes 2026-10-29 (user confirmed PRD draft 2).
2. ~~Sync: git remote or folder sync only?~~ ANSWERED 2026-10-28: defer the sync feature. No sync work in v0.2. R2 stays, because the portable key also helps clones and is cheapest to migrate now.
3. A6 changes from "not scrubbed" to "redacted at save". Should a one-time `redact` command also rewrite the notes already saved? Recommendation: yes, with `--dry-run`, because v0.1 notes may already hold secrets. Round 2: dry-run is the default and ANSWERED yes 2026-10-29 (user confirmed PRD draft 2).

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

## Recommended Path (round 1, superseded)

Option B: build R1, R2 and R3 during the measurement. Replaced by Option B2 below.

---

# Round 2 (2026-10-29): three-agent review

**Tier**: Deep. FR-010 changes where stores live, and the safe-now claim touched the live measurement.
**Method**: three read-only agents, one lens each (key, redaction and split, gates and measurement). Their reports are model output. The Supervisor checked the facts marked "checked" against the files.

## Round 2 facts

| # | Fact | Evidence | State |
|---|---|---|---|
| F9 | The hooks are live and run this checkout. A merge changes the measured hooks on the next prompt. | `~/.claude-personal/settings.json` lines 56 and 75 | checked |
| F10 | `RUNBOOK.md` still says "not yet installed", so no window start date exists. | `RUNBOOK.md:76` | checked |
| F11 | The on/off switch, `prompts.log` and `weights.json` live inside the keyed store. A key change moves the measured data. | `easy_memory.py:394-410`, `:654`, `:668`, `:695` | checked |
| F12 | `report` groups sessions by `effective`. The lines seen do not filter on `configured`. | `easy_memory.py:1209-1220` | checked (filter absence: agent finding, to verify) |
| F13 | The sample floor is 10 sessions per group. | `easy_memory.py:1063`, `:1241` | checked |
| F14 | The 24 patch sites match. 13 patch module attributes. | `tests/` grep: 5+4+3+2+5+3+2 | count checked, the 13 is an agent finding |
| F15 | The file is 1,567 lines. About 1,500 lines move in the split. | `wc -l`; per-module table from the agent | file size checked, table is an estimate |
| F16 | `_index_lines` reads and scores every note on every prompt. `memory_forget` is a bare `os.unlink` with no prompt. | `easy_memory.py:581`, `:1399` | checked |
| F17 | `serve` uses `os.getcwd()`. MCP has no write tool, so notes come only from Claude's Stop hook. | `easy_memory.py:1497`, PRD FR-005 | checked |
| F18 | Experiment 03's `work/` data is not in the repo. | `ls experiments/03-precision` | checked |
| F19 | The report's verdict line uses all four usage counts. PRD FR-007 says input + output. | `easy_memory.py:1263-1265`, `PRD.md:52` | checked |
| F20 | `tests/parity_t003.py` is a parity check of compact against full weights (two candidate sets). An embedder is meant to differ, so it cannot use that bar. | `tests/parity_t003.py` header | read; the 95% figure is an agent finding |

## Round 2 options

| Option | Name | Summary | Regression risk | Recommended? |
|--------|------|---------|-----------------|--------------|
| B | Round 1 plan | Split, portable key and redaction all built during the window | Medium: moves the measured data (F11), live hooks run the checkout (F9) | |
| B2 | Redaction only now | FR-009 ships in the window. Split is built in a worktree and merged at Gate 1. Key is deferred. | Low | ✅ Yes |
| B3 | Redaction plus split now | As B2 but the split merges at once | Medium: a half-merged split breaks live hooks | |

**B2 cut list** (50% rule): FR-010, `keys.json`, `moved.json`, format v2, A8, the `Retriever` seam until FR-013, Gate 3 and the 4-gate table replaced by Gates 0, 1, 2a and 2b.

## Round 2 adversarial review

- **FR-010 (key)**: worst contamination of the measurement (F11). Unstable after the first commit, after history rewrites and after an `origin` change. Forks and templates share a root commit, so unrelated repos can merge notes. Concurrent hooks may lose log lines during a move. Cut. Cheaper idea kept: an opt-in `alias.json`.
- **FR-009 (redaction)**: sound. Round 1's E5 was wrong: a private key block is easy to match across lines with one whole-text regex. A `|\Z` fallback was quadratic (7 s at 224 KB). Use `|.*`. The `NAME: value` rule eats lines like `token: string`, so restrict it. The `sk-` rule needs a look-behind. It does not leave the measurement untouched: it removes whole `TOKEN: …` style lines.
- **FR-011 (split)**: safe to build, unsafe to merge mid-window. Silent test failure is the main risk: a patch left on the shim passes without testing anything. The shim must exit 0 on `ImportError` for hook commands.
- **Gates**: "passes when user confirms" is circular. "2 weeks" has no anchor (F10). A positive-only Gate 2 blocks the fix when the result is bad. Any automatic expiry changes the candidate set, so it is a ranking change. The "HUN-76 parity bar" cannot apply to an embedder (F20).

## Edge cases: changes

- **E5 (replaces round 1 E5)**: a private key block spans lines and is matched by one whole-text regex. A key split over two lines in any other pattern is a known miss, documented in A6.
- E1 to E4 belong to FR-010. They are kept for a later sync round.
- E7 stays: a test patch that points at the shim stops testing silently. Mitigation: a guard test on `vars()` of the target module.
- **E8**: unterminated `BEGIN PRIVATE KEY` redacts to the end of the text (fail closed).
- **E9**: redaction raises an error. The hook writes no note and logs it. It never saves unredacted text.
- **E10**: `redact --apply` run twice. The second run changes no byte.
- **E11**: `redact` dry-run output never shows matched text.
- **E12**: the shim cannot import the package. Hook commands exit 0 and the prompt goes through unchanged.
- **E13**: `__file__` in moved code points at a module, not the shim. The hook respawn path must stay the shim path.

## Surgical Scope (round 2)

- **Gate 0** may change: `easy_memory.py` (redaction function, `save_stop_note`, a `redact` subcommand), `tests/` (new redaction tests), `RUNBOOK.md` (dates).
- **Gate 0** must not change: the scorer, `INDEX_*` constants, store key and layout, the switch, `report`, any file in `experiments/`.
- **FR-011** is built on a branch or worktree, not in the live checkout, until Gate 1.

## Recommended Path (round 2)

**Option B2.** Ship FR-009 and the `redact` command during the window. Record the dates. Build the split in a worktree. Open Gates 1, 2a and 2b only when `PRD_v0.2.md` says so.

## Next Actions for Stage 2

1. DONE 2026-10-29: the user confirmed `PRD_v0.2.md` (draft 2), which answers Questions 1 and 3 and the package name.
2. DONE 2026-10-29: install time and window start are in `RUNBOOK.md` (open item O1).
3. Create Linear issues (team HUN, project easy-memory-mcp): FR-009 redaction hook plus fixtures plus ReDoS test; the `redact` command; the `configured == auto` report filter (O5). Then `python3 scripts/board_sync.py pull`.
4. Order: redaction hook → `redact` command. The report filter is independent.
5. Create the FR-011 split issue now but keep it out of the live checkout until Gate 1.
6. Ask the user for experiment 03's `work/` data (O2) and the metric column (O3) before Gate 2a.
