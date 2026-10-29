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
6. Read `site/index.html`, `site/theme.css`, `tests/test_site_page.py` in full, and the updated spec export (revision 25 of the user's Claude Docs doc "Easy Kit family — Graphite Mint implementation spec", [https://claude.ai/artifact/3mXfGbwzZz89WjKWsT4WAz](<https://claude.ai/artifact/3mXfGbwzZz89WjKWsT4WAz>)); the spawn prompt gives the file paths. The canvas artboard "B · Graphite Mint — Easy Memory" ([https://claude.ai/artifact/5jKFUHLaGJTPK4KgazQ2o1](<https://claude.ai/artifact/5jKFUHLaGJTPK4KgazQ2o1>)) is the visual reference; the spawn prompt gives its saved source.

---

## Requirement (Pillar 1 — Adapt the requirement)

The user updated the design ("design is updated, please check …"). Spec revision 25 adds a neon highlight layer to Graphite Mint: a bright `--neon` #3CF5A8 with `--neon-soft`, `--neon-line`, `--neon-bar` and glow tokens (`--glow-text`, `--glow-box`, `--glow-dot`, `--glow-line`); soft mint `--accent` #7EDDB0 stays for ordinary links and hover only. Neon plus glow goes only on the elements in the spec's "Neon highlights" table, at most about 6 neon elements visible per screen, glows static, and an `html.no-glow` class sets every `--glow-*` token to `none`. Apply this to the Easy Memory page as it stands after HUN-127 (container, visual guide, folded detail, highlight-only release notes, no "How it was built").

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> The page keeps its HUN-127 layout and copy, and gains the spec's neon highlights: the things that need attention (active nav, current-site dot, eyebrow, step numbers, primary buttons, key numbers, the shipped experiment card, the main path in charts and diagrams, progress fills, `$` prompts) glow in neon; links stay soft mint; nothing else glows.

**Out of scope** (what this task explicitly does NOT do):

* Copy, section or layout changes. The canvas artboard is older than HUN-127 (it still shows "How it was built", a 5-cell step grid and a 4-cell stat strip, and shorter copy): take only its neon treatment, never its layout or copy. The user's HUN-127 decisions win where the spec's "keep sections" rule conflicts.
* The spec's "Easy Personal dashboard" section (another repo).
* A visible glow on/off control (the spec asks only for the `.no-glow` class); list it as a cut.

**Requirement Refs**: user request of 2026-10-29; spec rev 25 sections "Brief" principles 2 and 4, "Design tokens", "Shared layout" (header glyph, family dot, sidebar active item, eyebrow), "Components", "Neon highlights" table, "Per-site pages → Easy Memory → Context", "Rules and acceptance checklist".

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Every Acceptance Criterion below traces to a line in spec rev 25

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: HUN-127 (merged)

**Entry point**: `site/index.html`

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | `site/theme.css` `:root` block is byte-identical to the rev 25 token block, and its component CSS byte-identical to the rev 25 component block. | Tokens, Components |
| 2 | No reference to a token the rev 25 block no longer defines (`--accent-soft`, `--accent-line`) or to any undefined custom property anywhere in `site/`. | Tokens |
| 3 | Neon treatments exactly per the "Neon highlights" table: active sidebar item (text `--neon` + `--glow-text`, background `--neon-soft`, `inset 0 0 0 1px var(--neon-line)`); current-site family dot (`--neon` + `--glow-dot`), in the header and in the drawer; header glyph stroke `--neon`; eyebrow (`--neon` + `--glow-text`); step numbers in the flow and the install stepper (`--neon` + `--glow-text`); primary buttons incl. Copy (`--neon`, `--on-accent` text, `--glow-box`, hover `filter: brightness(1.08)`); key numbers (Measured values and the shipped experiment number: `--neon` + `--glow-text`); the exp 03 card (`--neon-line` border + `--glow-box`), label `exp 03 · shipped` in `--neon`; chart/diagram main path strokes (`--neon` + `filter: var(--glow-line)`); progress/bar fills (`--neon` + `--glow-dot`); `$` prompts `--neon` with no glow. | Neon highlights |
| 4 | Nothing else uses `--neon` or a glow: links, hover, focus ring, headings, body text, ordinary cards, section borders stay as before (`--accent` for links/hover/focus). | Rules |
| 5 | Neon budget: at 1280×800, at every scroll stop that starts a section, at most 6 neon elements are visible, counting one diagram, stepper, strip or bar chart as one element. Report the count per stop. If a stop needs more, report it with a proposal instead of exceeding silently. | Brief principle 2 |
| 6 | `html.no-glow` sets every `--glow-*` token to `none`; with the class on, no element has a non-`none` `text-shadow`, `box-shadow` (glow) or `filter` from a glow token. Glows are never animated or transitioned. | Neon highlights note |
| 7 | Accessibility holds: text contrast ≥ 4.5:1 (check neon text on `--bg`, `--on-accent` on `--neon`); focus ring visible; skip link, drawer, Copy, scroll-spy and `<details>` still work; no horizontal page scroll at 1920, 1440, 1024, 768, 375. | Rules (Accessibility) |
| 8 | `tests/test_site_page.py` updated (rev 25 token and component blocks byte-identical, no undefined `var(--…)`, `.no-glow` rule present, neon/glow used only in the listed selectors) and passing; full suite passes. | Hard-Stop Gate 5 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The reviewer fills **Evidence** at Stage 4/5 in `tasks/TASK_REVIEW_<ID>.md`, copied from
> `templates/TASK_REVIEW_template.md`. A task is **not done** until every row has evidence.

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | `cmp` of theme.css blocks vs the rev 25 export | identical | pasted |
| 2 | page at 1280×800, each section start | ≤ 6 neon elements visible; list per stop | CDP script output pasted |
| 3 | `document.documentElement.classList.add('no-glow')` | zero glow shadows/filters on any element | CDP script output pasted |

### Verification Command (exact, runnable)

```bash
python3 -m unittest tests.test_site_page -v && python3 -m unittest discover -s tests 2>&1 | grep -E "^Ran|^OK|FAILED"
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-130.md` (review sections are never taken from the board).

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_HUN-130.md` (review sections are never taken from the board).

## UI / Design Acceptance Criteria

### 1. Visual Regression

Before/after at 1920, 1440, 1024, 768, 375, compared with the canvas artboard's neon treatment.

### 2. Design-System Compliance

AC1–AC6.

### 3. Layout / Responsiveness

AC7; layout must be unchanged from HUN-127 apart from colour/glow.

## Approach

**Vital slice**: swap theme.css to rev 25, fix references to removed tokens, then apply the neon table element by element, then `.no-glow`, then the budget count.
**Cut list**: A visible glow toggle; neon on anything not in the table; layout or copy changes.

---

## Edge Case Checklist

- [ ] Hidden duplicates (the tall/wide flow SVG, the drawer family nav) get the same treatment.
- [ ] `prefers-reduced-motion`: glows are static anyway; no transitions on glow properties.
- [ ] `.no-glow` also removes the SVG `filter` glow.

---

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| site/theme.css | rev 25 tokens + components |
| site/index.html | neon treatments, `.no-glow` rule |
| tests/test_site_page.py | updated rules |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| easy_memory.py, other tests | not part of this task |

---

## Test Plan

Updated page tests; byte comparison with the export; CDP neon count per section stop; no-glow probe; screenshots at five widths.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Evidence pasted into the TASK_REVIEW Evidence table, including all three UI rows (Hard-Stop Gates 5 and 6)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review