# TASK_REVIEW — HUN-130: Release page — Graphite Mint neon highlight layer

> Sibling of `tasks/TASK_GUIDE_HUN-130.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_site_page.py` (39 tests; 7 new or changed for HUN-130): `test_theme_css_is_byte_identical_to_spec_rev_25` (AC1, sha256 of both blocks), `test_theme_root_holds_the_spec_tokens` (AC1), `test_no_undefined_or_removed_custom_property` (AC2), `test_neon_treatments_match_the_table` (AC3), `test_neon_and_glow_only_on_the_highlight_selectors` + `test_shadows_and_filters_use_only_the_glow_tokens` (AC4), `test_no_glow_class_switches_every_glow_token_off` (AC6), `test_neon_contrast_holds` (AC7). Run against the old (main) site, the 7 fail: `FAIL: test_neon_and_glow_only_on_the_highlight_selectors / test_neon_treatments_match_the_table / test_no_glow_class_switches_every_glow_token_off / test_no_undefined_or_removed_custom_property / test_shadows_and_filters_use_only_the_glow_tokens / test_theme_css_is_byte_identical_to_spec_rev_25 / test_theme_root_holds_the_spec_tokens`, `Ran 39 tests` `FAILED (failures=7)` (`/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun130/neg-result.txt`) |
| Verification command run | ☑ pass | `python3 -m unittest tests.test_site_page -v` gave `Ran 39 tests in 0.025s` `OK`. `python3 -m unittest discover -s tests 2>&1 \| grep -E "^Ran\|^OK\|FAILED"` gave `Ran 417 tests in 30.289s` and `OK (skipped=3)` |
| Negative cases hold | ☑ pass | Links stay `rgb(126, 221, 176)` (footer `source`). Focus ring `rgb(126, 221, 176) solid 2px` on the skip link and on a Copy button focused by Tab. `--accent-soft` and `--accent-line` are absent and no `var(--…)` is undefined (test). With `html.no-glow`: 0 elements with a glow, all four tokens `none` (CDP, below) |
| verify | ☑ N/A | The `Skill` tool was not available to this agent, so `/verify` was not run. A CDP script did the browser check (`/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun130/verify130.mjs`, output `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun130/verify-after.txt`): Copy gives `Copied` and the clipboard holds the commands; the skip link takes focus; Tab shows the focus ring; `<details>` opens; scroll-spy marks `Release notes`; the 375 drawer opens with the neon current-site dot. All observed to work — pass. The Supervisor runs `/verify` at Stage 5 |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | Changed: `site/theme.css`, `site/index.html`, `tests/test_site_page.py`. Self-review of the diff only; the `Skill` tool was not available, so `code-review` was not run (Supervisor runs it at Stage 4). Not touched: `easy_memory.py`, other tests, copy, layout |
| Full smoke suite still green (no regression) | ☑ pass | `Ran 417 tests in 30.289s` and `OK (skipped=3)` |
| **Companion score (easy-verifier)** | ☑ N/A | Not run: no easy-verifier tool was available to this agent |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | Before and after screenshots at 1920, 1440, 1024, 768, 375 (scrollbars visible): `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun130/before-<w>-top.png` against `after-<w>-top.png`; section stops `{before,after}-{1440,375}-{context,how,run,numbers}.png`; `after-375-drawer.png`. Verdict (viewed with Read): layout is identical to the before shots, only colour and glow changed. Glow strength matches the canvas artboard: its script computes the same four glows (`text 0 0 12px @0.35`, `box 0 0 0 1px @0.25, 0 0 18px @0.25`, `dot 0 0 8px`, `line drop-shadow(0 0 3px @0.6)`) and the page tokens hold exactly those values. Neon on: active nav (ring, soft fill, glow text), current-site dot, glyph, eyebrow, hero button, exp 03 card (border, glow, label, number), flow arrows and step numbers, stepper line and mark, Copy buttons, `$` prompts, bar fills and values, stat numbers. Links, headings and other cards stay neutral or soft mint |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | AC1: `cmp` of the two `theme.css` blocks against the rev 25 export printed `ROOT-IDENTICAL` and `COMPONENTS-IDENTICAL` (sha256 `a7ba10aeab3bc94a5184eab59c5e2574df0a108d8b3d26890883619170e29d45` and `730b8e5a36ef56cf87fb2b02288241d93bee292a398b6f22442abf947e7a5e3a`, also asserted in the test). AC2: the test finds no undefined `var(--…)` and no `--accent-soft` or `--accent-line`. AC3/AC4: tests pin every neon or glow rule to its selector (the 6 theme.css rules plus 12 page rules and `html.no-glow`). Computed values (CDP): eyebrow `rgb(60, 245, 168)` with `rgba(60, 245, 168, 0.35) 0px 0px 12px`; hero button background `rgb(60, 245, 168)`, text `rgb(14, 16, 15)`, `box-shadow` the `--glow-box` pair, on hover `filter: brightness(1.08)` (`/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun130/hover.txt`); current-site dot `rgb(60, 245, 168)` with `0 0 8px`; flow main line `filter: drop-shadow(rgba(60, 245, 168, 0.6) 0px 0px 3px)`; `$` prompt neon with text-shadow `none`; footer link `rgb(126, 221, 176)`. AC6: with `html.no-glow` glow elements went 87 to 0, tokens `--glow-text=none --glow-box=none --glow-dot=none --glow-line=none`, the active-nav inset ring stays and its text-shadow is `none`. No `transition` or `animation` in any CSS (test). AC7 contrast: neon on `--bg`, and `--on-accent` on neon, are both at least 4.5:1 (test) |
| **UI: Responsiveness at target viewports** | ☑ pass | `[scrollWidth, clientWidth]`: 1920 `[1905, 1905]`, 1440 `[1425, 1425]`, 1024 `[1009, 1009]`, 768 `[753, 753]`, 375 `[375, 375]` (15px scrollbar at the first four): no horizontal page scroll. Layout rules are unchanged from HUN-127. The 375 drawer opens (`aria-expanded=true`) and shows the neon current-site dot. AC5 neon budget at 1280x800 (`verify130.mjs`, one stop per section start; literal rule: a diagram, stepper, strip or bar chart counts as one): top 4; what 5; context 5; how 5; run 4; use 5; **rollback 7**; numbers 5; limits 3; notes 3. Strict count (each Copy button and each codebox `$` group separate): how 8, run 10, the others as literal. **The `rollback` stop shows 7 (more than 6)**: header glyph, current-site dot, active nav item, the codebox `$` prompts, its Copy button, and (because the section is short) the Measured bar chart and stat strip below it. Proposal, not applied (the spec table fixes each element): count a codebox (prompts and Copy button) as one element, which gives 6; or drop neon on the `$` prompts. Left to the Supervisor |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured Thu Oct 29 03:19:00 PM UTC 2026 with `date -u`, on `main` content, before any implementation commit on `hun-130`; `node /tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun130/shots.mjs /tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun130/ before file://<worktree>/site/index.html accent`):

Screenshots of the unchanged page (headless Chrome, scrollbars visible: scrollWidth 1905 of innerWidth 1920 etc., so a 15px scrollbar shows):
`/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun130/before-1920-top.png`, `before-1440-top.png`, `before-1024-top.png`, `before-768-top.png`, `before-375-top.png`; extra stops `before-1440-{context,how,run,numbers}.png`, `before-375-{context,how,run,numbers}.png` (same folder).

Elements using the accent colour `#7EDDB0` (computed, at 1280 wide; full list in `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun130/before-accent.txt`), grouped:
- skip link text; header glyph (stroke); `.eyebrow` text; hero primary button background; the `exp 03 · shipped` card border (`--accent-line`) and its label
- flow diagram (wide and tall copies): step numbers `00`-`04` fill, five main node outlines (`--accent-line`), five main-loop arrow strokes
- install stepper: step numbers `01`,`02`,`03`,`end`, three connector lines, end mark; `$` prompts in every code box (3+1+1+3 = 8); Copy buttons background (4)
- Use it day strip: four `on` cells (`--accent-line` border) and their `on` text
- Measured: two bar fills; footer link `source`; header family dot (`::before`) of the current site (header and drawer)
- sidebar active item (`--accent-soft` background, accent text) appears after scroll-spy runs
- Not accent before: `.strip .num` stats, `.big` experiment numbers, `.bar-val` (all `--text-strong`)

**AFTER** (same screenshot script, `node /tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun130/shots.mjs /tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun130/ after file://<worktree>/site/index.html`, run on `hun-130` after the change): `/tmp/claude-1000/-home-hungnguyenhuu-workspace-pets-hungnguyen111-easy-memory-mcp/28185bde-ebb4-4e62-9f40-560e8aee485f/scratchpad/hun130/after-{1920,1440,1024,768,375}-top.png` and the section stops. The same script as `verify130.mjs` printed, for the neon elements (computed, 1280 wide): eyebrow `rgb(60, 245, 168)` with a `0 0 12px` glow, hero button background `rgb(60, 245, 168)`, glyph `rgb(60, 245, 168)`, current-site dot `rgb(60, 245, 168)` with `0 0 8px`, flow main line `drop-shadow(rgba(60, 245, 168, 0.6) 0px 0px 3px)`, link `rgb(126, 221, 176)`. With `html.no-glow`: `glow elements with html.no-glow: 0 []`. Test run: `python3 -m unittest tests.test_site_page -v` `Ran 39 tests` `OK`; full suite `Ran 417 tests` `OK (skipped=3)`.

**DELTA**: The release page now shows the things that need attention (active nav, current-site dot, eyebrow, step numbers, primary buttons, key numbers, the shipped experiment card, the main flow path, progress fills, `$` prompts) in glowing neon while links stay soft mint, and a reader can switch every glow off with `html.no-glow`.

**WITNESS**: Left for the Supervisor to derive from `memory/event-trace/HUN-130.jsonl` (the frontend-developer agent ran the commands above on 2026-10-29, BEFORE captured at 03:19:00 PM UTC).
