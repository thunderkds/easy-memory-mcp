# decisions.md — Cold Tier: Architectural & Infrastructure Decisions

> **Rules**: Supervisor-only writes. Each entry: `### YYYY-MM-DD — Title`, then **Decision**, **Why**, and **Files** (cite paths — the diff-driven pass greps this file by changed file path).

## Architecture

### 2026-10-28 — Implementation path C: single-file, stdlib-only prototype
**Decision**: Build one Python module with subcommands (`hook-stop`, `hook-prompt`, `serve`, `report`, `install`, `uninstall`). Hand-written stdio MCP server (4 tools). Notes are one JSON file each under `~/.easy-memory/`, written by temp file + atomic rename. Word weights come from the repo's own files (as in experiment 03), built in a background process and read by the hook, never built inside it. One note per Stop turn (answer ≥200 chars). Injected index ≤2,500 characters. Worktrees share the main repo's store.
**Why**: Building weights on orderly (7,835 files) took 16.5 s and gave a 16 MB file that takes 0.3 s to load; NFR-001 allows 1 s. The `mcp` SDK is not installed, and NFR-005 forbids dependencies. Keeping experiment 03's scorer keeps its evidence (−28% tokens, 0 misled) valid. Rejected: A (SDK port, latency and dependency), B (SQLite FTS5, changes the validated scorer).
**Files**: `BRAINSTORMING_LOG.md`, `PRD.md`, `experiments/02-auto-memory/memstore.py` (scorer to port), `experiments/03-precision/precision.py` (index to port)

### 2026-10-28 — Word weights keep words found in at least 3 files
**Decision**: `MIN_FILES_PER_WORD = 3` in `easy_memory.py`, not the guide's 2. On orderly, 2 gave a 3.61 MB `weights.json` (limit 2 MB, AC2); 3 gives 1.69 MB, loads in 0.024 s, and passes the parity check (99.5% of score pairs, 96.3% of top-5 orders).
**Why**: AC1 says drop words found in one file, AC2 caps the file at 2 MB; only 3 meets both. The 0.12 floor was not changed.
**Files**: `easy_memory.py`, `tests/parity_t003.py`, `tasks/TASK_GUIDE_HUN-76.md`

### 2026-10-29 — v0.2 plan: redaction only now, everything else gated (Option B2)
**Decision**: Only FR-009 (secret redaction at save, plus a `redact` command, dry-run by default) ships during the v0.1 on/off measurement. The package split (FR-011, package `easy_memory_core/`) is built in a worktree and merged when Gate 1 opens. The portable store key (FR-010) is deferred with sync. Gate 2 splits into 2a (decay, expiry) and 2b (optional embedder in `memory_search` only). Gate 3 (other clients) is removed.
**Why**: A three-agent review found the hooks run live from this checkout, so a merge changes the measured hooks on the next prompt. A key change moves `config.json`, `prompts.log` and `weights.json`, which are the measured data. Root-commit keys can merge unrelated forks. The user chose Claude only on 2026-10-28.
**Files**: `PRD_v0.2.md`, `BRAINSTORMING_LOG_v0.2.md`, `RUNBOOK.md` (commit 109d96e). Confirmed by the user on 2026-10-29.
**Status**: Gate 0 shipped 2026-10-29T08:03:51Z (merge `0ffe6f2`, HUN-84..87): `redact_text` in `save_stop_note` and the `redact [--repo] [--apply]` command in `easy_memory.py`, tests in `tests/test_t010_redact.py`. O5 done by HUN-122 (merge `6f0db14`): `report` groups only sessions whose first `prompts.log` line has `configured == "auto"` and prints `forced switch: N (left out of the comparison)`; the "too few" rule now measures the sample bar directly. Next: wait for the sample bar (10 auto sessions per group in one repo), then Gate 1.

### 2026-10-29 — Release page uses the Easy Kit family Graphite Mint theme
**Decision**: `site/index.html` follows the user's Claude Docs spec "Easy Kit family — Graphite Mint implementation spec" (https://claude.ai/artifact/3mXfGbwzZz89WjKWsT4WAz), Easy Memory section: graphite `--bg` #121413, IBM Plex Sans/Mono from Google Fonts, one mint accent #7EDDB0, 1px hairlines, no gradients/glows/shadows; 64px header with family nav (Easy Memory `aria-current`), 248px sidebar with `// group` labels. HUN-125 (merge `177d82c`) replaced the HUN-123 dark indigo look the same day.
**Why**: the user set one theme for all three family sites (Easy Kit, Easy Memory, Easy Verifier).
**Update (HUN-127, merge `fcd3428`)**: user feedback the same day — the page sits in a centred 1280px container (`--container-max`, page style, not theme.css); sections lead with pictures (flow SVG for How it works, wide + tall copies; Install stepper; switch day-strip; Measured bar chart vs limits) with the main path in mint and other prose folded into one `<details>` "More detail" per section (visible words 1377 → 650); release notes are highlights grouped save/recall/control/measure/install with no task IDs; "How it was built" removed. Prefer pictures plus short captions over prose on this page.
**Update (HUN-130, merge `816222a`)**: spec rev 25 adds a neon layer — `--neon` #3CF5A8 with `--neon-soft/-line/-bar` and `--glow-text/-box/-dot/-line`; `--accent` #7EDDB0 stays for links, hover and focus; `--accent-soft`/`--accent-line` are gone. Neon + glow only on the spec's "Neon highlights" list (active nav, current-site dot, header glyph, eyebrow, step numbers, primary/Copy buttons, key numbers, exp 03 card, main-path strokes, bar fills; `$` prompts neon without glow); `html.no-glow` zeroes every glow token; no visible toggle (cut). Budget "about 6 neon elements per screen": the user accepted 7 on the Remove-it stop (a code box with its Copy button counted as one). The canvas https://claude.ai/artifact/5jKFUHLaGJTPK4KgazQ2o1 is older than HUN-127: take its neon look only, not its layout or copy. `--text-dim` #6E7772 is still 4.0:1 in rev 25.
**Update (HUN-133, merge `45d3068`)**: from 720px up the Install stepper's step items use `grid-template-rows: subgrid` (span 4) so the three code boxes share one height, Copy buttons align at the bottom and captions align; below 720px steps stack and boxes size to content.
**Files**: `site/theme.css` (the spec `:root` block byte-identical, plus its component CSS; the other two sites must copy the same block, repos cannot share one file), `site/index.html`, `tests/test_site_page.py` (24 tests). Spec issue found: `--text-dim` #6E7772 is 4.0:1 on `--bg`, under the spec's own 4.5:1 rule; the page does not use it for text.

### 2026-10-31 — Index ranking stays as on main; HUN-140 rare-word gate shelved
**Decision**: Do not merge HUN-140 (branch `v03-m5-ranking`) in any tried form; `main` keeps its ranking. HUN-140 moved back to Todo on Linear with the evidence comment.
**Why**: Offline recall check `experiments/06-hun140-recall/` (branch `exp-06-hun140-recall` @ `1d1d50f`, not merged): two blind labellers (kappa 0.87 on relevant-or-not), 486 sampled lines plus a 329-line holdout. Bar fixed before scoring: keep ≥90% of main's relevant index lines, 95% lower bound ≥80%. As built (`RARE_SHARE` 0.10, `BM25_B` 0.75): 65% [50, 82]. Rework V3 (gate only when rare words carry < 0.6 of prompt idf weight, `aec0013`): 67% [51, 83], 0 of 26 holdout relevant lines kept; its first pass came from one line in a 20-prompt sample (selection on 9 variants). Length rule alone: 86% [74, 98] and fails V-R4 AC 1. `RARE_SHARE` 0.30 + `BM25_B` 0.25 breaks AC 1–3. Trade-off: V-R4 costs ~1 extra index line (~60 tokens) per prompt, which exp 03 found the agent ignores; a missed relevant note cost 21k → 113k tokens in exp 03. Also rejected in the same pass: claude-mem's document-frequency cutoff (exp 05, branch `exp-05-df-cutoff`: −29% wrong lines, 78% recall on real prompts, 52% on scripted).
**Lesson**: a ranking change that can hide notes must pass a holdout that was not used to pick it; the labelled pool in exp 06 is the reusable benchmark.
**Files**: `easy_memory.py` (`score`, `_index_lines`), `experiments/05-df-cutoff/`, `experiments/06-hun140-recall/`, `tasks/TASK_GUIDE_HUN-140.md`

### 2026-10-31 — Forget is recoverable: trash + memory_restore (HUN-135 merged)
**Decision**: `memory_forget` moves the note to `<store>/trash/` (0700; file 0600; mtime = move time); `memory_restore` moves it back and never overwrites; trash files older than 30 days (`TRASH_KEEP_DAYS`) are purged at the next forget; `redact` (dry run and `--apply`) covers `trash/`; forget, restore and redact refuse a symlinked `trash/`.
**Why**: verifier V-R5 (forget was irreversible); user chose trash + restore, 30 days. Debate re-run 2026-10-31 with 3 Advocates: redact must cover trash (AC 7, "secret must not survive a forget").
**Open (Low)**: a secret stays in clear text in the trash up to 30 days after a forget; `redact --apply` removes it at once.
**Files**: `easy_memory.py` (`_tool_forget`, `_tool_restore`, `redact_command`), `tests/test_v03_m6_trash.py`, `README.md`

### 2026-11-03 — report.json for easy-personal (HUN-197 merged)
**Decision**: `report --json [--repo R]` prints the FR-015 object (format `v` 1, numbers/flags/time only) and writes `<store>/report.json` (0600, atomic). After a saved note, the Stop hook spawns a detached `report --json --release-lock` when the file is missing or >1 h old and `<store>/report.lock` is free (O_EXCL, 10-min stale); a future mtime counts as fresh. Text `report` output unchanged (split into `_report_numbers` + printer). Supersedes PRD.md A7 for this one file; easy-personal reads it directly (XR-1, its own board).
**Why**: user 2026-11-03 "give the easy-personal the number ... to show on the dashboard"; one copy of the on/off join logic. Exp 07 (TokenEconomizer envfacts) failed, kept on branch `exp-07-envfacts`, not merged.
**Follow-ups**: HUN-199 merged 2026-11-03: `report --json --repo <not a folder>` returns 1 and writes nothing; `no_data` (counts only the refreshing checkout's logs) documented in README, not changed (Gate 2a). Consumer HUN-198 merged in easy-personal-mcp (`63271cf`, its FR-066): Memory panel block reads `report.json`, abstains on `v` > 1.
**Files**: `easy_memory.py` (`_refresh_report`, `_report_numbers`, `_report_object`, `report_command`, `hook_stop`), `tests/test_v04_report_json.py`, `PRD_v0.4.md`, `README.md`

### 2026-11-04 — Prompt hook splits each word once per run (HUN-208 merged)
**Decision**: `tokens()` uses `_word_parts(word)` (`functools.lru_cache(maxsize=1<<16)`); `_index_lines` builds the prompt's weight map once (`_prompt_weight`) and scores each note with `_score_with`; `score()` is a thin wrapper. Ranking byte-identical (golden sha256 test, real store check). No saved word-count cache, no retention limit (user 2026-11-04, picked from 3 options).
**Why**: defect D1. cProfile: `tokens()` was ~97% of scoring; the prompt was re-split per note. Results: 4,000-note probe max 1.62 s → 0.41 s (probe now passes); real 440-note store hook 290 → 145 ms; weights build 1.7 → 0.4 s, same df.
**Follow-ups**: P2 (cache bounded entries, not bytes) fixed by HUN-210, merged 2026-11-04: words over `WORD_CACHE_MAX_CHARS` (64) bypass the cache; full cache ~46 MB worst case; `serve` with 1,600 distinct 20,000-char query words stays at 35 MB (was 95 MB). Lower `maxsize` in a later task if 46 MB matters. Pre-existing: a 1.7 MB prompt of 150k distinct words still takes 17.4 s (hook timeout 5 s) — HUN-211 (Todo) caps prompt words; ask the user about Gate 2a before its merge. Still linear in notes: a saved cache file is the next step if a store nears ~3,000 notes.
**Files**: `easy_memory.py` (`_word_parts`, `tokens`, `_prompt_weight`, `_score_with`, `score`, `_index_lines`), `tests/test_prompt_word_split.py`, `tests/test_t004_hook_prompt.py`, `tests/test_t005_switch.py`, `tests/test_word_cache_bound.py` (HUN-210)

## Infrastructure

### 2026-10-28 — easy-verifier registered as the scoring MCP (dev tool)
**Decision**: Register the user's running `easy-verifier` container as a project-scoped HTTP MCP in `.mcp.json` (`http://127.0.0.1:8766/mcp`) for Stage 4/5 scoring. No install: the user already runs it (container `2685b68319b9`, `~/workspace` mounted read-only, reports to `~/.easy-verifier-reports`). Not a product dependency.
**Why**: User request "adding the easy-verifier as a scoring mcp". A `pipx install` from `main` was declined by the user.
**Files**: `.mcp.json`, `PROJECT_SPEC.md`


### 2026-10-28 — Linear is the source of truth for tasks
**Decision**: Tasks `HUN-74`..`HUN-82` live in Linear (team HUN, project easy-memory-mcp). Each issue description is the task guide. `PROJECT_KANBAN.md` and `tasks/TASK_GUIDE_<ID>.md` are a cache rewritten by `python3 scripts/board_sync.py pull`; `PROJECT_SPEC.md` lists no tasks. `.claude/board.json` (board mode `online`) holds no secret; `LINEAR_API_KEY` stays in the shell.
**Why**: User instruction "use Linear as the source of truth, remove the local tasks". Linear assigns the IDs, so the draft `T001`..`T009` labels were replaced.
**Files**: `.claude/board.json`, `scripts/board_sync.py`, `PROJECT_SPEC.md`, `PROJECT_KANBAN.md`, `tasks/`

