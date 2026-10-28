# learnings.md — Cold Tier: Clarifications, Patterns & Gotchas

> **Rules**: Supervisor-only writes. Each entry dated (`YYYY-MM-DD`) and citing the file/task it came from (the diff-driven pass greps this file by changed file path).

## Requirement Clarifications

## Patterns

- 2026-10-28 — Board setup without a terminal: `board_sync.py init` needs `/dev/tty`. Call `board_sync.init(root, ask, make_adapter, env, out, err)` from Python with a scripted `ask`. Create issues in dependency order with `create --guide`, then rewrite forward `Txxx` references to the new IDs and push each with `update --guide` (`scripts/board_sync.py`).


## Gotchas

- 2026-10-28 — `README.md` says raw agent answers stay local (`.gitignore`), but the repo had no `.gitignore` and `experiments/*/results/*.json`, `experiments/*/work/`, run logs and `.pyc` files are tracked and already pushed in commit `6452883`. They may quote orderly/tapchat source. Open: ask the user whether to untrack them (`README.md`, `experiments/`).
- 2026-10-28 — `gh` is not authenticated on this machine; use SSH git remote `github` for push, and WebFetch for public repo pages (`scripts/`, remote `github`).

