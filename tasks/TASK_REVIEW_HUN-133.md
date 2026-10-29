# TASK_REVIEW — HUN-133: Install stepper — equal code boxes across the three steps

> Sibling of `tasks/TASK_GUIDE_HUN-133.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_site_page.py::SitePageTest::test_install_stepper_boxes_are_equal_from_720_up` (failed before the CSS change, passes after: pins `.stepper > li` `display:grid; grid-row:span 4; grid-template-rows:subgrid` and `.stepper .codebox code` `flex:1` inside `@media (min-width:720px)`, and no `subgrid` in the `max-width:719px` block). |
| Verification command run | ☑ pass | `python3 -m unittest tests.test_site_page -v` -> `Ran 40 tests ... OK`; `python3 -m unittest discover -s tests` -> `Ran 418 tests in 29.893s` / `OK (skipped=3)`. |
| Negative cases hold | ☑ pass | 375 px: box tops/heights identical to BEFORE (180 / 120 / 100, stacked); end/Check column h3 top 1788.6 and caption top 1817.6 at 1440, same as BEFORE; test asserts no subgrid below 720. |
| verify | ☑ pass | Real-browser CDP run (headless Chrome, file://, `measure.mjs`): equal heights, Copy tops and caption tops at 1920/1440/1280/1024/768 - pass. The `verify` skill itself was not invokable from this agent (no Skill tool); Supervisor to run it. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Reviewed the `.stepper` rules, the `#run` stepper (4 `li`), the <720 block and the page test file; `site/theme.css` and other sections untouched. Diff: 6 CSS lines in `site/index.html`, 1 test. |
| Full smoke suite still green (no regression) | ☑ pass | `Ran 418 tests in 29.893s` `OK (skipped=3)`. |
| **Companion score (easy-verifier)** | ☑ N/A | Not run by the implementing agent (6-line CSS change; no verifier tool in this run). |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | Before/after crops of `#run`: `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun133/before-1440.png` vs `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun133/after-1440.png`, and `before-375.png` vs `after-375.png`. Verdict (viewed with Read): at 1440 the three boxes are one height, Copy buttons on one line at box bottoms, captions on one line; Check column unchanged; at 375 identical to BEFORE. |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | No colour, token or neon rule added: the new rules are `display`, `grid-row`, `grid-template-rows`, `flex` only. Existing page tests for colour literals, glow selectors and token bytes of `theme.css` pass in the 40-test run. |
| **UI: Responsiveness at target viewports** | ☑ pass | CDP at 1920, 1440, 1280, 1024, 768, 375 (`/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun133/after.txt`): no horizontal overflow (scrollWidth <= innerWidth at all six). 375 stacked and unchanged. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured `Thu Oct 29 03:47:38 PM UTC 2026`, unchanged page at `main` 86ee29d, before any implementation commit; Chrome headless via CDP, driver `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun133/measure.mjs`, full output `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun133/before.txt`). Page-absolute px; boxes = `.stepper .codebox` top/height of steps 01/02/03; copy = Copy button tops; cap = caption `p` tops.

```
1920 boxes top 1817.6 h 192 | 112 | 112   copy 1960.6 | 1880.6 | 1880.6   cap 2019.6 | 1939.6 | 1939.6
1440 boxes top 1817.6 h 192 | 112 | 112   copy 1960.6 | 1880.6 | 1880.6   cap 2019.6 | 1939.6 | 1939.6
1280 boxes top 1817.6 h 192 | 112 | 112   copy 1960.6 | 1880.6 | 1880.6   cap 2019.6 | 1939.6 | 1939.6
1024 boxes top 1835.5 h 252 | 132 | 132   copy 2038.5 | 1918.5 | 1918.5   cap 2097.5 | 1977.5 | 1977.5
 768 boxes top 2240.4 h 252 | 132 | 132   copy 2443.4 | 2323.4 | 2323.4   cap 2502.4 | 2382.4 | 2382.4
 375 boxes top 2789.7/3085/3320.2 h 180 | 120 | 100  (stacked)  scrollWidth 375 = innerWidth
```
End column (Check) at 1440: h3 top 1788.6, caption top 1817.6. Crop screenshots: `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun133/before-1440.png`, `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun133/before-375.png`.

**AFTER** (`Thu Oct 29 03:48:16 PM UTC 2026`, same driver, same widths, after the change; `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun133/after.txt`):

```
1920 boxes top 1817.6 h 192 | 192 | 192   copy 1960.6 | 1960.6 | 1960.6   cap 2019.6 | 2019.6 | 2019.6
1440 boxes top 1817.6 h 192 | 192 | 192   copy 1960.6 | 1960.6 | 1960.6   cap 2019.6 | 2019.6 | 2019.6
1280 boxes top 1817.6 h 192 | 192 | 192   copy 1960.6 | 1960.6 | 1960.6   cap 2019.6 | 2019.6 | 2019.6
1024 boxes top 1835.5 h 252 | 252 | 252   copy 2038.5 | 2038.5 | 2038.5   cap 2097.5 | 2097.5 | 2097.5
 768 boxes top 2240.4 h 252 | 252 | 252   copy 2443.4 | 2443.4 | 2443.4   cap 2502.4 | 2502.4 | 2502.4
 375 unchanged: boxes h 180 | 120 | 100, scrollWidth 375
```
Crops: `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun133/after-1440.png`, `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun133/after-375.png`.

**DELTA**: A visitor sees the three Install steps as one aligned set (equal boxes, Copy buttons and captions on shared lines) instead of one tall box beside two short ones.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/HUN-133.jsonl`, never the
implementing agent alone]
