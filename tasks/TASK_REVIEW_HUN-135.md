# TASK_REVIEW — HUN-135: memory_forget moves a note to the trash; memory_restore brings it back

> Sibling of `tasks/TASK_GUIDE_HUN-135.md`. Filled by the reviewer at Stage 4/5.

---

## Auto decisions

Mode: auto
1. Spawn model sonnet for this task — FACT: PROJECT_SPEC.md:97 "| claude | `claude` | haiku-5-5 | sonnet-5-5 | sonnet-5-5 | opus-5-5 |"
2. Not merged to `main` by the Supervisor although the request said "merge to main after done" — RULE: `docs/claude-md/tracks.md` `### Never in auto mode` "merge or push"
3. `redact` (dry run and `--apply`) covers `trash/` — DEBATED: rewrite trash like notes (Advocate 1: rewrite trash like notes; Advocate 2: leave trash untouched; Advocate 3: list trash in dry run, apply to notes only) ⚠ decided for you — please review
Checks: (filled at Stage 4)
Not done: merge (yours); auto verify: running (T182)
Paused: auto-mode check failed — extended track, but the trace has no `code-review` Skill call (Stage 4 runs in auto mode); Risk High, but the trace has no `security-review` Skill call

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE**: captured 2026-10-30T15:46:07Z on branch `v03-m6-trash` (commit 38f5014, before any implementation commit). Throwaway `EASY_MEMORY_HOME`; a note saved, then `memory_forget` and `memory_restore` called over `easy_memory.py serve` (JSON-RPC on stdio):

```
2026-10-30T15:46:07Z saved <tmp>/.easy-memory/c5aa0c6dafcc6672/notes/20261030T154607730-535de01a.json
forget reply: Forgot note 20261030T154607730-535de01a.
tools: ['memory_search', 'memory_read', 'memory_list', 'memory_forget']
restore reply: {'code': -32602, 'message': 'unknown tool'}
2026-10-30T15:46:07Z note file exists: False
store contents: ['meta.json', 'notes'] trash dir exists: False
```

The note file is gone, no `trash/` exists, and `tools/list` has no `memory_restore`.

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]
