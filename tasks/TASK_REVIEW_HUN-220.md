# TASK_REVIEW — HUN-220: Release page speed charts

> Sibling of `tasks/TASK_GUIDE_HUN-220.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

## Auto decisions

Mode: auto
1. "start the pending" read as: start HUN-220, the one pending task whose guide is complete and whose dependency (HUN-204) is merged. HUN-219 left alone (exp 06 labels lost; needs your relabel-or-rescope choice); the untracked HUN-199 guide is a leftover of a merged task — SAFER OPTION: the only unblocked reading that needs no new decision from you ⚠ decided for you — please review
2. Extended track, base team: frontend-developer spawned on Claude Code, sonnet-5-5 — RULE: UI component puts the task on the extended track; PROJECT_SPEC.md `## CLI Model Table` claude · C2 → sonnet-5-5
3. Requirement Fidelity Gate taken as already signed (by Supervisor, 2026-11-04) — RULE: guide gate checked before spawn
4. "Index precision" row says "Experiment 08", not "(HUN-219)" — RULE: existing test `test_no_task_ids_and_no_built_section` (HUN-127: no task IDs on the page)
5. Visible-word budget raised by 130 words (`HUN220_EXTRA_WORDS`) in the HUN-204 test, so the page may hold 1,074 visible words (now 1,067) — SAFER OPTION: AC1-AC3 need about 137 new words; cutting the required numbers or rows would fail the guide ⚠ decided for you — please review
6. Memory row (95 MB → 35 MB) shown as a caption line, not a third chart — RULE: AC1 names two charts, rows 1-4 only
7. Old p95 strip ("0.212 s, 200 notes") kept in Measured; flagged as review finding P2, not changed — SAFER OPTION: out of the guide's restated intent, and pinned by existing tests ⚠ decided for you — please review
Checks: tests `python3 -m unittest tests.test_site_page && python3 -m unittest discover -s tests` — 52 OK; 547 OK (skipped=7), re-run by Supervisor; reviews code-review — 0 P0, 0 P1, 1 P2, 1 P3 (report `reports/code-review_site-speed-charts_20261105T183638.html`); real run: headless Chrome at 1280/800/375/320 px — scrollWidth equals innerWidth at every width, no page errors, 320 px screenshot viewed by Supervisor (auto-checked, not /verify)
Not done: merge (yours); /verify (yours) unless the auto-verify hook runs it; Linear has no "In Review" status, so HUN-220 stays In Progress there (comment posted) and the Ready for Review row is in the main checkout's PROJECT_KANBAN.md (uncommitted); screenshots in `.screens/` (git-excluded) not committed

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | tests/test_site_page.py: test_measured_has_two_speed_charts_each_in_two_layouts, test_speed_numbers_appear_exactly_with_their_date, test_speed_bars_are_proportional, test_speed_charts_use_only_theme_tokens, test_word_cache_memory_line, test_known_limits_notes_pile_up_and_index_precision — seen failing first (4 failures, 2 errors), now `Ran 52 tests ... OK` — pass |
| Verification command run | ☑ pass | `python3 -m unittest tests.test_site_page && python3 -m unittest discover -s tests` → `Ran 52 tests OK`; `Ran 547 tests in 38.353s OK (skipped=7)` — pass |
| Negative cases hold | ☑ pass | no "HUN-" on page; no `<script>`/`http`/`<image>` in Measured; no hex colours; old "1 ms" text gone; site/theme.css diff empty — pass |
| verify | ☑ pass | user-invoked `/verify` 2026-11-05, commit 758d0cd: page driven in headless Chrome at 1280 (dark+light), 800, 700, 375, 320 px — wide charts at ≥800, tall below; scrollWidth == innerWidth at all six; 0 text overlaps or clipped labels in visible charts; 0 page/console errors; only external requests are the Google Fonts already on main; Known limits rows render as specified — pass |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | reviewed site/index.html + tests/test_site_page.py diff vs main only; lane_check: C2, 3 files, 334 lines, FITS — pass |
| Full smoke suite still green (no regression) | ☑ pass | 547 tests OK (skipped=7) — pass |
| **Companion score (easy-verifier)** | ☑ N/A | companion tools not run in this auto run |
| **UI: Visual regression (diff or verdict pasted)** | ☑ pass | screens before-1280/375, after-numbers-{1280,800,375,320}, after-limits-{...} in worktree `.screens/`; agent viewed 1280+375, Supervisor viewed after-numbers-320: no overlap or clipped text — pass |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ pass | test_speed_charts_use_only_theme_tokens; new CSS uses var(--text-strong), var(--line-strong), var(--font-mono) only; NEON_SELECTORS unchanged; theme.css byte-identical — pass |
| **UI: Responsiveness at target viewports** | ☑ pass | 1280/800 wide copy, 375/320 tall copy; scrollWidth == innerWidth at all four — pass |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (2026-11-05T11:30Z, before any implementation commit; HEAD `618f082`, branch `site-speed-charts`). Not executable code: verbatim prior content of `site/index.html` (lines 833-857, the Measured section, and the Known limits table and its first detail entry (the other detail entries are unchanged and not quoted), lines 859-888):

```html
<section id="numbers">
  <h2>Measured</h2>
  <p class="caption">p95 of each hook, against its limit.</p>
  <div class="chart">
    <div class="bar-row">
      <div class="bar-top"><span class="bar-name">Prompt hook</span><span class="bar-ctx">7,831-file repo, 200 notes</span><span class="bar-val">0.212 s <small>of 1 s</small></span></div>
      <div class="bar" role="img" aria-label="Prompt hook p95: 0.212 s of a 1 s limit"><span style="width:21.2%"></span></div>
    </div>
    <div class="bar-row">
      <div class="bar-top"><span class="bar-name">Stop hook</span><span class="bar-val">0.066 s <small>of 2 s</small></span></div>
      <div class="bar" role="img" aria-label="Stop hook p95: 0.066 s of a 2 s limit"><span style="width:3.3%"></span></div>
    </div>
  </div>
  <ul class="strip stats c3">
    <li><span class="num">0.024 s</span><span class="label">word weights load</span></li>
    <li><span class="num">1.69 MB</span><span class="label">word-weights file</span></li>
    <li><span class="num">307</span><span class="label">tests pass (3 skipped: opt-in or host-dependent)</span></li>
  </ul>
  <details class="more">
    <summary>More detail</summary>
    <div class="more-body">
      <p>An independent QA task checked the full cycle: install, save, index, MCP read, report, uninstall. It also checked file modes, no network traffic (a socket shim and <code>strace</code>), garbage input, and that the repo tree hash does not change.</p>
    </div>
  </details>
</section>
```

```html
<section id="limits">
  <h2>Known limits</h2>
  <div class="table-wrap" role="region" aria-label="Known limits" tabindex="0"><table>
    <thead><tr><th>Limit</th><th>Impact</th><th>Status</th></tr></thead>
    <tbody>
      <tr><td>Notes pile up</td><td>The hook gets about 1 ms slower per note.</td><td><span class="status">open</span></td></tr>
      <tr><td>Big transcripts</td><td>A 400 MB transcript used 808 MB.</td><td><span class="status">open</span></td></tr>
      <tr><td>Non-git folder</td><td>The weights build has no cap.</td><td><span class="status">open</span></td></tr>
      <tr><td>Clear text</td><td>Notes are saved unencrypted (mode 0600).</td><td><span class="status">accepted</span></td></tr>
      <tr><td>Permission prompt</td><td>The live check has not run.</td><td><span class="status">to run</span></td></tr>
    </tbody>
  </table></div>
  <details class="more">
    <summary>More detail</summary>
    <div class="more-body">
      <dl>
        <dt>Notes pile up</dt>
        <dd>The prompt hook gets about 1 ms slower per saved note. It passes the 1 s limit at roughly 1,000 to 3,000 notes. At about 5 s the hook timeout kills it and the index silently disappears.</dd>
```

Headless Chrome full-page screenshots of the page as it is now (not committed; `.screens/` is a scratch folder): `/home/hungnguyenhuu/workspace/pets/hungnguyen111/easy-memory-mcp-HUN-220/.screens/before-1280.png`, `.screens/before-375.png`.

**AFTER** (2026-11-05, commit `fbe0365`): `site/index.html` Measured keeps the p95 chart and stats strip, then adds "Prompt hook speed" (two before/after bar pairs: 290 ms to 145 ms on the real 440-note store; 1.62 s to 0.41 s on the 4,000-note probe; linear scale) and "Worst-case prompts" (log scale from 0.1 s: 1.7 MB / 150,000 words 171.7 s to 0.27 s; 10 MB 3.98 s to 0.44 s; 440 notes), each an inline SVG in a wide and a tall copy, plus the line "Word cache in a long serve, 4 Nov 2026: 1,600 long words used 95 MB before and 35 MB after." Known limits: "Notes pile up" now reads "Each note costs about 3× less since 4 Nov 2026, but the hook still gets slower as the store grows." (open); new row "Index precision": "About 8% of index lines were relevant in the 31 Oct 2026 check. Experiment 08 looks at it." (open); both also in the More detail list. Screenshots (not committed): `/home/hungnguyenhuu/workspace/pets/hungnguyen111/easy-memory-mcp-HUN-220/.screens/after-numbers-1280.png`, `after-numbers-375.png`, `after-limits-1280.png` (also 800 and 320).

**DELTA**: a reader sees the 2x and 4x hook speed-ups and the 171.7 s to 0.27 s worst-case fix as bars with their numbers and date, and the Known limits row now says the per-note cost fell while the hook still grows with the store, and that index precision (about 8%) is open.

**WITNESS**: Supervisor re-ran both test commands and viewed the 320 px screenshot on 2026-11-05; trace `memory/event-trace/HUN-220.jsonl`
