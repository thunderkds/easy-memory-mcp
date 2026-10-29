# TASK_REVIEW — HUN-127: Release page — centred container, visual guide, highlight-only release notes

> Sibling of `tasks/TASK_GUIDE_HUN-127.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_site_page.py` (30 tests; 10 of them fail on the old page, 20 old/kept). New: container (AC1), flow SVG role=img + aria-label + 5 mint / 3 neutral line paths (AC2), stepper 01-02-03-end with 3 codeboxes (AC3), day strip on/off x4 + 4 commands (AC4), 4 roll-back chips (AC5), bar chart widths 21.2 / 3.3 and stat cells (AC6), one `<details>` "More detail" at the end of each of 8 sections (AC7), no `HUN-` + five release-note groups (AC8), no `built` section or link (AC9). Test-first note: the page was written before the tests; the new tests were then run against the old page (commit 3c19c69) and failed 10 + 1 error, then passed on the new one. |
| Verification command run | ☑ pass | `python3 -m unittest tests.test_site_page -v` -> `Ran 30 tests in 0.016s` `OK`. `python3 -m unittest discover -s tests` -> `Ran 408 tests in 24.698s` `OK (skipped=3)`. |
| Negative cases hold | ☑ pass | `grep -rnE "HUN-\|#built" site/` printed nothing (exit 1). `git diff 97d7cd1 -- site/theme.css` empty (tokens byte-identical). No colour literal outside the token block, no gradient, shadow, filter, transition, animation, dasharray (existing tests, still green). Number check: all 38 distinct numbers of the old `<main>` (minus task IDs and the built section) appear on the new page; commands present (they differ only by the `$ ` prompt span in my naive text diff): /tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun127/fact-check.txt |
| verify | ☑ pass | Browser run through CDP on `http://127.0.0.1:8791/index.html` (log: /tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun127/verify-after.txt; 0 script errors): no horizontal page scroll at 1920, 1440, 1280, 1279, 1024, 768, 375 (docScroll == client); details toggle by Enter and Space, focus ring `solid rgb(126, 221, 176)`; Copy step 1 -> button "Copied", clipboard `git clone git@github.com:thunderkds/easy-memory-mcp.git
cd easy-memory-mcp
python3 -m unittest discover -s tests`; scroll-spy marks what, context, how, run, use, rollback, numbers, limits, notes in order, and `#notes` at the page end (see Review notes: this needed a small JS fix after #built was removed); skip link first Tab -> `#main`; drawer opens/Esc closes at 768 and 375, drawer shows the family links; 44 px tap targets at 375 (menu items, summary, Copy). Result: pass. The Skill tool was not available to this agent, so `code-review` and the `verify` skill were not run; the Supervisor runs them. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Reviewed only `site/index.html` (page style, markup, script) and `tests/test_site_page.py`. Not touched: `site/theme.css`, `easy_memory.py`, other tests, other sites. |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m unittest discover -s tests` -> `Ran 408 tests in 24.698s`, `OK (skipped=3)` |
| **Companion score (easy-verifier)** | ☑ N/A | Not run: no MCP tool in this agent's session; static page task. |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | Before/after full-page screenshots at 1920, 1440, 1024, 768, 375 in /tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun127: `before-<w>.png` vs `after-<w>.png`; zoomed section crops `clip-<w>-<section>.png` (how, run, use, numbers at 375, 768, 1440) and `open-<w>-<section>.png` (details open). Verdict from looking at them: the page is now mostly pictures with a short caption (flow, stepper, day strip, bar chart); the mint flow and the mint install line read at a glance; page height 5430 -> 4481 px at 1440. Word count of `<main>` (same script on both pages; visible text outside `code`, `pre`, `details`, hidden nodes; SVG text counted): before **1377**, after **650** = 47.2% (<= 50%); at 375 646. Screenshots are full-height captures, so the scrollbar paints only in the 1920/1440/1024 ones (`scroll [1905,1920]`). |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | Method: unit tests (no colour literal in the page style or markup, no gradient/shadow/filter/animation, weights <= 600, no text-transform, only Plex via tokens) + contrast computed from the token values: text-muted on bg 6.01:1, on bg-sunken 6.20:1, accent on bg 11.33:1; the `off` day word was text-dim (4.00:1) and was changed to text-muted (6.01:1). Mint marks only the main path: flow arrows and node borders (`--accent`, `--accent-line`), stepper line, `on` days, bar fill, step numbers; side paths use `--text-dim` strokes (4.00:1 graphic, >= 3:1) and node borders `--line-strong`. Deviation from AC2 wording: side-path lines use `--text-dim` instead of `--line-strong`, because `--line-strong` (#2C3230 on #121413) is nearly invisible; still a neutral token. Chart bar height is 10 px (spec progress bar is 6 px); the track is `--line-header` as the spec says. |
| **UI: Responsiveness at target viewports** | ☑ pass | 1920, 1440, 1024, 768, 375 (+1280, 1279, 720, 719 for the flow switch). Container: at 1920 header-inner and shell both `[312.5, 1592.5]` width 1280 (centred, edges identical); at 1440 both `[72.5, 1352.5]` width 1280; at <= 1280 both fill the viewport as before; header hairline stays full-bleed (`[0,1905]`). No element overflows the viewport in `main` (list empty at every width). Flow: wide layout >= 800 px, top-to-bottom layout below (text 12 px at rendered scale; wide at 800 is 0.9 scale); stepper stacks below 720 px with a vertical mint line; day strip 8 -> 4 columns; command list one column; release notes one column. Log: /tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun127/verify-after.txt |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured 2026-10-29T11:09:38Z, page unchanged at `main` 97d7cd1, no implementation commit yet; `date -u` printed `Thu Oct 29 11:09:38 AM UTC 2026`; fact inventory saved `11:10:03Z`):
Full-page screenshots, via CDP `node /tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun127/shots.mjs` (the viewport is as tall as the page, so no scrollbar paints; width and overflow come from the numbers below):
- /tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun127/before-1920.png, before-1440.png, before-1024.png, before-768.png, before-375.png
- Measurement log: /tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun127/before-measure.txt
- Fact inventory (every block, number and command of the current page): /tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun127/before-facts.txt (142 lines)

Measured (left, right, width in px), unchanged page:
```
1920 scroll [1920,1920] shell [0,1920,1920] brand [32,173,141] GitHub btn [1813,1888,75] main [248,1920,1672] words 1377
1440 scroll [1440,1440] shell [0,1440,1440] brand [32,173,141] GitHub btn [1333,1408,75] main [248,1440,1192] words 1377
1024 scroll [1024,1024] shell [0,1024,1024] main [248,1024,776] words 1377
 768 scroll [768,768]   main [0,768,768]  words 1377
 375 scroll [375,375]   main [0,375,375]  words 1377
```
Finding: the shell and header content grow with the screen (1920 px wide at 1920). Visible word count of `<main>` before: **1377** (text nodes outside `code`, `pre`, `details`; `display:none` and `visibility:hidden` skipped; SVG text will be counted after).

**AFTER** (same measurement script, `node /tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun127/shots.mjs`, page at commit 71d109d + this file):
```
1920 scroll [1905,1920] shell [313,1593,1280] brand [346,486,141] GitHub btn [1484,1560,75] main [562,1592,1030] words 650
1440 scroll [1425,1440] shell [73,1353,1280] main [322,1352,1030] words 650
1024 scroll [1009,1024] shell [0,1009,1009] words 650
 768 scroll [768,768]   words 650
 375 scroll [375,375]   words 646
```
Screenshots: /tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun127/after-1920.png, after-1440.png, after-1024.png, after-768.png, after-375.png. Visible `<main>` words 1377 -> 650 (47.2%).

**DELTA**: A reader on a wide screen sees the page in a 1280 px centred container, gets How it works, Install, Use it, Remove it and Measured as a flow, stepper, day strip, labels and bar chart with the mint path first, finds highlight-only release notes without task IDs, and no longer sees "How it was built".

**WITNESS**: pending the trace file `memory/event-trace/HUN-127.jsonl` (the Supervisor derives it; the agent ran the commands in this worktree on 2026-10-29).
