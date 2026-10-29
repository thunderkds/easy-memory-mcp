# easy-memory-mcp

**Status:** working prototype (v0.1.0 planned, not yet installed on a real repo). `easy_memory.py` is one file, standard library only. The experiments below came first; the code follows their result.

## Use it

Run these from the main checkout, never from a git worktree. The hook commands keep an absolute path.

```bash
python3 easy_memory.py install --dry-run   # preview the change to your Claude Code settings
python3 easy_memory.py install             # add the Stop and prompt hooks, the MCP server and the allow rule
python3 easy_memory.py switch [on|off|auto]  # per repo; auto is on for even days, off for odd days
python3 easy_memory.py report              # sessions with memory on against off
python3 easy_memory.py redact [--apply]    # list saved notes that hold a secret (dry run); --apply rewrites them
python3 easy_memory.py uninstall [--purge] # remove it; --purge also deletes ~/.easy-memory
python3 -m unittest discover -s tests      # the test suite
```

What it does: after each answer of 200 characters or more, the Stop hook saves a note under `~/.easy-memory/`. On your next prompt, the prompt hook adds a short index of matching notes. The agent can open one with the MCP tool `memory_read` (the tools are `memory_search`, `memory_read`, `memory_list` and `memory_forget`). Notes are saved in clear text with mode 0600.

Known limits: the prompt hook gets slower as notes pile up (about 1 ms per note), and the live check that opening a note causes no permission prompt has not run yet. See [the release page](docs/RELEASE_v0.1.0.md) for the install steps, the rollback plan and the full list. [RUNBOOK.md](RUNBOOK.md) has the day-to-day checks.

## Purpose

Coding agents pay again for what an earlier session already found out. They read the same files again, and long sessions carry every old tool result forward. This project tests one idea: save what a session concluded, and give it to the next session that needs it. The goal is fewer model tokens (input and output) at the same accuracy.

The cost that counts is what the model reads and writes. How fast the store searches does not matter. How good its choice is matters only because a wrong choice adds tokens or rounds.

## Background

This continues easy-context-mcp, which was retired on 2026-10-23. Code search (vectors plus a symbol graph) did not beat plain grep in any test. Memory between sessions was the first idea that did.

## Experiments

| # | Question | Result |
|---|---|---|
| [01](experiments/01-memory-vs-cold/RESULTS.md) | Does memory from the last session cut tokens on a follow-up? | Yes. The previous final answer cut tokens by 58% at the same accuracy and caught a renamed method. Resume was misled. |
| [02](experiments/02-auto-memory/RESULTS.md) | Does it still work when saving, choosing and delivering memory are automatic, across repos? | Risk. It cut tokens by 35% on tapchat and added 4% on orderly, about 15% saved overall. Accuracy was the same, and stale memory misled 0 runs. The picker is the weak part: memory helps only when it already holds the answer. |
| [03](experiments/03-precision/RESULTS.md) | Can more precise injection save tokens on both repos? | Go for a prototype. The index method (list notes, the agent opens one) cut tokens by 29% on tapchat and 27% on orderly. Accuracy was the same, and stale memory misled 0 runs. |

Raw agent answers stay local (`.gitignore`). They quote private source code.
