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

**AFTER**: same script, 2026-10-30T15:50:39Z, after the change (implementation commit on `v03-m6-trash`); the `forget` call, then `tools/list`, then `memory_restore`:

```
2026-10-30T15:50:39Z saved <tmp>/.easy-memory/c5aa0c6dafcc6672/notes/20261030T155039275-5ac93bf2.json
forget reply: Moved note 20261030T155039275-5ac93bf2 to the trash. Restore it with memory_restore within 30 days; after that it is deleted.
tools: ['memory_search', 'memory_read', 'memory_list', 'memory_forget', 'memory_restore']
restore reply: {'content': [{'type': 'text', 'text': 'Restored note 20261030T155039275-5ac93bf2.'}], 'isError': False}
2026-10-30T15:50:39Z note file exists: True
store contents: ['meta.json', 'notes', 'trash'] trash dir exists: True
trash folder mode: 700
```

**DELTA**: A forgotten note now sits in `trash/` for 30 days and `memory_restore <id>` brings it back; before, `memory_forget` deleted the file for good.

**WITNESS**: [who ran it and when — derived from `memory/event-trace/Txxx.jsonl`, never the
implementing agent alone]

## Security review

**Date**: 2026-10-31 · **Commit reviewed**: `c946f87` · **Scope**: `git diff main...HEAD` (code: `easy_memory.py`, `plugin/easy_memory.py` — byte-identical, `cmp` clean)

**Command**: `Skill({ skill: "security-review" })` was invoked, but it ran against the main checkout (`main` vs `origin/main`, docs-only diff), not this worktree. The same review was then done by hand in the worktree on `git diff main...HEAD -- easy_memory.py`, using the skill's criteria (confidence >= 8 to report; DoS, on-disk secrets, theoretical races excluded). `python3 -m unittest tests.test_v03_m6_trash` → `Ran 31 tests ... OK`.

**Result: no High or Medium findings.**

Checked and found sound:
- Path traversal: `memory_forget` / `memory_restore` ids go through `valid_note_id` (`[A-Za-z0-9._-]{1,128}`, no `..`) and `_note_path` (easy_memory.py:1457), now with a `folder` argument fixed by the code (`"notes"` / `"trash"`), never from MCP input. `lstat` refuses symlinks; the `realpath` parent check keeps the file inside the folder.
- Overwrite on restore / forget: `_move_note` (easy_memory.py:1530) uses `os.link` + `os.unlink`; `link()` fails with `EEXIST` on any existing target (also a dangling symlink) and does not follow a source symlink. A restore never replaces a live note; a forget never replaces a trashed one. Failed unlink of the source removes the new link, so one copy stays.
- Symlinks: `trash/` symlink is refused in `_tool_forget` (easy_memory.py:1558) and in `redact_command`; `_purge_trash` (easy_memory.py:1541) uses `lstat` and deletes only regular files.
- File modes: `_private_dir(trash)` makes `trash/` 0700; a hard link keeps the inode, so the file stays 0600. `redact --apply` rewrites trash files via `_atomic_write` (0600).
- Exposure: search, list, read and the prompt hook read only `notes/` (easy_memory.py:153, :685, :1328); trash is not reachable through them. `uninstall --purge` removes the whole store, trash included.
- Redact: covers `trash/` in dry run and `--apply`; prints ids and counts only, never matched text.
- Races: concurrent forget/restore of one id end in `FileExistsError` or "not found", never data loss. Swapping files between `lstat` and `link` needs write access to the user's own 0700 store — outside the threat model.

Residual risk (Low, by design — not a vulnerability, recorded for the owner):
- L1 — A secret survives `memory_forget` (easy_memory.py:1558). Before this change, forget deleted the file at once; now the note stays in `trash/` in clear text (0600) for at least 30 days, and longer if no later `memory_forget` runs, because `_purge_trash` runs only from forget (easy_memory.py:1576). Scenario: a user forgets a note to get rid of a leaked token, believing it is gone; the token stays on disk until a later forget after 30 days. There is no "delete now" path except `redact --apply` or `uninstall --purge`. Mitigation already present: the forget reply and README say the note is kept 30 days, and `redact` scans the trash. Optional fix (owner decision): a `memory_forget` `permanent: true` flag, or a README line "to remove a secret now, run `redact --apply`".
