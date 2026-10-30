# BRAINSTORMING_LOG.md — v0.3
**Generated**: 2026-10-30
**Task / Context**: `PRD_v0.3.md` items M2-M7 (requirement gate passed 2026-10-30)
**Skill**: `Skill({ skill: "brainstorming" })` — tier **Standard**: the rules are fixed in grilling; the open choice is how to cut and order the work.

---

## The Problem Space

Six fixes to one file, `easy_memory.py` (1,773 lines), copied byte-for-byte to `plugin/easy_memory.py` (`tests/test_plugin.py` checks it). Four of them (M2-M5) must stay unmerged until Gate 2a (sample bar met, report done); M6 and M7 merge when ready. Non-negotiable: hooks exit 0 and stay under 2 s (NFR-001, NFR-004), store `FORMAT_VERSION` stays 1, old notes are not rewritten.

Where each item lands (verified at `cb876eb`):

| Item | Functions touched | Side |
|------|-------------------|------|
| M2 event turns | `_typed_text` :257, `last_user_prompt` :276, `save_stop_note` :364, `_index_line` :641, `_tool_list` :1507 | save + display |
| M4 citations | `cited_files` :228, `save_stop_note` :364 | save |
| M3 branch flags | `save_stop_note` :364, `_file_flags` :610 | save + read |
| M5 ranking | `score` :417, `_index_lines` :651 | read |
| M6 trash | `_tool_forget` :1522, `MCP_TOOLS` :1407, `MCP_HANDLERS` :1531, `redact_command` :1686 | MCP |
| M7 save->search | tests only (unless the repro fails) | test |

M2, M4 and M3 all change `save_stop_note`, and M2 and M4 both need the same "entries after the last typed prompt" slice of the transcript. Held branches will sit for days or weeks, so overlapping edits mean rebase conflicts.

---

## Questions for the User

1. Approve Option B (below), or pick A or C?

---

## Alternative Paths

| Option | Name | Summary | Invasiveness | Code Volume | Regression Risk | Recommended? |
|--------|------|---------|-------------|------------|----------------|--------------|
| A | Six independent branches | Each item branches from `main` | Low per branch | ~450 lines + tests | Medium (3 branches conflict in `save_stop_note`) | |
| B | Two stacks + two singles | Save stack M2 -> M4 -> M3 (each branches from the one before); M5, M6, M7 from `main` | Low | ~400 lines + tests | Low | ✅ Yes |
| C | Bundle the save path | One task "save path v2" = M2+M4+M3, plus M5, M6, M7 | Medium (one C3 task) | ~400 lines + tests | Medium (big review) | |

### Option A — Six independent branches
**Approach**: six tasks, six branches off `main`, merged in any order once their gate opens.
**Pros**: matches the grilling wording exactly; any item can be dropped alone.
**Cons**: M2 and M4 each write their own transcript-slice helper; M2, M3, M4 conflict in `save_stop_note` at merge.
**Why it might fail**: the third merge needs a hand-resolved conflict in the save path while the live hooks run this checkout (PRD v0.2 A9) — a bad resolution breaks note saving silently (hooks only log to `hook.log`).

### Option B — Two stacks + two singles
**Approach**: still one task and one branch per item. M2 adds `_turn_entries(transcript)` (entries after the last typed prompt) and the `trigger` field. M4 branches from M2 and reuses `_turn_entries` for touched files. M3 branches from M4 and adds the `git` field and `NOT-ON-BRANCH`. M5, M6, M7 branch from `main`. Merge order at Gate 2a: M2, M4, M3 (fast-forward chain), then M5.
**Pros**: one helper, no save-path conflicts; each task stays C1-C2 and reviewable alone; M6/M7 ship now.
**Cons**: M4 cannot merge without M2, M3 without M4; a fix in M2 after M4 starts needs a rebase of M4 and M3.
**Why it might fail**: if review of M2 drags, the whole save stack waits. Mitigation: M2 is the smallest of the three; review it first.

### Option C — Bundle the save path
**Approach**: one C3 task for M2+M4+M3, plus three small tasks.
**Pros**: one branch, one review, no stack bookkeeping.
**Cons**: C3 with Medium-High risk; one bug blocks all three fixes; a reviewer sees ~300 lines at once.
**Why it might fail**: the bundle is the kind of task that hides a regression in the save path behind two unrelated features.

---

## 50% Rule Check

- **M7**: likely zero code. The save is synchronous (`write_note` -> `_atomic_write`) and search reads note files directly, so the repro test is the whole deliverable unless it fails.
- **M3**: store only `commit` and check `<commit>:<path>` — half the git logic. Rejected: K-R3 says DELETED only when the file is gone from the *saving branch* too, which needs the branch tip.
- **M6**: no purge, keep the trash forever — saves the purge code (~15 lines). Rejected: 30-day retention was decided in grilling.
- **M4**: count only Read/Edit/Write paths, skip Bash — saves the command parser. Rejected: Bash is 2,721 of ~3,050 file-relevant tool calls in 300 recent sessions; without it most touched files are missed.

---

## Recommended Path

**Option B — Two stacks + two singles.** Six tasks as decided in grilling, with M4 stacked on M2 and M3 stacked on M4 so the save path has one helper and no merge conflicts.

---

## Edge Case Checklist (for the TASK_GUIDEs)

**M2**
- Typed prompt queued while a background task runs (`queueTranscriptOnly`); the notification comes after it — the typed prompt is still the question.
- `<bash-stdout>` carries `turnOrigin: "human"`; it is still an event, not a question.
- Compaction summary (`isCompactSummary: true`, not `isMeta`) — event, trigger `compact`; the typed prompt before it is still in the file.
- Transcript with no typed prompt at all — question `<trigger>: <first line>`, never raw tags.
- The `trigger` tag passes through `_quoted` (no angle brackets reach the index frame).

**M4**
- Edit/Write paths are absolute; convert to repo-relative and drop paths outside the repo root (another worktree is outside).
- Bash paths: quoted, `./x`, `x:12`, globs — match by the same `CITED_PATH` token, then normalise.
- The answer names `a.py:12` — the `:line` suffix is already stripped by `CITED_PATH`.
- A sub-agent hand-back turn touched nothing itself — cites none (accepted in grilling).

**M3**
- Detached HEAD: `branch` is `""`, check the commit only.
- Commit gone (gc, shallow clone) or branch deleted and commit gone: DELETED.
- Not a git repo / no commit: no `git` field, behaviour as today.
- One `git cat-file --batch-check` per hook run, under `GIT_TIMEOUT_SECONDS`; a timeout falls back to DELETED and logs one `hook.log` line.

**M5**
- `memory_search` with no weights file (`{"n": 0, "df": {}}`): every word is "rare", so the rare-word rule does nothing — same as today.
- A prompt with no rare word returns no lines (by design); the MCP reply stays "No matching notes."
- Average note length over the notes read in the same pass — no extra file reads.
- `tests/bench_t004.py` p95 within +10% (NFR-009).

**M6**
- `os.rename` keeps the file's mtime; set it to the move time (`os.utime`) or the 30-day purge counts from the save time.
- `redact --apply` must also scan `trash/`, or a secret survives a forget.
- Restore when a note with that id already exists in `notes/`: error, change nothing.
- `uninstall --purge` already removes the whole store, trash included — test it.
- `memory_restore` falls under the existing allow rule `mcp__easy-memory` (no prompt) — restore is safe to run unprompted.

**All tasks**
- Copy `easy_memory.py` to `plugin/easy_memory.py` in the same commit (`tests/test_plugin.py`).
- Held branches (M2-M5) must not be merged into this checkout before Gate 2a: the live hooks run it (PRD v0.2 A9).
- FR-011 (module split, Gate 1) is not built yet. Build it after M2-M5 merge, so the split covers the new code and four held branches are not rebased onto modules.

---

## Surgical Scope

**Should touch**: `easy_memory.py`, `plugin/easy_memory.py` (copy), new test files `tests/test_m2_*.py` etc. (names set in Stage 2), `README.md` (cap, trash, M7 note), `PRD_v0.3.md`.
**Must not touch**: `experiments/`, `site/`, `docs/RELEASE_v0.1.0.md`, store files of any repo, `report_command` and the switch (measurement code), `INDEX_FLOOR`/`INDEX_MAX_NOTES`/`INDEX_MAX_CHARS` values.

---

## Next Actions (Stage 2)

1. Six TASK_GUIDEs: M2 (C2, Medium), M4 (C2, Medium), M3 (C2, Medium), M5 (C2, Medium), M6 (C2, High: deletes user data), M7 (C1, Low).
2. Set `RARE_SHARE` on a fixture set inside the M5 task, before review.
3. M6 and M7 run first; the save stack M2 -> M4 -> M3 next; M5 in parallel with the stack.
