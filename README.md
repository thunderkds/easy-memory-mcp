# easy-memory-mcp

**Status:** working prototype (v0.1.0 planned, not yet installed on a real repo). `easy_memory.py` is one file, standard library only. The experiments below came first; the code follows their result.

## Use it

### As a Claude Code plugin (no clone)

The repo `thunderkds/easy-memory-mcp` is private. Only GitHub accounts with access to it can add the marketplace or install the plugin; for anyone else the clone fails with `Repository not found` or a password prompt.

In Claude Code:

```
/plugin marketplace add thunderkds/easy-memory-mcp
/plugin install easy-memory@easy-memory
```

The plugin runs the same Stop and prompt hooks and the same MCP server, and saves notes in the same `~/.easy-memory/`. It does not edit your settings. Its MCP tools have new names, `mcp__plugin_easy-memory_easy-memory__memory_search` and so on, so the old allow rule `mcp__easy-memory` does not match them. To open notes without a permission prompt, add this rule to `permissions.allow` in your settings yourself (a plugin cannot set permissions):

```
mcp__plugin_easy-memory_easy-memory
```

If you installed the old way, run `python3 easy_memory.py uninstall` (no `--purge`) first — your notes stay. If you skip it, the plugin's hooks do nothing while the old hooks are in your settings (still one note per turn), but both MCP servers run and every tool shows up twice. The plugin puts `easy-memory` on the Bash PATH: `easy-memory switch [on|off|auto]`, `easy-memory report`, `easy-memory redact [--apply]`.

### From a clone

Run these from the main checkout, never from a git worktree. The hook commands keep an absolute path.

```bash
python3 easy_memory.py install --dry-run   # preview the change to your Claude Code settings
python3 easy_memory.py install             # add the Stop and prompt hooks, the MCP server and the allow rule
python3 easy_memory.py switch [on|off|auto]  # per repo; auto is on for even days, off for odd days
python3 easy_memory.py report              # sessions with memory on against off
python3 easy_memory.py redact [--apply]    # list saved notes (and trashed notes, shown as trash/<id>) that hold a secret (dry run); --apply rewrites them
python3 easy_memory.py uninstall [--purge] # remove it; --purge also deletes ~/.easy-memory
python3 -m unittest discover -s tests      # the test suite
```

What it does: after each answer of 200 characters or more, the Stop hook saves a note under `~/.easy-memory/`. On your next prompt, the prompt hook adds a short index of matching notes. The agent can open one with the MCP tool `memory_read` (the tools are `memory_search`, `memory_read`, `memory_list`, `memory_forget` and `memory_restore`). Notes are saved in clear text with mode 0600. `memory_forget` does not delete a note: it moves it to `~/.easy-memory/<repo-key>/trash/`, and `memory_restore <id>` brings it back for 30 days. A trashed note older than 30 days is deleted at the next `memory_forget`. Search, list, read and the prompt hook do not see trashed notes. `redact` also scans the trash, and `uninstall --purge` deletes it with the rest of the store.

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
