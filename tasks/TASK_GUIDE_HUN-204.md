**Date**: 2026-11-03
**Complexity Level**: C2
**Risk Level**: Low
**Priority**: P2
**Assigned agent**: Frontend-Implementer
**Agent guide**: `agents/frontend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read your role guide (`Agent guide` above) with the Read tool and no `limit`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in your role guide
6. Read `memory/decisions.md` entry "Release page: Graphite Mint family theme" (HUN-125/127/130/133 updates: pictures first, one `<details>` "More detail" per section, neon only on the highlight list, no task IDs on the page)
7. Read `site/index.html`, `site/theme.css` and `tests/test_site_page.py` in full

---

## Requirement (Pillar 1 — Adapt the requirement)

Owner, 2026-11-03 (verbatim):

> update the the personal agentic to https://easy-kits.vercel.app/ and related
> from the index, should update the index more visualize with flow, chart to easy understanding how can you save the memory, how our memory help to save the token, talk about problem and solution
> by the way, from personal, we got the section to show our data as memory section, let add it, remote the release note also

**Restated intent**:

> The release page `site/index.html` changes in five ways. (1) The "Easy Kit" family link (header nav and drawer nav) points to `https://easy-kits.vercel.app/` instead of `https://personal-agentic-claude.vercel.app/`; no other file in this repo keeps the old URL. (2) The "What it is" section becomes **"Problem and solution"** (`id="problem"`): a two-lane picture, "Without memory" (a new session re-reads files and re-runs searches that an earlier session already did → long token bar) and "With memory" (the prompt hook adds a ≤5-line index → the agent opens one note → short token bar), plus one short paragraph per lane; the three promise chips stay. (3) A **"How a note is saved"** figure is added to "How it works", under the existing flow: what one note holds (question, answer, time, cited repo files with their sha256) and how a cited file that changes later is flagged `CHANGED:` / `DELETED:` in the index. (4) The "Context" experiment cards become a **token chart**: horizontal bars of "tokens with memory, as % of tokens without memory" (without = 100%), from the measured numbers already on the page — exp 01 42% (−58%), exp 02 about 85% (~−15%), exp 03 71% and 73% (−29% / −27%, the shipped method, highlighted). (5) A new section **"See it in Easy Personal"** (`id="dashboard"`) shows the Easy Personal dashboard's Memory view panel for easy-memory, drawn in HTML/SVG with this repo's real numbers (below), with a link to `https://easy-personal.vercel.app/`. (6) The "Release notes" section is removed with its sidebar link and its CSS (`.rn` rules, the `<720px` `.rn` rule); the footer drops "release plan in `docs/RELEASE_v0.1.0.md`" and keeps the version and the source link.

**Easy Personal panel — real snapshot of this repo's store, 2026-11-03** (counts only; label the figure "this repo, 3 Nov 2026"):

| Panel line (wording as easy-personal draws it) | Value |
| -- | -- |
| title | `easy-memory` |
| total | `143 notes` |
| sparkline caption | `saved per day, last 30 days` — non-zero days: 29 Oct 63, 30 Oct 23, 31 Oct 41, 2 Nov 3, 3 Nov 13; every other day of the 30 is 0 |
| hit rate | `Hit rate 70% of 56 prompts` |
| `Memory on vs off` | `On 3 sessions 23.2M tokens / session`; `Off 5 sessions 16.6M tokens / session` |
| saving line | `too few sessions to compare (3 on / 5 off, need 10 each)` |

One caption under the panel: Easy Personal reads `report.json`, which easy-memory refreshes about once an hour; it shows counts only, never note text. Do not print a saving percentage for the live numbers: the report itself says there are too few sessions.

**Section order** (sidebar groups): overview — Problem and solution, Context, How it works; guide — Install, Use it, See it in Easy Personal, Remove it; reference — Measured, Known limits.

**Out of scope**:

* `site/theme.css` (spec-locked, byte-identical test)
* Other repos' sites (easy-verifier, easy-ui, easy-personal) — separate boards
* The Measured numbers, Known limits rows, Install/Use/Remove content
* A screenshot of the real dashboard (it shows project names); a JS chart library; any new external request

**Requirement Refs**: owner request 2026-11-03 (HUN-204); `memory/decisions.md` Release page entry

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [X] Restated intent confirmed to match the user's request (Supervisor, 2026-11-03)
- [X] Every Acceptance Criterion below traces to a line in the Requirement

---

## Dependencies & Reachability

**Depends on**: none.

**Branch**: `HUN-204` in worktree `/home/hungnguyenhuu/workspace/pets/hungnguyen111/easy-memory-mcp-wt/HUN-204`. Commit there. Do not merge.

**Entry point**: `site/index.html` (`id="problem"`, `id="dashboard"`)

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to |
| -- | -- | -- |
| 1 | Both family navs link "Easy Kit" to `https://easy-kits.vercel.app/`; `grep -r personal-agentic-claude.vercel.app` over the repo (excluding `.claude/worktrees/`) finds nothing | (1) |
| 2 | `#problem` "Problem and solution" holds an accessible two-lane SVG (`role="img"`, `aria-label` that says both lanes) with a wide and a tall copy like the How-it-works flow, plus the three chips | (2) |
| 3 | "How it works" holds a second figure "How a note is saved" naming question, answer, time, cited files + sha256, and `CHANGED:` / `DELETED:` | (3) |
| 4 | `#context` shows a bar chart with 4 bars (exp 01 42%, exp 02 ~85%, exp 03 71%, exp 03 73%), a 100% "without memory" reference, each bar with an `aria-label` stating its value; exp 03 bars are the highlighted ones; the experiment detail stays in "More detail" | (4) |
| 5 | `#dashboard` "See it in Easy Personal" draws the panel with every value from the snapshot table exactly, a 30-bar sparkline, the caption, and a link to `https://easy-personal.vercel.app/`; no `Saves`/`Uses` percentage text | (5) |
| 6 | No `#notes` section, no "Release notes" text, no `.rn` CSS; footer has no `RELEASE_v0.1.0` | (6) |
| 7 | Sidebar groups and section order match the Section order above; every in-page link has a target; scroll-spy still works (it reads `main > section[id]`) | (2)(5)(6) |
| 8 | Existing site tests still pass after updating only the ones this change makes stale (family URL, sidebar items, section order, release-notes test removed, experiment-cards test replaced by the chart test); new tests cover AC 1–7 | all |

---

## Evaluation & Acceptance

> The reviewer fills **Evidence** in `tasks/TASK_REVIEW_HUN-204.md`.

### Verification Command (exact, runnable)

```bash
python3 -m unittest tests.test_site_page -v && python3 -m unittest discover -s tests
```

## UI / Design Acceptance Criteria

### 1. Visual Regression

| Screen | Method | Expected |
| -- | -- | -- |
| Full page 1280×720 and 375×812 | headless Chromium screenshot (`npx playwright screenshot --full-page` or `chromium --headless --screenshot`) | new figures render, no overlap or clipped SVG text |

### 2. Design-System Compliance

| Criterion | Method | Expected |
| -- | -- | -- |
| Colours / fonts | existing tests `test_no_colour_literal_outside_the_token_block`, `test_neon_and_glow_only_on_the_highlight_selectors` | every colour from `theme.css` tokens; reuse existing classes (`.figure`, `.flow`, `.fl-*`, `.chart`, `.bar-row`, `.bar`, `.card`, `.chips`); neon only on the highlight list (the exp 03 bars use `.bar > span`, other bars `--neon-bar`); if a new selector truly needs neon, add it to `NEON_SELECTORS` and say why in the review file |
| Text amount | visible words outside `<details>` | at most ~150 words more than now; pictures carry the explanation |

### 3. Layout / Responsiveness

| Viewport | Method | Expected |
| -- | -- | -- |
| 1280, 800, 375 px | screenshot + `document.documentElement.scrollWidth <= innerWidth` | no horizontal page scroll; wide SVGs switch to tall copies below 800 px |

---

## Approach

**Vital slice**: link fix → release notes out → Problem and solution picture → token chart → Easy Personal panel → note figure.
**Cut list**: no animation, no theme change, no light mode, no new JS beyond what exists.

1. Tests first in `tests/test_site_page.py` (update stale ones, add AC tests); see them fail.
2. Edit `site/index.html`.
3. Screenshots at 1280 and 375; paste paths and `scrollWidth` results in the review file.

---

## Edge Case Checklist

- [ ] SVG text stays inside its boxes at 375 px (tall copies)
- [ ] The "~85%" exp 02 bar is labelled "about 85%" in its aria-label
- [ ] No task IDs (HUN-xxx) on the page (`test_no_task_ids_and_no_built_section`)
- [ ] Neon budget: about 6 neon elements per screen

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| `site/index.html` | all page changes |
| `tests/test_site_page.py` | tests |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| `site/theme.css` | spec-locked |
| `easy_memory.py`, `plugin/` | not part of this task |
| `PROJECT_KANBAN.md` | pulled cache |
| `agents/`, `skills/`, `.claude/` | kit files |

## Completion Checklist

- [ ] Tests written AND pass — output pasted into the review file
- [ ] UI Evidence rows filled (Hard-Stop Gate 6) with screenshot paths
- [ ] Not merged into `main`
- [ ] Report: `Status: done` with commits, or `Status: blocked` + `Question:`
