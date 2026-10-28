# learnings.md — Cold Tier: Clarifications, Patterns & Gotchas

> **Rules**: Supervisor-only writes. Each entry dated (`YYYY-MM-DD`) and citing the file/task it came from (the diff-driven pass greps this file by changed file path).

## Requirement Clarifications

## Patterns

- 2026-10-28 — Board setup without a terminal: `board_sync.py init` needs `/dev/tty`. Call `board_sync.init(root, ask, make_adapter, env, out, err)` from Python with a scripted `ask`. Create issues in dependency order with `create --guide`, then rewrite forward `Txxx` references to the new IDs and push each with `update --guide` (`scripts/board_sync.py`).

- 2026-10-28 — Store folders: `os.makedirs`/`mkdir(mode=)` obey the umask and race under concurrent writers; create with explicit `chmod` and tolerate `FileExistsError` (`easy_memory.py` `_private_dir`, HUN-74).
- 2026-10-28 — Hook stubs and later hook handlers must write nothing to stdout (it joins the prompt) and must catch argparse exit 2 to keep exit 0 (NFR-004) (`easy_memory.py`).
- 2026-10-28 — Stop hook (HUN-75): bare-name citations resolve through `git ls-files` only when unique; paths are `realpath`-checked against the repo root so `..` and escaping symlinks are rejected; citation regex length-capped to avoid quadratic scan (`easy_memory.py` `cited_files`). `hook-stop` swallows argparse exit 2 and always exits 0; p95 0.063 s on 7,000 files.
- 2026-10-28 — Weights (HUN-76): tests that patch `subprocess.Popen` also patch git calls; use a spy that intercepts only `build-weights` argv. Experiment 03 answers live only in git history (`6452883`); extract them outside the repo and pass `EASY_MEMORY_EXP03_DIR` to `tests/parity_t003.py`. Known gap: two callers can both replace the same stale build lock.
- 2026-10-28 — Prompt hook (HUN-77): note text is untrusted. Index fields are JSON-quoted, whitespace-collapsed, control/format characters stripped, `<`/`>` replaced by `‹`/`›`, ids and cited paths regex-checked; p95 0.238 s on orderly with 200 notes. A test that calls a hook through `main()` must set a temp `EASY_MEMORY_HOME` and stdin, even for a stub (a stub test wrote to the real `~/.easy-memory/hook.log` once; removed).
- 2026-10-28 — Switch (HUN-78): `auto` is on when days since 1970-01-01 are even; `_today()` is the test seam. `hook-prompt` reads the switch first and logs one `prompts.log` line per run with readable input (none for bad stdin: no repo to name); a log failure goes to `hook.log` only. `hook-stop` ignores the switch.
- 2026-10-28 — Report (HUN-80): Claude session JSONL writes one API reply as several lines with the same `message.id`; count once with the largest value per token field. Headline tokens = input + cache creation + cache read + output, as experiments 01 to 03 counted; `in+out` is a separate column. Field names checked against a real log (`sessionId`, `message.id`, `message.usage.*`, `tool_use.name`); sessions are joined to `prompts.log` by session id. Parallel tasks both edit the stub-test tuple in `tests/test_t001_store.py`: keep both sides on merge.

## Gotchas

- 2026-10-28 — `README.md` says raw agent answers stay local (`.gitignore`), but the repo had no `.gitignore` and `experiments/*/results/*.json`, `experiments/*/work/`, run logs and `.pyc` files are tracked and already pushed in commit `6452883`. They may quote orderly/tapchat source. Open: ask the user whether to untrack them (`README.md`, `experiments/`).
- 2026-10-28 — `gh` is not authenticated on this machine; use SSH git remote `github` for push, and WebFetch for public repo pages (`scripts/`, remote `github`).

