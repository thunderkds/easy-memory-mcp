**Date**: 2026-10-29
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P2
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
6. Look at the reference image `/home/hungnguyenhuu/workspace/image/1709717801518.png` (outside the repo; do not copy it into the repo)

---

## Requirement (Pillar 1 — Adapt the requirement)

The user asked: "update the index page to this style" with the reference image above. The index page is `site/index.html`, the static release page served by Vercel (`vercel.json`, `outputDirectory: site`). Restyle it to match the reference: a dark indigo app frame on a purple gradient, monospace type, rounded card panels, a left sidebar with collapsible groups and coloured dots, blue-to-violet accents, outline pill buttons, and a progress ring.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> The release page looks like the reference dashboard, while every word, link, table and code block on it stays the same. Only the presentation changes.

**Out of scope** (what this task explicitly does NOT do):

* Any text, number, link or section change (the page still describes v0.1.0; updating content for Gate 0 is a separate task).
* Copying the reference's content (news, timeline, friend requests, avatars, names). It is a style reference only.
* New sections, new data, or invented stats. A progress ring may show only a number already on the page.
* JavaScript frameworks or build steps. The page stays one self-contained HTML file.

**Requirement Refs**: user request of 2026-10-29 (no PRD FR; the site is a release artefact of `docs/RELEASE_v0.1.0.md`)

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Every Acceptance Criterion below traces to a line in the Requirement

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: None — can start immediately

**Entry point**: `site/index.html` (open in a browser; Vercel serves `site/`)

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | The visible text of the page is unchanged: the text extracted from `<body>` (tags stripped, whitespace collapsed) is identical before and after, and so is the list of `href` values. | Restated intent |
| 2 | The look matches the reference: purple gradient page background around a dark indigo frame; panels and cards in dark indigo with rounded corners; monospace body type; light lavender text with a muted lavender secondary; blue-to-violet accent (links, active nav, buttons); outline pill buttons/links; sidebar groups with chevrons and coloured dots. | Requirement |
| 3 | At least one existing number from the "Measured" section is shown as a progress ring (SVG, gradient stroke), and its text value stays readable as text. | Requirement |
| 4 | Colours are CSS custom properties on `:root`; no raw hex colours outside `:root` (SVG favicon excepted). | design-system compliance |
| 5 | Text contrast is at least 4.5:1 for body text and 3:1 for large text against its panel. | accessibility |
| 6 | Works at 375 px, 768 px and 1280 px wide: no horizontal page scroll (tables may scroll inside their wrapper), the sidebar collapses behind the existing Menu button on narrow screens, and nav, skip link, focus outlines and `prefers-reduced-motion` keep working. | responsiveness, a11y |
| 7 | No external request is added unless it is one Google Fonts stylesheet; the page must still look right with that font blocked (monospace fallback stack). | self-contained page |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The reviewer fills **Evidence** at Stage 4/5 in `tasks/TASK_REVIEW_<ID>.md`, copied from
> `templates/TASK_REVIEW_template.md`. A task is **not done** until every row has evidence.

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | `site/index.html` before and after | identical stripped body text and href list | script output pasted (diff empty) |
| 2 | headless Chrome screenshots at 375, 768, 1280 px | match the reference style; no horizontal scroll | screenshots saved outside the repo, paths pasted; `document.documentElement.scrollWidth <= innerWidth` printed |
| 3 | grep for `#[0-9a-fA-F]{3,8}` outside `:root` and the favicon | none | command output pasted |

### Verification Command (exact, runnable)

```bash
google-chrome --headless=new --disable-gpu --hide-scrollbars --window-size=1280,2400 --screenshot=/tmp/after-1280.png "file://$PWD/site/index.html"
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-123.md` (review sections are never taken from the board).

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_HUN-123.md` (review sections are never taken from the board).

## UI / Design Acceptance Criteria

### 1. Visual Regression

Before and after screenshots at 375, 768 and 1280 px, plus the reference image, compared side by side.

### 2. Design-System Compliance

Tokens on `:root` (AC4); one accent gradient; one monospace stack; one radius scale.

### 3. Layout / Responsiveness

375 / 768 / 1280 px (AC6).

## Approach

**Vital slice**: replace the `:root` tokens and the component styles (body background, frame, sidebar, cards, tables, code, tags, buttons, details) with the reference look; add the progress ring for one existing measured number.
**Cut list**: Theme switcher; animations beyond a hover transition; a right-hand rail with invented content.

Keep the existing markup and IDs where possible; add wrapper elements or classes only when the layout needs them. Keep the existing small script (nav toggle, active link) working.

---

## Edge Case Checklist

- [ ] Wide tables scroll inside `.table-wrap`, not the page.
- [ ] Long code lines wrap or scroll inside `pre`.
- [ ] Keyboard: skip link, nav, `details/summary` all visible on focus.
- [ ] Print or no-JS: content still readable.

---

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| site/index.html | styles, minimal markup for frame and ring |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| easy_memory.py, tests/\*\* | not part of this task; live hooks run from the main checkout |
| vercel.json | deploy config unchanged |

---

## Test Plan

Text/href identity script, hex-colour grep, headless Chrome screenshots at three widths, scroll-width check, manual keyboard pass.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Evidence (text identity, screenshots, contrast, grep) pasted into the TASK_REVIEW Evidence table (Hard-Stop Gates 5 and 6)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review