**Date**: 2026-10-30
**Complexity Level**: C2
**Risk Level**: Medium
**Priority**: P1
**Assigned agent**: backend-developer
**Agent guide**: `agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:

1. Read `PROJECT_SPEC.md` (Glossary has the v0.3 terms: Typed prompt, Event, Trigger, Turn, Touched file, Trash)
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/backend.md` in full
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/backend.md`
6. Read `PRD_v0.3.md` (Decision record row for M2) and `BRAINSTORMING_LOG_v0.3.md` (Edge Case Checklist, M2)
7. Read `easy_memory.py` sections: `_typed_text`, `last_user_prompt`, `save_stop_note`, `_quoted`, `_index_line`, `_index_lines`, `_tool_list`, `_tool_read`

---

## Requirement (Pillar 1 — Adapt the requirement)

Kit list K-R2 (2026-10-30): notes are saved whose question is a harness event — `<task-notification>…`, `<bash-stdout>…` from a `!` command — e.g. note 20261030T125945217-4bf416e4. Verifier list V-R1: store a readable question, never raw tags or internal ids. V-R2: a declared, deterministic, written-down rule for which turns become notes, e.g. flag them `kind: event`. Store check 2026-10-30: 50 of 455 notes start `<task-notification`, 13 `<bash-stdout`, 2 `This session is being continued`. Rule chosen in grilling (Supervisor, user delegated: "as your choose").

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> An Event (task notification, `!` output, `[Request interrupted`, compaction summary) is never a note's question. The note's question is the last Typed prompt before it, and the note gets `trigger` (`task-notification` | `bash` | `compact`), shown as a short tag in `memory_list`, `memory_search`, `memory_read` and the hook index. If the transcript has no Typed prompt, the question is `<trigger>: <first line of the answer>`. The 200-character answer rule is unchanged. Notes after a Typed prompt are byte-for-byte as today (no `trigger` key).

**Out of scope** (what this task explicitly does NOT do):

* Skipping event-triggered replies (rejected in grilling: hand-back findings are kept).
* Cited files (that is HUN-138).
* Rewriting notes already saved (user, 2026-10-30: old notes are not rewritten).
* `report_command`, the switch, `INDEX_FLOOR` / `INDEX_MAX_NOTES` / `INDEX_MAX_CHARS` values, `experiments/`, `site/`.

**Requirement Refs**: `PRD_v0.3.md` M2; kit K-R2, verifier V-R1 and V-R2 (pasted 2026-10-30).

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [X] Restated intent confirmed to match the user's request (by Supervisor, 2026-10-30; rules fixed with the user in requirement grilling)
- [X] Every Acceptance Criterion below traces to the requirement

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: none.

**Branch**: `v03-m2-event-turns` from `main`. HUN-138 branches from this branch.

**Merge gate**: PRD v0.2 Gate 2a — do NOT merge into `main` until the sample bar is met and the report is done (user, 2026-10-30: keep the gates). The live hooks run the `main` checkout (PRD v0.2 A9).

**Entry point**: `save_stop_note` (Stop hook) → `last_user_prompt`.

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | A transcript whose last `type: user` entry has `origin.kind == "task-notification"` saves a note whose `prompt` is the Typed prompt before it and whose `trigger` is `task-notification` | K-R2, V-R1 |
| 2 | Same for `<bash-input>` + `<bash-stdout>` (and `<bash-stderr>`) entries: `trigger` `bash` | K-R2 |
| 3 | Same for an entry with `isCompactSummary: true`: `trigger` `compact`; for `[Request interrupted…`: skipped as question, `trigger` absent if a Typed prompt follows | grilling |
| 4 | A transcript with only events: `prompt` is `<trigger>: <first line of the answer>`; no `<` tag text and no task/tool-use id is stored in `prompt` | V-R1 |
| 5 | A Typed prompt turn: the note JSON has the same keys as today (no `trigger` key) — existing Stop-hook tests pass unchanged | V-R1 "unchanged" |
| 6 | `memory_list`, `memory_search`, `memory_read` and the hook index show `[<trigger>]` before the question for a note with `trigger`; no tag for others; the tag passes through `_quoted` | V-R1 |
| 7 | README states the rule: which turns are saved (answer ≥ 200 characters), which become `trigger` notes, and that the question is the last Typed prompt | V-R2 |
| 8 | A test per event kind: task notification, `!` output, Stop-hook feedback (`isMeta`, already skipped), compaction summary — none yields a `prompt` starting with `<task-notification`, `<bash-stdout` or `Stop hook feedback` | K-R2 acceptance |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | fixture transcript: typed prompt, then task-notification entry | note `prompt` = typed text, `trigger` = `task-notification` | automated test |
| 2 | fixture: typed prompt, `<bash-input>`, `<bash-stdout>` | `trigger` = `bash` | automated test |
| 3 | fixture: only a task-notification | `prompt` = `task-notification: <first line>` | automated test |
| 4 | fixture: typed prompt only | note keys identical to today | automated test |
| 5 | note with `trigger` in the store | index / list / search lines carry `[task-notification]` | automated test |

### Verification Command (exact, runnable)

```bash
python3 -m unittest tests.test_v03_m2_event_turns && python3 -m unittest discover -s tests
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-137.md` (review sections are never taken from the board).

## Approach

1. Tests first (red) in `tests/test_v03_m2_event_turns.py`, with fixture transcripts shaped like the real entries (see `PRD_v0.3.md` Facts).
2. Add `_event_kind(entry)` → `"task-notification" | "bash" | "compact" | "interrupt" | None`. Change `last_user_prompt` to return `(prompt, trigger)`; keep one reverse pass over the lines. Add `_turn_entries(transcript)` (the entries after the last Typed prompt) as a small helper, because HUN-138 reuses it — but only if this task needs it; else leave it to HUN-138.
3. `save_stop_note`: set `trigger` only when not None; the no-prompt case builds `<trigger>: <first line>` (redacted like the prompt).
4. Show the tag in `_index_line`, `_tool_list`, `_tool_read`. 5. README rule paragraph.

---

## Edge Case Checklist

- [ ] Typed prompt queued while a background task runs (`queueTranscriptOnly`): the typed prompt is still the question
- [ ] `<bash-stdout>` carries `turnOrigin: "human"`: still an event
- [ ] Compaction summary is `isCompactSummary: true` but NOT `isMeta`
- [ ] Partial last JSON line still ignored (today's behaviour)
- [ ] `<command-name>` slash commands stay as today (`/verify T127`) — not an event
- [ ] `plugin/easy_memory.py` is byte-identical to `easy_memory.py` in the same commit (`tests/test_plugin.py`)
- [ ] Every hook path still exits 0 and prints nothing on error (NFR-004)

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| `easy_memory.py` | `_event_kind`, `last_user_prompt`, `save_stop_note`, tag in `_index_line` / `_tool_list` / `_tool_read` |
| `tests/test_v03_m2_event_turns.py` | new |
| `README.md` | which turns become notes |
| `plugin/easy_memory.py` | copy of `easy_memory.py` |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| `experiments/`, `site/`, `docs/RELEASE_v0.1.0.md` | out of scope |
| `report_command`, switch code, `INDEX_*` values | measurement code (PRD v0.2 Gate 2a) |
| any `~/.easy-memory/` store, user's real `~/.claude*` | tests use a throwaway `EASY_MEMORY_HOME` / config dir |
| `agents/`, `skills/`, `.claude/` | the repo's own dev kit |

## Test Plan

`python3 -m unittest tests.test_v03_m2_event_turns`, plus the existing `tests/test_t002_hook_stop.py` unchanged. Then `python3 -m unittest discover -s tests` (full suite, 434 tests at `cb876eb`).

## Completion Checklist

- [ ] Tests written first and failing, then passing
- [ ] Full suite passes, output pasted
- [ ] README updated where an AC says so
- [ ] Not merged into `main` unless the Merge gate above is open
- [ ] Report: `Status: done` with commits, or `Status: blocked` + `Question:`