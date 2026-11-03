# TASK_REVIEW — HUN-204: site — Easy Kit link, problem and solution, token chart, Easy Personal panel, no release notes

> Sibling of `tasks/TASK_GUIDE_HUN-204.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_site_page.py` (46 tests; new: `test_easy_kit_link_points_to_easy_kits_and_the_old_host_is_gone` AC1, `test_problem_and_solution_two_lane_picture` AC2, `test_how_a_note_is_saved_figure` AC3, `test_context_token_chart` AC4, `test_dashboard_panel_shows_the_snapshot` AC5, `test_release_notes_are_gone` AC6, updated `test_sidebar_groups_and_items` / `test_section_order_and_anchors` AC7, `test_visible_words_grow_by_at_most_150`). Red first: before the page edit the run ended `FAILED (failures=10, errors=4)`. |
| Verification command run | ☑ pass | `python3 -m unittest tests.test_site_page -v` → `Ran 46 tests in 0.029s` / `OK`; `python3 -m unittest discover -s tests` → `Ran 504 tests in 37.448s` / `OK (skipped=3)` |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green | ☑ pass | the discover run above: 504 tests, OK, 3 skipped (opt-in or host-dependent) |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression | ☑ pass | Full-page screenshots, looked at by the implementer, no overlap or clipped SVG text: `/home/hungnguyenhuu/workspace/pets/hungnguyen111/easy-memory-mcp-wt/HUN-204/.screens/after-1280.png`, `/home/hungnguyenhuu/workspace/pets/hungnguyen111/easy-memory-mcp-wt/HUN-204/.screens/after-375.png` (also `after-800.png`; per-section crops `problem-/context-/how-/dashboard-<width>.png`). Before: `before-1280.png`, `before-375.png`. One fix from the look: tall note figure value column moved from x=104 to x=114 ("cited files" touched its value). |
| **UI: Design-system compliance | ☑ pass | `test_no_colour_literal_outside_the_token_block` and `test_neon_and_glow_only_on_the_highlight_selectors` pass. New neon selectors added to `NEON_SELECTORS` (the guide allows it): `.fl-bar-on` (the with-memory token bar in the Problem picture), `.bar.is-soft > span` (exp 01/02 chart bars in `--neon-bar`, as the guide says), `.sp-bar` and `.sp-bar.is-today` (sparkline: soft bars, today neon). Exp 03 bars use the bare `.bar > span` (neon). Removed `.card .exp.shipped` and `.card.is-highlight .big` from the set because the cards are gone. `site/theme.css` untouched (byte-identical test passes). Visible words outside `<details>`: 794 → 930 (+136, limit +150; tall copies not counted). |
| **UI: Responsiveness | ☑ pass | `document.documentElement.scrollWidth` / `innerWidth` from headless Chromium: 1280 → 1280/1280 OK; 800 → 800/800 OK; 375 → 375/375 OK. Wide SVGs switch to tall copies below 800 px (`.flow-wide`/`.flow-tall`). Scroll-spy checked in the browser: problem → "Problem and solution", dashboard → "See it in Easy Personal", rollback → "Remove it", limits → "Known limits"; no page errors. |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (2026-11-03T15:42:58Z, before any implementation commit; HEAD `196f541`), `grep -n "personal-agentic-claude\|id=\"notes\"\|id=\"what\"" site/index.html`:

```
263:    <a class="fam" href="https://personal-agentic-claude.vercel.app/">Easy Kit</a>
278:    <a class="fam" href="https://personal-agentic-claude.vercel.app/">Easy Kit</a>
331:<section id="what">
677:<section id="notes">
```

Headless screenshot of the current page at 1280 px (full page): `/home/hungnguyenhuu/workspace/pets/hungnguyen111/easy-memory-mcp-wt/HUN-204/.screens/before-1280.png` (375 px: `.screens/before-375.png`).

**AFTER** (2026-11-03, after commit `c0962d7`): `grep -n "personal-agentic-claude\|id=\"notes\"\|id=\"what\"" site/index.html` prints nothing; `grep -n 'id="problem"\|id="dashboard"\|easy-kits.vercel.app' site/index.html` finds both sections and both Easy Kit links. Screenshot `/home/hungnguyenhuu/workspace/pets/hungnguyen111/easy-memory-mcp-wt/HUN-204/.screens/after-1280.png`.

**DELTA**: a reader sees the problem and the fix as two lanes, how a note is saved, the token saving as a bar chart, and this repo's real Easy Personal panel, with no release notes and the new Easy Kit link.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
