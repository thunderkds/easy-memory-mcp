# PRD v0.3 (requirement gate passed; tasks HUN-135..140 created 2026-10-30) — easy-memory-mcp

Source: two requirement lists observed on 2026-10-30, one from the personal-agentic-claude kit (K-R1..R5) and one from the easy-verifier-mcp repo (V-R1..R5). Check of each claim against the code: commit `cb876eb`.

## Closed before grilling

| Item | Outcome | Date |
|------|---------|------|
| K-R1 install by other users | Repo stays private (owner). README, plugin and marketplace descriptions say access is required (`cb876eb`). | 2026-10-30 |
| K-R5 slash-command question | Dropped by the user: the stored question is already `<command> <args>`; a wrong arg cannot be recovered. | 2026-10-30 |

## Items in grilling

| ID | Task | Item | From | Gate (PRD v0.2) |
|----|------|------|------|-----------------|
| M2 | HUN-137 | Event-triggered turns: question, skip or flag rule | K-R2, V-R1, V-R2 | Gate 2a (changes which notes rank; note schema) |
| M3 | HUN-139 | Branch-aware DELETED flag | K-R3 | Gate 2a (note schema) |
| M4 | HUN-138 | Citation = file the turn read or edited | V-R3 | Gate 2a (note schema, ranking text) |
| M5 | HUN-140 | Ranking: common-word prompts, long notes, stated cap | V-R4 | Gate 2a (`INDEX_*`, scorer) |
| M6 | HUN-135 | Recoverable `memory_forget` | V-R5 | none: merge when ready (does not change ranking) |
| M7 | HUN-136 | Save -> search within 1 s | K-R4 | none: repro and test first; fix or document |

## Decision record

| Decision | By | Date |
|----------|----|------|
| Keep the v0.2 gates. Build all items now, one branch each, with tests. Merge M6 and M7 when ready. Hold M2-M5 until the sample bar is met and the report is done (Gate 2a). | user | 2026-10-30 |
| M2 rule: an event entry (`origin.kind == "task-notification"`, `<bash-input>`/`<bash-stdout>`/`<bash-stderr>`, `[Request interrupted`, a compaction summary with `isCompactSummary: true`) is never the question. The question is the last prompt the user typed before it; the note gets `trigger: "task-notification" \| "bash" \| "compact"` (absent for a typed prompt), shown as a tag in `memory_list`, `memory_search` and the hook index. The 200-character answer rule is unchanged. No typed prompt in the transcript: question = `<trigger>: <first line of the answer>`. Raw tags and internal ids are never stored as the question. | Supervisor (user delegated: "as your choose") | 2026-10-30 |
| M4 rule: a repo file is cited only if the answer names it (today's `CITED_PATH` match) AND the same turn touched it: a `file_path`/`notebook_path` of Read, Edit, Write, MultiEdit or NotebookEdit, a `path` of Grep or Glob, or the path inside a Bash `command`. Turn = transcript entries after the last typed prompt (same boundary as M2). Sub-agent reads (sidechain files) are not counted. | user | 2026-10-30 |
| M5 rule: (a) BM25 length adjustment of the note score (`b = 0.75`, average length over the repo's notes); (b) a note is a candidate only if it matches at least one rare prompt word: a word missing from the weights `df`, or one with `df <= RARE_SHARE * n`. `RARE_SHARE` is a fixed constant set on fixtures in Stage 2. `INDEX_FLOOR`, `INDEX_MAX_NOTES` (5) and `INDEX_MAX_CHARS` (2,500) stay; the README states the cap. Gate 2a also needs the offline check on experiment 03 data, which is missing (PRD v0.2 O2, owner: user). | user | 2026-10-30 |
| M3 rule (taken from K-R3 as written, no question needed): the note stores `git: {"branch": <name or "">, "commit": <HEAD sha>}` at save. A cited file missing from the worktree is flagged `NOT-ON-BRANCH:<path>` with `(saved on <branch>@<sha7>)` when the saving branch tip has the path, or, if that branch no longer exists, when the saved commit has it. Otherwise `DELETED:<path>`. One `git cat-file --batch-check` call per hook run, with the existing git timeout. CHANGED is unchanged. | Supervisor (requirement explicit) | 2026-10-30 |
| M6 rule: `memory_forget` moves the note to `<store>/trash/` (0700 folder, file keeps 0600); trashed notes are not read by search, list, read or the hook. New MCP tool `memory_restore <id>` moves it back (error if the id is not in the trash, or a note with that id exists). Trash entries older than 30 days (by move time) are purged at the next `memory_forget`. Unknown id: clear error, as today. The forget reply names the restore tool and the 30 days. | user | 2026-10-30 |
| M7 (no question needed): first a scripted run (fake Stop hook input, then `memory_search` over MCP, both as subprocesses) must find the note within 1 s; it becomes a test. If it passes, the delay is outside easy-memory's write path: record the finding and document it in the README; no code change. | Supervisor | 2026-10-30 |

| Old notes are not rewritten. M2, M3 and M4 apply to notes saved after the merge. New fields (`trigger`, `git`) are optional: a note without them behaves as today. `FORMAT_VERSION` stays 1 (NFR-007). | user | 2026-10-30 |

## Non-functional requirements

| ID | Requirement |
|----|-------------|
| NFR-001 (kept) | Stop hook and prompt hook each stay within 2 s. M4 reads only the entries after the last typed prompt, in the same transcript pass as `last_user_prompt`. |
| NFR-009 (new) | `tests/bench_t004.py` prompt-hook p95 is not worse by more than 10% after M3 and M5. M3 makes at most one git call per hook run. |
| NFR-004 (kept) | Every hook exits 0 and prints nothing on error; a failure is one `hook.log` line. |

## Gate sign-off

Requirement grilling: PASS (2026-10-30). Every item traces to an observed requirement (K-R2..R4, V-R1..R5); each rule above is fixed enough that two engineers build the same thing. Open, not blocking planning: `RARE_SHARE` value (Stage 2, on fixtures); experiment 03 data for the Gate 2a offline check (PRD v0.2 O2, user).

## Facts found in grilling

- Transcript shapes (300 recent sessions): a task notification is a `type: user` entry with `origin.kind == "task-notification"`; a `!` command is two entries, `<bash-input>` then `<bash-stdout>`; a compaction summary is a `type: user` entry with `isCompactSummary: true`, not `isMeta` (2 saved notes have it as the question); Stop-hook feedback is `isMeta: true`, so `last_user_prompt` already skips it (no saved note starts with `Stop hook feedback`).
- Tool use in the same 300 sessions: Bash 2,721, Read 188, Write 107, Edit 40. So M4 must parse paths inside Bash commands, or most touched files are missed.
