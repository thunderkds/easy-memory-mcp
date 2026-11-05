**Date**: 2026-11-04
**Complexity Level**: C2
**Risk Level**: Low
**Priority**: P1
**Assigned agent**: frontend-developer
**Agent guide**: `agents/frontend.md`

---

## Mandatory Startup (Do Not Skip)

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt; read `memory/MEMORY.md` in full only if your work reaches what the slice does not cover
3. Read this file completely
4. Read `agents/frontend.md` in full
5. Apply the C2 process from the Complexity matrix in `agents/frontend.md`
6. Read `tasks/TASK_GUIDE_HUN-204.md` and `tasks/TASK_REVIEW_HUN-204.md` (the page this builds on); `memory/decisions.md` entries for HUN-208 and HUN-211 and the Release page entry; `tasks/TASK_REVIEW_HUN-208.md`, `TASK_REVIEW_HUN-210.md`, `TASK_REVIEW_HUN-211.md` (the numbers)
7. Read `site/index.html` (Measured and Known limits sections) and `tests/test_site_page.py`

---

## Requirement (Pillar 1 — Adapt the requirement)

User 2026-11-04: "checking the index page to make it more visualize, chart, flow, number analyzed, will be better to catch". HUN-204 (merged first) added the flow, the token chart and the Easy Personal panel. Its Measured section and Known limits still show pre-2026-11-04 numbers: prompt hook 0.212 s (200 notes), and the limit "Notes pile up: the hook gets about 1 ms slower per note — open".

**Restated intent**:

> The Measured section adds two before/after bar charts (inline SVG, theme tokens, no JS library) with the measured numbers below, and Known limits is updated to match. Every number has its source in the review files; nothing is estimated.

Numbers (Supervisor-verified, copy exactly):

| Chart / row | Before | After | Source |
| -- | -- | -- | -- |
| Prompt hook, normal prompt, real 440-note store | 290 ms | 145 ms | `TASK_REVIEW_HUN-208.md` verify row |
| Prompt hook, 4,000-note probe (max) | 1.62 s | 0.41 s | HUN-208 Demonstration |
| Worst-case prompt, 1.7 MB / 150,000 words, 440 notes | 171.7 s | 0.27 s | `TASK_REVIEW_HUN-211.md` verify row |
| Worst-case prompt, 10 MB, 440 notes | 3.98 s | 0.44 s | HUN-211 verify row |
| Word-cache memory in a long `serve`, 1,600 long words | 95 MB | 35 MB | `TASK_REVIEW_HUN-210.md` verify row |

Known limits: "Notes pile up" stays open but its text says the cost per note fell (≈3× less since 2026-11-04) and the hook still grows with the store; add "Index precision: about 8% of index lines were relevant in the 2026-10-31 check — open, experiment 08 (HUN-219)".

**Out of scope**: `site/theme.css` (spec-locked); any section other than Measured and Known limits; JS chart libraries or new external requests; project names (use Project A / Project B only).

**Requirement Refs**: user request 2026-11-04; HUN-208/210/211 review files; `BRAINSTORMING_LOG_v0.5.md` (precision fact).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [X] Restated intent confirmed to match the user's request (by Supervisor, 2026-11-04)
- [X] Every Acceptance Criterion below traces to the requirement

---

## Dependencies & Reachability

**Depends on**: HUN-204 (merge first; this task branches from `main` after it).

**Branch**: `site-speed-charts` from `main`.

**Merge gate**: none beyond Stage 4/5.

**Entry point**: `site/index.html` Measured section.

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | Measured has two inline-SVG before/after charts: hook speed (rows 1-2) and worst-case prompts (rows 3-4); bar lengths proportional within each chart (log scale allowed for the 171.7 s row, labelled) | chart |
| 2 | Each number in the table above appears exactly as written, with a caption naming its date (4 Nov 2026) | number analyzed |
| 3 | Known limits: "Notes pile up" text updated; "Index precision" row added, status open | honest limits |
| 4 | Existing site tests pass; new tests cover AC1-AC3 (numbers present, SVG count, rows present) | tests |
| 5 | Colours only from theme tokens; no new external request; no legacy project names | design system |

## UI / Design Acceptance Criteria

* Charts readable at 1280, 800, 375 and 320 px (wide SVG switches to a tall copy, as HUN-204 did); no horizontal scroll.
* Text in SVG uses theme fonts; contrast as the existing neon tests require.

---

## Evaluation & Acceptance

### Verification Command (exact, runnable)

```bash
python3 -m unittest tests.test_site_page && python3 -m unittest discover -s tests
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-220.md` (review sections are never taken from the board).

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| `site/index.html` | Measured charts, Known limits rows |
| `tests/test_site_page.py` | new tests |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| `site/theme.css` | spec-locked (byte-identical test) |
| `easy_memory.py`, `plugin/` | not a code task |

## Completion Checklist

- [ ] BEFORE screenshot of Measured/Known limits captured before any change
- [ ] Tests written first, failing, then passing
- [ ] Screenshots at 1280 and 375 after
- [ ] Report: `Status: done` with commits, or `Status: blocked` + `Question:`