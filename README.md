# easy-memory-mcp

**Status:** experiments only. There is no product code yet. The rule is to test first, then plan.

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
