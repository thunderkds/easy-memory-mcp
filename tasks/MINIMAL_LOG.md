# Minimal-track Decision records

> One Decision record per minimal-track task (`docs/claude-md/tracks.md`), **newest first**: insert each
> new record directly under this note. The same block is the Supervisor's final chat message.

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
