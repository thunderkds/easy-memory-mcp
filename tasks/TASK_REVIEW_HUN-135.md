# TASK_REVIEW — HUN-135: memory_forget moves a note to the trash; memory_restore brings it back

> Sibling of `tasks/TASK_GUIDE_HUN-135.md`. Filled by the reviewer at Stage 4/5.

---

## Auto decisions

Mode: auto
1. Spawn model sonnet for this task — FACT: PROJECT_SPEC.md:97 "| claude | `claude` | haiku-5-5 | sonnet-5-5 | sonnet-5-5 | opus-5-5 |"
2. Not merged to `main` by the Supervisor although the request said "merge to main after done" — RULE: `docs/claude-md/tracks.md` `### Never in auto mode` "merge or push"
3. `redact` (dry run and `--apply`) covers `trash/` — DEBATED: rewrite trash like notes (Advocate 1: rewrite trash like notes; Advocate 2: leave trash untouched; Advocate 3: list trash in dry run, apply to notes only); re-run 2026-10-31 with 3 Advocate agents: self-ratings high / low / low, and Advocates 2 and 3 conceded because `tasks/TASK_GUIDE_HUN-135.md:73` "| 7 | `redact` (dry run and `--apply`) covers `trash/` | secret must not survive a forget |" ⚠ decided for you — please review
Checks: (filled at Stage 4)
Not done: merge (yours); auto verify: running (T182)
Paused: auto-mode check failed — extended track, but the trace has no `code-review` Skill call (Stage 4 runs in auto mode); Risk High, but the trace has no `security-review` Skill call

## Code review (Stage 4)

`lane: C2, 7 files, 752 lines, EXCEEDS (lines 752 > 500); unpredicted: tasks/TASK_GUIDE_HUN-135.md, tests/test_t008_mcp.py, tests/test_t009_smoke.py`. Warn-only: 430 of the 752 lines are the new test file and 89 are this review file; the code diff is ~150 lines in `easy_memory.py` (+ byte-identical `plugin/easy_memory.py`, `cmp` clean). The unpredicted test edits are required (tool list now has 5 tools); the guide edit is the Questions Log line. Entry point `serve` → `_mcp_call_tool` → `_tool_forget` / `_tool_restore`: found (`MCP_HANDLERS`, easy_memory.py:1594). Reviewed by hand in this worktree on `git diff main...HEAD` with the `code-review` skill's rules (the skill has no worktree argument). Startup-reads check of the implementing agent: not done, its final report was not available to this reviewer. Fresh review at `865aa61`; the earlier review's fix `c946f87` (skip purge when `os.utime` fails) was re-checked and holds.

- P0: none.
- P1: none. All 9 Acceptance Criteria are met (AC1–AC8 by tests in `tests/test_v03_m6_trash.py`, AC9 by the README diff).
- P2 (confidence 100, verified by a probe): `_tool_restore` (easy_memory.py:1581) does not refuse a `trash/` folder that is a symlink, but `_tool_forget` (:1561) and `redact_command` do. `_note_path(..., "trash")` resolves the parent with `realpath`, so the parent check passes through the link. Scenario: `trash -> /elsewhere`, a file `/elsewhere/x-1.json`; `memory_restore {"id": "x-1"}` returns `Restored note x-1.` and the file is moved out of `/elsewhere` into `notes/`. Needs write access to the user's own 0700 store, so not a vulnerability (security review agrees), but the three paths disagree and no test covers restore here. Action: add the same `is_symlink()` refusal to `_tool_restore` and a test; owner may waive.
- P3 (confidence 75): the `c946f87` fix only defers the risk it addresses. If `os.utime` fails (:1572), the trashed note keeps its save time; the purge is skipped now, but the next `memory_forget` whose `utime` succeeds deletes that note at once if it was saved more than 30 days ago. Needs `utime` to fail on one file in the user's own folder and not on the next, so very unlikely. Action: none required; optionally purge by a time recorded elsewhere, or log it in the forget reply.
- P3 (confidence 75): in `_redact_note`, if `os.utime(path, ns=...)` (:1748) fails after `_atomic_write`, the note is rewritten (secret gone) but reported `failed`, and its trash time becomes "now", which extends retention. Harmless direction (secret is removed, note kept longer). Action: none required.
- Residual L1 from the security review (secret stays in `trash/` for at least 30 days after a forget) is by design and stated in the forget reply and README; not repeated as a finding.

Checked, no issue: id validation shared with `_note_path` (no traversal into or out of `trash/`); `_move_note` link+unlink never overwrites and leaves one copy on failure; forget sets mtime to the move time and purges only regular `.json` files older than `TRASH_KEEP_DAYS`; purge errors are logged and forget still succeeds; search, list, read, `read_notes` and the prompt hook read only `notes/` (easy_memory.py:153, :685, :1328); nothing else sorts by note file mtime, so a restored note's new mtime changes nothing; old clients that never call `memory_restore` keep working; no hook path changed (NFR-004).

Actions: Supervisor decides on the P2 (fix in a follow-up commit on this branch, or waive). P3s are suggestions only. No code was changed by this review.

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | `tests/test_v03_m6_trash.py` (new, 31 tests): AC1 `test_forget_then_restore_gives_back_the_same_bytes`; AC2 `test_forget_of_an_unknown_id_is_an_error_and_moves_nothing`; AC3 `test_forgotten_note_is_gone_from_list_search_read_and_the_index`; AC4 `test_restore_of_an_id_not_in_the_trash_is_an_error`, `test_restore_never_overwrites_a_note_with_the_same_id`; AC5 `test_trash_older_than_30_days_is_deleted_at_the_next_forget`; AC6 `test_memory_restore_is_listed_with_the_schema_of_forget`; AC7 `RedactTrashTest` (7 tests); AC8 `test_trash_is_0700_and_a_trashed_file_0600`, `test_uninstall_purge_removes_the_trash`; AC9 README diff (docs, no test). `Ran 31 tests in 2.710s` `OK` (reviewer, 2026-10-31) |
| Verification command run | ☑ pass | `python3 -m unittest tests.test_v03_m6_trash && python3 -m unittest discover -s tests` at `865aa61` → `Ran 31 tests in 2.710s` `OK`; then `Ran 465 tests in 45.663s` `OK (skipped=3)`, exit 0 |
| Negative cases hold | ☑ pass | unknown id → `note not found: <id>`, nothing moved; second forget → not found; forget never overwrites a same-id trash file; restore of a live or unknown id → error; restore never overwrites a note; bad ids and a symlinked trash file refused; symlinked `trash/` refused by forget and redact (not by restore, see P2); failed `utime` skips the purge; purge error logged, forget succeeds |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | reviewed the `easy_memory.py` diff (`TRASH_KEEP_DAYS`, `MCP_TOOLS`, `_note_path`, `_move_note`, `_purge_trash`, `_tool_forget`, `_tool_restore`, `MCP_HANDLERS`, `_redact_note`, `redact_command`), `cmp` with `plugin/easy_memory.py`, their callers and the readers of `notes/` (`read_notes`, `_index_lines`, `_tool_search`/`_tool_list`/`_tool_read`, `uninstall --purge`), README, and the test diffs; nothing outside that set |
| Full smoke suite still green (no regression) | ☑ pass | `Ran 465 tests in 45.663s` `OK (skipped=3)` (434 at `cb876eb` + 31 new); `tests/test_t008_mcp.py` and `tests/test_t009_smoke.py` changed only to expect `memory_restore` in the tool list; `tests/test_t010_redact.py` unchanged |
| **Companion score (easy-verifier)** | ☑ N/A | not run |
| **UI: Visual regression (diff or verdict pasted)** | ☑ N/A | no UI |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☑ N/A | no UI |
| **UI: Responsiveness at target viewports** | ☑ N/A | no UI |

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
