# Experiment 01 — Memory vs cold vs resume (2026-10-23)

**Question:** A new session gets a follow-up task. Does it use fewer model tokens, with the same accuracy, when it gets memory from the earlier session?

**Verdict:** Yes. When the new session got the earlier session's whole final answer (the "digest"), it used 58% fewer tokens. Accuracy did not change. The digest runs also caught a method that was renamed after the earlier session. Resuming the old session was misled 3 times out of 3.

## Setup

- Repo: project-a (NestJS, 557 TypeScript files), read-only scratch copies (`prepare.sh`).
- Runs: 54 `claude -p` runs, Sonnet (`claude-sonnet-5-5`), `--effort medium`, `--safe-mode`, tools `Read,Grep,Glob`. Spend $3.68.
- 3 task chains. Session A explores a topic. Session B is a related follow-up:
  - **M** — moderation: how a suspension happens and is lifted → where to send a push when a moderator suspends a user.
  - **D** — device tokens: how FCM tokens work → is the token removed at logout?
  - **P** — diamond purchase: end-to-end flow → where can a paid purchase fail to add diamonds?
- Session B ran 3 times in each condition:
  - **cold** — no memory.
  - **notes** — session A's own "NOTES FOR LATER" (8 lines at most).
  - **digest** — session A's whole final answer.
  - **resume** — `--resume <A> --fork-session`.
- Memory goes in the user turn, framed as data that may be out of date. A system-prompt version was blocked by the auto-mode classifier.
- Trap: after the normal runs, `make_stale.sh` renamed `makeDecision` to `decideModeration` in the moderation module. Then 12 more runs (S_M_*).
- Cost comes from `usage` tokens (`grade.py`). For a resumed session, `total_cost_usd` includes session A's cost.

## Results (session B, median per chain, sum of 3 chains)

| Condition | Tokens in+out | Cost | Accuracy | After the rename |
|---|---|---|---|---|
| cold | 249,934 | $0.32 | baseline | not affected |
| notes | 146,604 (−41%) | $0.19 | same | the notes did not contain the method |
| **digest** | **104,029 (−58%)** | **$0.12** | same | **caught it in 3 of 3 runs** |
| resume | 216,844 (−13%) | $0.11 with a warm cache; about $0.44 when it has expired (estimate) | same | **misled in 3 of 3 runs** |

Per chain, digest compared with cold: D −47%, M −28%, P −84%. Memory from the wrong topic (M's digest on D's question) added +2% tokens. It did not reduce accuracy. Full table: `final_table.txt`.

## Findings

1. **The digest beats the notes.** The notes left out the fact that the follow-up needed (`makeDecision` as the decision site). The digest is the final answer, so it costs nothing extra to save.
2. **The words "check before relying" work.** All 3 digest runs re-checked the code: "The notes call this method `makeDecision`, but the code names it `decideModeration`." A resumed session takes its old context as true.
3. **Memory steers the answer.** Chain M had two correct places for the call: the moderation decision and the admin status update. Cold runs found only the admin path (3 of 3). Digest runs found only the moderation path (3 of 3).

## Limits

The test used 1 repo and 1 model, with 3 runs per condition and one session A per chain. Memory was chosen by hand. The follow-ups were related by design. The resume cost with an expired cache is an estimate, not a measurement.

## Not tested here → experiment 02

- Saving memory automatically.
- Choosing which memory fits a new prompt automatically.
- Delivering memory through a real hook.
- Code drift beyond a rename.
- More repos and languages.
