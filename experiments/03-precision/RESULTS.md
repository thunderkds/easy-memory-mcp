# Experiment 03 — Precision: inject memory only when it is likely to help (2026-10-25)

**Question:** Experiment 02 saved tokens on Project A (−35%) but cost more on Project B (+4%), because the picker injected memories that did not answer the new question. Can a more precise way of injecting memory save tokens on both repos?

**Verdict: GO, for a small prototype of the "index" method.** All three methods saved tokens on both repos, with accuracy unchanged and no run misled. The index method saved the most overall and was the most even across repos (−29% and −27%). It also had the least tuning on test data.

## Setup

- 108 `claude -p` runs, all valid after a resume (13 runs hit the usage limit and were rerun). Same model, tools, repos, tasks and code changes as experiment 02.
- Each method ran rounds b and c (6 sessions), 3 repeats per repo. All methods start from the same round-a memories, which are experiment 02's saved answers.
- Baseline: experiment 02's cold runs and auto runs for the same sessions. Both repos' code was the same commit for both experiments.
- Methods:
  - **facts** — split each saved answer into paragraph or bullet chunks. Inject only chunks that score ≥ 0.10 against the prompt, up to 2,000 characters.
  - **judge** — experiment 02's top-2 pick, then Haiku answers "would this note save real exploration for THIS question?". Only YES notes are injected. Haiku's tokens are counted separately.
  - **index** — inject a short list of up to 5 notes scoring ≥ 0.12. Each line gives the earlier question, the first line of the answer, the cited files and any changed files. The full notes are files in `.agent-memory/`, and the agent decides whether to open one.

## Results

Rounds b and c, tokens per sequence of 6 sessions, median over 3 repeats:

| Method | Project A | Project B | Both repos |
|---|---|---|---|
| cold (no memory) | 428,455 | 420,664 | 849,119 |
| auto (experiment 02 picker) | 229,773 (−46%) | 447,162 (+6%) | 676,935 (−20%) |
| facts | 322,268 (−25%) | 333,747 (−21%) | 656,015 (−23%) |
| judge | 304,532 (−29%) | 362,174 (−14%) | 666,706 (−21%), plus about 88k Haiku tokens |
| **index** | **302,825 (−29%)** | **305,146 (−27%)** | **607,971 (−28%)** |

- Accuracy matched cold in every method: 5.5 of 6 on Project A and 6 of 6 on Project B. The one point lost on Project A is the ambiguous `M_b`, the same as in experiments 01 and 02.
- Stale traps: 0 misled in every method.
- Injection size when memory was injected (median): facts about 1,900 to 2,400 characters, index about 1,500 to 2,300, judge about 4,000 (whole answers).

## Findings

1. **Precision fixed the Project B loss.** The costly Project B session `O_b` used 99,543 tokens with auto, 60,313 with facts and 78,657 with index (cold: 67,880). `E_b`, which got a wrong-topic memory in experiment 02, used 29,880 with index (cold: 83,519).
2. **Index wins without needing precise picking.** Its list carried many wrong-topic lines (29 on Project B), but they are cheap, and the agent ignores lines that don't fit. At least 12 of 36 answers say they used a note. The agent judges relevance better than a keyword score does.
3. **Facts and judge each miss the big wins.** Facts missed Project A `P_b` (113,431 against auto's 21,444) because no single chunk matched strongly enough. Judge rejected Project A `M_b`. Both were also tuned on experiment 02 data: the facts floor and the judge question. That makes their numbers slightly optimistic.
4. **Auto is best only when its pick happens to be right** (Project A −46%), and it was the worst method on Project B.

## Limits

The test used 2 repos and 1 model, with tasks written by the experimenter and 3 repeats. Agent cost varies a lot from run to run. The baseline comes from experiment 02's runs, on the same commit and setup but on an earlier day. Saving was done by the harness, not by a real Stop hook.

## Next

Build a small prototype with real hooks and run it on real work. A Stop hook saves each final answer with file hashes. A UserPromptSubmit hook injects the index. Then measure real sessions instead of scripted ones.
