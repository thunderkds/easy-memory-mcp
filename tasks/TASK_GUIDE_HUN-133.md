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
6. Read `site/index.html` (the `#run` section and the `.stepper` rules) and `tests/test_site_page.py`

---

## Requirement (Pillar 1 — Adapt the requirement)

User feedback, verbatim: "from the install section, the box from get the code, preview, and install is not equal cause of content, let make it map for 3". The three code boxes in the Install stepper (01 Get the code, 02 Preview, 03 Install) have different heights because step 01 holds three commands and steps 02 and 03 hold one.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> On wide screens the three step columns line up as one set: the three code boxes share one height (the tallest one's), the three Copy buttons sit on one line at the bottom of their boxes, and the three captions start on one line below. The commands themselves do not change.

**Out of scope** (what this task explicitly does NOT do):

* Changing, splitting or shortening the commands or captions.
* The "end / Check" column (it has no code box); it keeps its look.
* The stacked layout below 720 px (boxes are full width there; equal heights are not needed).
* Any colour, token or neon change.

**Requirement Refs**: user feedback of 2026-10-29 (above).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Every Acceptance Criterion below traces to the feedback

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: HUN-130 (merged)

**Entry point**: `site/index.html` `#run`

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | At 1920, 1440, 1280, 1024 and 768 px the three `.stepper .codebox` elements have equal rendered height (±1px), and their tops are equal. | Feedback |
| 2 | The three Copy buttons have equal `top` (±1px) — placed at the bottom of each box. | Feedback |
| 3 | The three captions under the boxes have equal `top` (±1px). | Feedback |
| 4 | Below 720 px nothing changes from HUN-130 (stacked steps, boxes size to their content). | Out of scope |
| 5 | Commands, captions, Copy behaviour, neon treatment and section text are unchanged; no horizontal page scroll at 1920, 1440, 1024, 768, 375. | Feedback |
| 6 | A test in `tests/test_site_page.py` pins the CSS that equalises the boxes (e.g. the step items stretch and the code box grows, or a subgrid row template), and the full suite passes. | Hard-Stop Gate 5 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The reviewer fills **Evidence** at Stage 4/5 in `tasks/TASK_REVIEW_<ID>.md`, copied from
> `templates/TASK_REVIEW_template.md`. A task is **not done** until every row has evidence.

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | page at 1440 px | 3 box heights equal; 3 Copy tops equal; 3 caption tops equal | CDP rects pasted |
| 2 | page at 375 px | boxes size to content as before | CDP rects pasted |

### Verification Command (exact, runnable)

```bash
python3 -m unittest tests.test_site_page -v && python3 -m unittest discover -s tests 2>&1 | grep -E "^Ran|^OK|FAILED"
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-133.md` (review sections are never taken from the board).

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_HUN-133.md` (review sections are never taken from the board).

## UI / Design Acceptance Criteria

### 1. Visual Regression

Before/after crop of `#run` at 1440 and 375.

### 2. Design-System Compliance

No new colours; existing tokens only.

### 3. Layout / Responsiveness

AC1–AC5.

## Approach

**Vital slice**: CSS only in the page style — make each step item a column that fills the row (or use `grid-template-rows: subgrid` across the step rows) and let the code box grow, with the Copy button pushed to the bottom (`margin-top:auto`). Prefer the smallest rule set that meets AC1–AC3.
**Cut list**: Markup changes; equal heights below 720 px.

---

## Edge Case Checklist

- [ ] Long command wrapping at 768 px still gives equal boxes.
- [ ] The end/Check column is not stretched oddly.

---

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| site/index.html | `.stepper` CSS |
| tests/test_site_page.py | one test |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| site/theme.css | byte-identical to the spec |
| easy_memory.py, other tests | not part of this task |

---

## Test Plan

CDP rect measurements at five widths; updated page test; full suite.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Evidence pasted into the TASK_REVIEW Evidence table, including all three UI rows (Hard-Stop Gates 5 and 6)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review