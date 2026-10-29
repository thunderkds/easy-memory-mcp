**Date**: 2026-10-29
**Complexity Level**: C2
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: frontend-developer
**Agent guide**: `agents/frontend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/frontend.md` in full
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/frontend.md`
6. Read `site/index.html`, `site/theme.css` and `tests/test_site_page.py` in full. The Graphite Mint spec (tokens, components, rules) still applies; the spawn prompt gives the exported spec files.

---

## Requirement (Pillar 1 — Adapt the requirement)

User feedback on the Graphite Mint page (HUN-125), verbatim:

1. "the site should have the container, currently it become wider following the screen, it's not good"
2. "it's too much text, the guide should show the flow, chart, way to go is the highlight"
3. "the release note should not show the task, just highlight the work only"
4. "remove the section how it was built"

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> The page sits in a centred container that stops growing on wide screens. A reader gets each section from a picture first — a flow, a stepper, a chart — with the recommended path ("the way to go") drawn in mint and everything else neutral; prose shrinks to a short caption, and the remaining detail is folded away, not deleted. Release notes list what the release does, with no task IDs. "How it was built" is gone.

**Out of scope** (what this task explicitly does NOT do):

* New facts. Every number, command and claim comes from the current page. No v0.2 content.
* Changes to `site/theme.css` tokens (the spec block stays byte-identical); new layout values go in the page's own style as new custom properties.
* The Easy Kit and Easy Verifier sites.

**Requirement Refs**: user feedback of 2026-10-29 (items 1–4 above); Graphite Mint spec rules (one accent, hairlines, no gradients/glows, status as mono words).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Every Acceptance Criterion below traces to one of the four feedback items or the spec

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: HUN-125 (merged)

**Entry point**: `site/index.html`

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | Container: header content and the sidebar+main shell sit inside one centred container, max width 1280px (a new `--container-max` custom property in the page style). At 1440 and 1920 px the header's left/right content edges line up with the shell's, the shell is centred, and the page background fills outside it; the header's bottom hairline may stay full-bleed. Below 1280 px nothing changes from HUN-125. | Feedback 1 |
| 2 | How it works = one flow diagram (inline SVG, `role="img"` + `aria-label`, labels as real text): your answer → Stop hook → note store → prompt hook → your next prompt with the index → `memory_read` opens one note, with word weights as a side input to the prompt hook. The main loop is drawn in `--accent`; side paths and labels neutral (`--line-strong`, `--text-muted`). On narrow screens it reflows top-to-bottom or scrolls inside its own box; never page scroll. | Feedback 2 |
| 3 | Install = a 3-step horizontal stepper (01 Get the code → 02 Preview → 03 Install, then a "Check" end marker) with one codebox each and one short line under each; the "way to go" path (the three steps) is the mint line; stacks vertically below 720 px. | Feedback 2 |
| 4 | Use it = a visual for the switch (a strip of days showing auto: even day on / odd day off, with `on` and `off` forcing it) plus the commands as a compact list of command → one line. | Feedback 2 |
| 5 | Remove it = the roll-back triggers as short mono labels (hook error on every prompt · prompts ≥ 1 s · MCP fails in `claude mcp list` · permission prompt on open), then the codebox. | Feedback 2 |
| 6 | Measured = a bar chart: for each hook, a bar of its p95 against its limit (prompt hook 0.212 s of 1 s; Stop hook 0.066 s of 2 s), measured part in `--accent`, the rest of the limit as a `--line-header` track, values and limits as text; plus the weights load (0.024 s, 1.69 MB) and 307 tests as plain stat cells. No gradients. | Feedback 2 |
| 7 | Text: each section shows at most 2 short sentences of visible prose above or under its visual. All other current prose of the section moves into one `<details>` ("More detail") at the end of that section — nothing factual is deleted except the How-it-was-built section and the release-note task IDs. Context keeps its three experiment cards with one line each, details folded. | Feedback 2 |
| 8 | Release notes: no task IDs (`HUN-` appears nowhere in the page). A short list of highlights, one line each, grouped by what the user gets (save · recall · control · measure · install), written from the current rows. | Feedback 3 |
| 9 | The "How it was built" section and its sidebar item are removed; no link points to `#built`. | Feedback 4 |
| 10 | Spec rules still hold: colours only from tokens, one accent, hairlines, no gradients/glows/text-shadows, status as mono words, Plex fonts only; contrast ≥ 4.5:1; skip link, focus ring, drawer, Copy and scroll-spy still work; no horizontal page scroll at 1920, 1440, 1024, 768, 375. | Spec |
| 11 | `tests/test_site_page.py` updated (section ids without `built`, no `HUN-` text, container property present, SVG flow has `role="img"` and an `aria-label`) and passing; full suite passes. | Hard-Stop Gate 5 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The reviewer fills **Evidence** at Stage 4/5 in `tasks/TASK_REVIEW_<ID>.md`, copied from
> `templates/TASK_REVIEW_template.md`. A task is **not done** until every row has evidence.

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | page at 1920 px | shell and header content 1280 px wide, centred, edges aligned | measured rects pasted + screenshot |
| 2 | visible word count of `<main>` (excluding `<details>` content and code) before vs after | after ≤ 50% of before | script output pasted |
| 3 | grep `HUN-` and `#built` in `site/` | nothing | pasted |

### Verification Command (exact, runnable)

```bash
python3 -m unittest tests.test_site_page -v && python3 -m unittest discover -s tests 2>&1 | grep -E "^Ran|^OK|FAILED"
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-127.md` (review sections are never taken from the board).

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_HUN-127.md` (review sections are never taken from the board).

## UI / Design Acceptance Criteria

### 1. Visual Regression

Before/after screenshots at 1920, 1440, 1024, 768, 375 (scrollbars visible).

### 2. Design-System Compliance

AC10; the flow, stepper and chart use only tokens and the spec's line weights.

### 3. Layout / Responsiveness

AC1, AC2, AC3, AC10.

## Approach

**Vital slice**: container first (one wrapper + header inner), then How it works flow, Install stepper, Measured chart, then the text folding and release notes, then removing #built.
**Cut list**: Animations; interactive charts; dark/light switch; new sections.

Hand-write the SVGs (no libraries). Keep labels as SVG `<text>` or HTML overlays that remain real text. Mint marks only the main path.

---

## Edge Case Checklist

- [ ] `<details>` open/closed both look right; keyboard opens them.
- [ ] Flow SVG readable at 375 px (reflow or contained scroll).
- [ ] Container at exactly 1280 px: no double padding jump.
- [ ] Scroll-spy still finds every section after `#built` is gone.

---

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| site/index.html | container, visuals, folded text, release notes, remove #built |
| tests/test_site_page.py | updated rules |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| site/theme.css `:root` block | must stay byte-identical to the spec |
| easy_memory.py, other tests | not part of this task |

---

## Test Plan

Updated page tests; word-count script; grep; screenshots at five widths; CDP checks of drawer, Copy, scroll-spy, details keyboard.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Evidence pasted into the TASK_REVIEW Evidence table, including all three UI rows (Hard-Stop Gates 5 and 6)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review