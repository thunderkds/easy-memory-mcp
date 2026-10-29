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
6. Read the design spec in full. Source of truth: the user's Claude Docs doc "Easy Kit family — Graphite Mint implementation spec" ([https://claude.ai/artifact/3mXfGbwzZz89WjKWsT4WAz](<https://claude.ai/artifact/3mXfGbwzZz89WjKWsT4WAz>)). The Supervisor exported it for you; the spawn prompt gives the two file paths (prose + code blocks). The code blocks (tokens, fonts, components) are normative; copy their values exactly.

---

## Requirement (Pillar 1 — Adapt the requirement)

The user asked to "follow the artifact and update" the release page. The artifact is the Graphite Mint spec for all three Easy Kit family sites. This repo holds only the Easy Memory site (`site/index.html`, served by Vercel from `site/`). Restyle it to the spec: graphite background, IBM Plex Sans and Mono, one mint accent, 1px hairlines, no gradients, glows or text shadows; the shared shell (64px header with glyph, name, tag and family nav; 248px sidebar with `// group` labels; main column); and the Easy Memory per-site section of the spec. This replaces the dark indigo look from HUN-123.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> The Easy Memory page looks like the Graphite Mint artboard for Easy Memory: same copy, anchors and section order, re-laid out with the spec's components (eyebrow, buttons, highlights strip, step grid, experiment cards, codeboxes, measured strip, tables with plain mono status words) and every colour from the spec's tokens.

**Out of scope** (what this task explicitly does NOT do):

* The Easy Kit and Easy Verifier sites (other repos).
* Content changes beyond what the spec's Easy Memory section names (eyebrow text, the "Install" secondary button, the header family nav). The page still describes v0.1.0.
* A light theme. A Copy button needing clipboard permissions beyond `navigator.clipboard.writeText` with a plain fallback.
* Lighthouse runs (no Lighthouse on this machine; covered by the manual a11y checks below).

**Requirement Refs**: user request of 2026-10-29; spec sections "Design tokens", "Typography", "Shared layout", "Components", "Per-site pages → Easy Memory", "Rules and acceptance checklist".

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Every Acceptance Criterion below traces to a line in the spec

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: HUN-123 (merged; this replaces its style)

**Entry point**: `site/index.html` (Vercel serves `site/`)

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | Tokens: `site/theme.css` holds the spec's `:root` block byte-for-byte (values and names) plus the spec's component CSS; `index.html` links it. No hex/rgb(a) colour anywhere else in `site/` (the favicon data URI may use token-equal hex values only). | Tokens, Rules |
| 2 | Only IBM Plex Sans and IBM Plex Mono load, with the spec's exact Google Fonts `<link>` tags; no other external request. | Typography, checklist |
| 3 | No `linear-gradient`, `radial-gradient`, `text-shadow`, glow `box-shadow`, `backdrop-filter`, or colour animation anywhere. The HUN-123 rings are removed. | Rules, checklist |
| 4 | Shell: 64px header (stacked-note-bars glyph, "Easy Memory", tag `memory kit · v0.1.0 prototype`, family nav Easy Kit · Easy Memory · Easy Verifier + GitHub secondary button; Easy Memory marked with the mint dot and `aria-current="page"`, linking [https://easy-memory.vercel.app/](<https://easy-memory.vercel.app/>)); 248px sidebar with groups `// overview`, `// guide`, `// reference` and the spec's item states (hover, scroll-spy active); main column 48px 56px, sections 40px apart. | Shared layout, Easy Memory |
| 5 | Easy Memory sections per spec: eyebrow `> per-repo memory for claude code`, h1, lede, buttons "View the source on GitHub" (primary) and "Install" (secondary, `#run` or the existing install anchor); Highlights `.strip` 3 cols (Local · Hooks and MCP · Measured on yourself, with their existing text); How it works step grid 5 cells (00–04) built from the existing flow text; Context 3 `.card`s with big mono numbers (−58%, \~−15%, −29% / −27%), experiment 03 `.is-highlight` with `exp 03 · shipped` in accent; Install as numbered steps each with a `.codebox` (`$` prompt in accent); Measured `.strip` 4 cols (0.212 s · 0.066 s · 0.024 s · 307); Known limits table with status as plain mono words in `--text-muted`, no pill badges. | Per-site pages |
| 6 | Content kept: every sentence, code line, table cell and link target of the current page still appears (the old Family sidebar group's links move to the header nav; the flow diagram's node labels move into the step grid). Section ids and order unchanged. | Brief, Rules |
| 7 | Responsive per spec at 1440, 1024, 768, 375 px: ≥1024 full shell; 720–1023 sidebar as a left drawer behind the existing Menu toggle, main padding 32px; <720 family nav inside the drawer top, header = glyph + name + Menu, main padding 24px 16px, h1 32px, grids to 1 column (strips to 2), tables scroll in `.table-wrap`; no horizontal page scroll; touch targets ≥ 44px below 720px. | Responsive, a11y |
| 8 | Accessibility: skip link first and visible on focus; mint focus ring on every link and button; text contrast ≥ 4.5:1 on its background; decorative SVG `aria-hidden="true"`; icon-only buttons `aria-label`. | Rules (Accessibility) |
| 9 | `tests/test_site_page.py` is updated to the new rules (AC1–AC4, AC6 links, AC8 aria) and passes; the full suite passes. | Hard-Stop Gate 5 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The reviewer fills **Evidence** at Stage 4/5 in `tasks/TASK_REVIEW_<ID>.md`, copied from
> `templates/TASK_REVIEW_template.md`. A task is **not done** until every row has evidence.

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | `grep -rEn '#[0-9a-fA-F]{3,8}\b|rgba?\(' site/` | hits only in `site/theme.css` `:root` (and the favicon) | pasted output |
| 2 | sentence inventory of old vs new page | every old sentence/cell/code line found in the new page | script output pasted |
| 3 | screenshots at 1440, 1024, 768, 375 (scrollbars visible) | match the spec; no horizontal scroll | paths + scrollWidth numbers pasted |

### Verification Command (exact, runnable)

```bash
python3 -m unittest tests.test_site_page -v && python3 -m unittest discover -s tests 2>&1 | grep -E "^Ran|^OK|FAILED"
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-125.md` (review sections are never taken from the board).

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_HUN-125.md` (review sections are never taken from the board).

## UI / Design Acceptance Criteria

### 1. Visual Regression

Before (HUN-123 look) and after screenshots at 1440/1024/768/375, compared with the spec.

### 2. Design-System Compliance

AC1–AC3; spec typography table (sizes, weights ≤ 600, no all-caps headings).

### 3. Layout / Responsiveness

AC7.

## Approach

**Vital slice**: `site/theme.css` (tokens + components verbatim), then the shell, then each section's component, in page order.
**Cut list**: Light theme; animations; a shared cross-repo theme URL (the spec's "one shared theme.css" is per repo here; keep the token block byte-identical to the spec so the three sites cannot drift).

Keep the existing small script (Menu toggle, scroll-spy) and extend it only for the drawer. Vercel serves `site/` as static files, so `theme.css` next to `index.html` works.

---

## Edge Case Checklist

- [ ] Fonts blocked: the fallback stacks still give a readable page.
- [ ] No JS: sidebar and content readable; Menu hidden or harmless.
- [ ] Long code lines scroll inside `.codebox`, not the page.
- [ ] Copy button: works where `navigator.clipboard` exists; otherwise selects the text.

---

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| site/index.html | new shell and section markup, links theme.css |
| site/theme.css | new: spec tokens + components |
| tests/test_site_page.py | updated rules |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| easy_memory.py, other tests | not part of this task; live hooks run from the main checkout |
| vercel.json | deploy config unchanged |

---

## Test Plan

Updated `tests/test_site_page.py`, sentence inventory script, hex/gradient grep, screenshots with scrollbars at four widths, CDP keyboard and drawer checks.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Evidence pasted into the TASK_REVIEW Evidence table, including all three UI rows (Hard-Stop Gates 5 and 6)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review