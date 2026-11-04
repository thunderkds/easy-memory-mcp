# Experiment 02 — Automatic memory: save, pick, hook delivery (2026-10-23 to 2026-10-25)

**Question:** Does memory still cut tokens when every step is automatic? That means saving each answer, picking memories for a new prompt, and delivering them through a real hook, on two repos.

**Verdict: RISK. Do not build yet.** Automatic memory cut tokens by 35% on Project A. On Project B it added 4%. Overall the saving was 15%. Accuracy did not change, and stale memory misled 0 runs. The weak part is the picking. A memory saves tokens only when it already holds the answer to the new question. A keyword picker cannot tell that apart from "same domain".

## Setup

- 120 `claude -p` runs, all valid. Spend $9.91. Sonnet, `--effort medium`, tools `Read,Grep,Glob`, and `--setting-sources project --strict-mcp-config`. Repo copies hold git-tracked files only, without agent instruction files.
- Repos: project-a (TypeScript, 557 files) and Project B (Java + TypeScript, 7,394 files). Project B is the repo the picker was not tuned on.
- Each repo has 3 topics with 3 sessions each, run in this order: round a, round b, then the code changes, then round c. There were 3 repeats.
- Conditions:
  - **cold** — the hook is installed but injects nothing.
  - **auto** — `memory_hook.py` (UserPromptSubmit) picks up to 2 earlier answers and adds them as context.
  - **noflag** — auto without the changed-file note. It ran only on the c-sessions of changed topics.
- Saving: the harness stores each auto session's final answer, with a sha256 hash of every repo file the answer cites. A real product would do this in a Stop hook.
- Picking (`memstore.py`): words are weighted by how rare they are in the repo's own source files. The score is the share of the prompt's weight found in the memory. Floor 0.18, at most 2 memories, each within half of the top score. The floor was set on experiment 01's Project A answers.
- Code changes (`changes.py`): one rename per repo (`restoreSuspendedUserByPhoneNumber` becomes `liftSuspensionByPhoneNumber`; `generateInvoicesForConfig` becomes `processRecurringConfig`). One logic change per repo makes an earlier answer false: Project A gains a duplicate check, so a Stripe retry no longer credits twice; on Project B a re-sent order no longer emails the subscribers.
- Resume note: 65 runs hit the weekly usage limit on 2026-10-23. `harness.py repair()` removed the memories that failed runs had saved. It recopied unchanged code before rerunning pre-change sessions, and only the failed runs were redone.

## Results

Per sequence of 9 sessions, median over 3 repeats:

| Repo | Cold tokens | Auto tokens | Change | Score cold → auto |
|---|---|---|---|---|
| Project A | 622,583 | 406,781 | **−35%** | 8.5 → 8.5 of 9 |
| Project B | 687,811 | 713,273 | **+4%** | 9.0 → 9.0 of 9 |

By round, median tokens per session (cold → auto):
- Round a (no related memory yet): Project A 61k → 68k, Project B 84k → 94k. This is agent variance plus memory that does not fit.
- Round b: Project A 62k → 28k (−54%), Project B 70k → 90k (+30%).
- Round c: Project A 74k → 49k (−34%), Project B 72k → 77k (+6%).

By what was picked, b- and c-sessions, sums:
- Only same-topic memories (21 runs): −33% tokens.
- At least one wrong-topic memory (15 runs): −5%.

Stale traps: 12 sessions × 3 conditions = 36 runs, and **0 were misled**. The auto runs flagged the changed files in all 12. The noflag runs were also never misled. The agents re-read the code and said so. Examples: "The code has a duplicate check, which my earlier notes said was missing", and "all renamed since the earlier memory, which called them `restoreSuspendedUserByPhoneNumber`".

## Findings

1. **A memory pays only when it holds the answer.** On Project A, `P_b` used P_a's memory, which already listed the silent early returns: 21k tokens against 112k cold. On Project B, `O_b` used O_a's memory, which is the same topic but covers the success path while the question was about failure: 90k to 138k tokens against 63k to 82k cold. The agent read the memory, then explored anyway. The memory also rode along in every turn.
2. **The picker does not transfer between repos.** Project B's topics share words (invoice, email, supplier, restaurant). Wrong-topic memories scored 0.19 to 0.29, above the floor, and were picked 15 times against 20 correct picks. On Project A it was 6 against 22. A higher floor would drop those, but it would also drop Project A's best savings, which scored 0.20 to 0.24.
3. **Stale safety holds without the file flags.** Framing the memory as "data that may be out of date: verify" was enough in this test. The hash flags fired correctly, but they made no measured difference.
4. **The anchoring from experiment 01 is still there.** `M_b` scored 1.5 of 3 in both conditions.

## Limits

The test used 2 repos, 1 model and 3 repeats. Agent variance is large: the same task cost 51k to 101k tokens. Topics and questions were written by the experimenter, and the picker floor was tuned on Project A.

## Next (if continued)

The open problem is precision: inject a memory only when it is likely to answer the question. Ideas to test, all untested:
- Inject a short index of memory titles with file anchors, and let the agent open one.
- Save smaller, fact-level memories instead of whole answers.
- Ask a small model whether the memory answers the question. This adds model cost.
