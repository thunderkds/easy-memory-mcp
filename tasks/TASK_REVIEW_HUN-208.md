# TASK_REVIEW — HUN-208: Prompt hook splits each word once per run, with the same ranking

> Sibling of `tasks/TASK_GUIDE_HUN-208.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

<!-- Optional: the final report, only for a task run in auto mode (the user's `[auto]` tag,
`docs/claude-md/tracks.md` `## Auto mode`). To use it, copy the block below out of this comment, to this
place, and replace every <...>. Keep `Mode: auto` as its first line, exactly as written: T182's hook reads
it. Write it to this file before the run ends; the chat message is a copy, not the report. The same
block is the Supervisor's final chat message. It is not the `delivery-report` page and not
Evidence. A taste decision (what the user wants) also ends with the flag. Write `DEBATED` only when ≥2
Advocate `Agent` calls ran for that question, naming each Advocate's option. A decision with no Advocates is
labelled `RULE`, `FACT` or `SAFER OPTION`, never `DEBATED`. A decision flagged `⚠ decided for you` is a choice, and is never labelled `FACT`. A
safety action a rule requires (for example the backup before a delete) is `RULE` without the flag.
At Risk Medium or High, a `RULE:` counts only when it names a written rule (`path:line`,
`path § <heading>`, or `docs/claude-md/tracks.md` `### <section>`), and a `FACT:` needs a Citation
(`path:line "quoted text"`); without one it is a choice and must be `DEBATED`. Good: `2. backed up the CSV
— RULE: `docs/claude-md/tracks.md` `### Stops that stay``. Bad: `1. kept recurring.csv — RULE: Surgical Changes`.

## Auto decisions

Mode: auto
1. <what was decided> — RULE: <the rule>
2. <what was decided> — FACT: <path>:<line> "<quoted text>"
3. <what was decided> — DEBATED: <option> (Advocate 1: <its option>; Advocate 2: <its option>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
Checks: tests `<command>` — <result>; reviews <skill — result>; real run `<command>` — printed `<what it printed>` (auto-checked, not /verify)
Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>

-->

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_prompt_word_split.py` (11 tests: AC1 tokens vs frozen old, AC2 score places=12, AC3 golden sha256 `ddd6af73…`, AC4 prompt split once in `_index_lines` and `_tool_search`, AC6 no new store file, AC8 cache bound). Supervisor run 2026-11-04 in the worktree: `Ran 510 tests in 30.453s` / `OK (skipped=3)` — pass |
| Verification command run | ☑ pass | Supervisor, 2026-11-04: `python3 -m unittest discover -s tests` → `Ran 510 tests` `OK (skipped=3)`; `HUN82_GROWTH_PROBE=1 python3 -m unittest tests.test_t009_smoke.StoreGrowthProbeTest` → `[HUN-82 growth probe] notes=4000 hook-prompt p50=0.396s max=0.408s` `OK` — pass |
| Negative cases hold | ☑ pass | /verify probes on the real CLI: empty prompt, slash command, garbage stdin (one `hook.log` line), non-ASCII prompt → rc 0, no stdout; 2M-char word: main 18.8 s → branch 0.24 s, identical stdout; 150k distinct words: main 171.7 s → branch 17.4 s, identical stdout (still over the 5 s hook timeout — pre-existing, follow-up) — pass |
| verify | ☑ pass | `/verify` run by the user's command 2026-11-04, Supervisor drove it: copy of the real `personal-agentic-claude` store (440 notes) under a temp `EASY_MEMORY_HOME`; `hook-prompt` main 288-298 ms → branch 143-151 ms, stdout byte-identical; MCP `serve` `memory_search` x3 replies byte-identical; real store untouched — verdict PASS |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | `easy_memory.py` `tokens`/`_word_parts`/`_prompt_weight`/`_score_with`/`score`/`_index_lines` and callers `_tool_search`, `prompt_index`, `_count_words` (weights build: df sha identical, 1.7 s → 0.4 s on personal-agentic-claude); 2 edited tests. lane_check: `C2, 6 files, 447 lines, FITS; unpredicted: tasks/TASK_GUIDE_HUN-208.md, tests/test_t004_hook_prompt.py, tests/test_t005_switch.py`. Code review: 0 P0; P1 process (agent skipped `agents/backend.md` startup read — recorded); P2 cache bounded by entries not bytes, 28.6 MB full, comment says "a few MB" — accepted by user 2026-11-04 ("merge it as is"), follow-up. Security review (independent read-only agent; built-in needs `origin/HEAD`): no P0/P1, same P3 — pass |
| Full smoke suite still green (no regression) | ☑ pass | 499 baseline tests still pass inside the 510 — pass |
| **Companion score (easy-verifier)** | ☑ N/A | not run for this task |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | backend only |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | backend only |
| **UI: Responsiveness at target viewports** | ☑ N/A | backend only |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-11-04T06:16:30Z on `main` (0bbf1cb), unchanged `easy_memory.py`:

```
$ date -u +%Y-%m-%dT%H:%M:%SZ && HUN82_GROWTH_PROBE=1 python3 -m unittest tests.test_t009_smoke.StoreGrowthProbeTest
2026-11-04T06:16:30Z
[HUN-82 growth probe] notes=4000 hook-prompt p50=1.532s max=1.620s
FAIL: test_prompt_hook_p95_stays_under_1_second_with_4000_notes
AssertionError: 1.6196922069993889 not less than 1.0 : NFR-001: hook-prompt must add at most 1 s
Ran 1 test in 8.211s
FAILED (failures=1)
```

AC3 golden `_index_lines` output, captured 2026-11-04T06:17:37Z from the unchanged `easy_memory.py` (60-note fixture of `tests/test_prompt_word_split.py`, 5 prompts, `fake_weights()`): 5 lines for each of the 5 prompts; sha256 of the joined output `ddd6af7376b21710ae33c45bc1dd8eed83f172e1ff8b54012f5f11399e0c3c98` (identical on 3 runs; now `IndexLinesTest.GOLDEN_SHA256`). First line of prompt 1:
`- id 20261001T000000058-0000003a | question: "and loader snake_case_name database authService database" | first line: "session Auth ab authService and token ..." | cites: none`

**AFTER**: captured 2026-11-04T06:19:18Z on branch `prompt-hook-word-split`, same machine, same session:

```
$ HUN82_GROWTH_PROBE=1 python3 -m unittest tests.test_t009_smoke.StoreGrowthProbeTest
[HUN-82 growth probe] notes=4000 hook-prompt p50=0.409s max=0.414s
Ran 1 test in 2.508s
OK
```

max 1.620 s to 0.414 s (3.9x lower); the probe's own 1 s assertion now passes too. Full suite: `Ran 510 tests ... OK (skipped=3)` (499 + 11 new in `tests/test_prompt_word_split.py`).

**DELTA**: The prompt hook and `memory_search` return the same notes about 2-4x faster (real 440-note store 290 ms → 145 ms; 4,000 notes 1.62 s → 0.41 s, now inside NFR-001's 1 s).

**WITNESS**: Supervisor, 2026-11-04 ~08:46Z: re-ran the suite and probe in the worktree, timed main vs branch on the real store (read-only) and drove `/verify` on a store copy; independent of the implementing agent.
