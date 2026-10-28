# learnings.md — Cold Tier: Clarifications, Patterns & Gotchas

> **Rules**: Supervisor-only writes. Each entry dated (`YYYY-MM-DD`) and citing the file/task it came from (the diff-driven pass greps this file by changed file path).

## Requirement Clarifications

## Patterns

- 2026-10-28 — Board setup without a terminal: `board_sync.py init` needs `/dev/tty`. Call `board_sync.init(root, ask, make_adapter, env, out, err)` from Python with a scripted `ask`. Create issues in dependency order with `create --guide`, then rewrite forward `Txxx` references to the new IDs and push each with `update --guide` (`scripts/board_sync.py`).

- 2026-10-28 — Store folders: `os.makedirs`/`mkdir(mode=)` obey the umask and race under concurrent writers; create with explicit `chmod` and tolerate `FileExistsError` (`easy_memory.py` `_private_dir`, HUN-74).
- 2026-10-28 — Hook stubs and later hook handlers must write nothing to stdout (it joins the prompt) and must catch argparse exit 2 to keep exit 0 (NFR-004) (`easy_memory.py`).
- 2026-10-28 — Stop hook (HUN-75): bare-name citations resolve through `git ls-files` only when unique; paths are `realpath`-checked against the repo root so `..` and escaping symlinks are rejected; citation regex length-capped to avoid quadratic scan (`easy_memory.py` `cited_files`). `hook-stop` swallows argparse exit 2 and always exits 0; p95 0.063 s on 7,000 files.
- 2026-10-28 — Weights (HUN-76): tests that patch `subprocess.Popen` also patch git calls; use a spy that intercepts only `build-weights` argv. Experiment 03 answers live only in git history (`6452883`); extract them outside the repo and pass `EASY_MEMORY_EXP03_DIR` to `tests/parity_t003.py`. Known gap: two callers can both replace the same stale build lock.

## Gotchas

- 2026-10-28 — `README.md` says raw agent answers stay local (`.gitignore`), but the repo had no `.gitignore` and `experiments/*/results/*.json`, `experiments/*/work/`, run logs and `.pyc` files are tracked and already pushed in commit `6452883`. They may quote orderly/tapchat source. Open: ask the user whether to untrack them (`README.md`, `experiments/`).
- 2026-10-28 — `gh` is not authenticated on this machine; use SSH git remote `github` for push, and WebFetch for public repo pages (`scripts/`, remote `github`).

