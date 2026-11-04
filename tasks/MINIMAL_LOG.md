# Minimal-track Decision records

> One Decision record per minimal-track task (`docs/claude-md/tracks.md`), **newest first**: insert each
> new record directly under this note. The same block is the Supervisor's final chat message.

## HUN-204 follow-up — old-host test scans tracked files only · minimal
**Asked:** "add the permission and do it" (2026-11-05: merge HUN-204 and HUN-218). After the merge, `test_easy_kit_link_points_to_easy_kits_and_the_old_host_is_gone` failed on `main`.
**Decisions:**
- Cause: the test walked every file on disk. On `main` it found the old host in git-ignored local trace logs (`memory/event-trace/HUN-211.jsonl`, `_untagged.jsonl`, `HUN-82.jsonl`). The HUN-204 worktree had no such logs, so it passed there.
- Fix: scan `git ls-files` only, as `tests/test_no_legacy_names.py` does; `tasks/` stays excluded. No new task ID: this is HUN-204's own test.
**Checked:**
- Red: on `main` after both merges, `Ran 541 tests` `FAILED (failures=1, skipped=7)`, the failure above
- Green: `python3 -m unittest discover -s tests` — `Ran 541 tests`, `OK (skipped=7)`
- Negative: the old host appended to `README.md` → the test fails with `['README.md'] != []`; restored → OK
**Files:** `tests/test_site_page.py`, `tasks/MINIMAL_LOG.md`
**Not done:** push (yours)

## HUN-218 — Legacy project names replaced by Project A / Project B · minimal
**Asked:** "update the legacy naming like [the two test repos] in the coding, by using a symbol like Project A, project B" (2026-11-04)
**Decisions:**
- First test repo → `project-a` / Project A; second → `project-b` / Project B — the user's own suggestion; letters carry no hint of the real names.
- Python names `project_a` / `project_b`, constants `PROJECT_A` / `PROJECT_B`, string keys `"project-a"` / `"project-b"`; prose and tables say Project A / Project B.
- The two hard-coded checkout paths (which also named a client and an org folder) became env vars `EASY_MEMORY_PROJECT_A` / `EASY_MEMORY_PROJECT_B` (default `~/project-a`, `~/project-b`) in `experiments/02-auto-memory/harness.py`.
- All tracked text files changed, including old guides, reviews, memory and one HTML report; old guides are also pushed to the board, or the next pull would restore the names.
- Git history and the remote's history are not rewritten (needs a force-push; not asked). Local, untracked experiment result folders keep their old keys, so re-grading old results needs a rename of those folders.
**Checked:**
- New test `tests/test_no_legacy_names.py` — failed before the change (`Lists differ: ['BRAINSTORMING_LOG.md:22', …] != []`, 119 lines), passes after; names built from pieces so the test does not match itself
- Suite: `python3 -m unittest discover -s tests` — `Ran 536 tests`, `OK (skipped=7)`
- Real run: every changed `.py` passes `py_compile`; `prepare.sh` passes `bash -n`; experiment 02 imports print `exp02 imports ok ['project-a', 'project-b']`, and `EASY_MEMORY_PROJECT_A=/tmp/x` gives `{'project-a': PosixPath('/tmp/x'), …}`; `python3 easy_memory.py switch` printed `switch: auto`
**Files:** 36 tracked files (`easy_memory.py` comment, `plugin/easy_memory.py`, `experiments/0[1-3]-*`, `README.md`, `PRD.md`, `PROJECT_SPEC.md`, `BRAINSTORMING_LOG.md`, `memory/*`, `tasks/TASK_GUIDE_HUN-7[4-9]..82.md`, `tasks/TASK_REVIEW_HUN-7[67]/82.md`, one report), `tests/test_no_legacy_names.py`, `tasks/MINIMAL_LOG.md`
**Not done:** merge (the user decides); history rewrite

## HUN-199 — report --json with a wrong --repo must not create a store folder · minimal
**Asked:** "do all" (after the HUN-197 merge: HUN-199 and HUN-198)
**Decisions:**
- `report --json` returns 1 with `easy-memory report: no such folder: <path>` on stderr when `--repo` is not a folder, and writes nothing — the stray store folder from the HUN-197 `/verify` run.
- Checked the repo path, not the store folder — AC7 of HUN-197 needs an empty (not yet created) store to still get a `report.json`.
- Plain text `report` left unchanged — it only reads (Gate 2a: measurement code does not move).
- `no_data` documented in README, not changed — it counts the refreshing checkout's own logs; changing that is measurement code (Gate 2a). Groups and medians do not depend on it.
**Checked:**
- New test `MissingRepoTest.test_missing_repo_path_writes_nothing_and_returns_1` — failed before the change (`AssertionError: 0 != 1`), passes after
- Suite: `python3 -m unittest discover -s tests` — `Ran 499 tests`, `OK (skipped=3)`
- Real run: `EASY_MEMORY_HOME=<tmp> python3 easy_memory.py report --json --repo /no/such/path` — printed `easy-memory report: no such folder: /no/such/path`, `exit=1`, the home stayed empty; with `--repo .` exit 0 and `report.json` written
**Files:** `easy_memory.py`, `plugin/easy_memory.py`, `tests/test_v04_report_json.py`, `README.md`, `tasks/MINIMAL_LOG.md`
**Not done:** merge (the user decides)
