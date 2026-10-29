**Date**: 2026-10-29
**Complexity Level**: C2
**Risk Level**: High
**Priority**: P0
**Assigned agent**: backend-developer
**Agent guide**: `agents/backend.md`

---

## Mandatory Startup (Do Not Skip)

Before writing any code:

1. Read `PROJECT_SPEC.md`
2. Read the memory slice in your spawn prompt (`<!-- memory-slice -->`). Read `memory/MEMORY.md` in full only if your work reaches a file, hook, skill or decision the slice does not cover
3. Read this file completely
4. Read `agents/backend.md`
5. Note the **Complexity Level** above and apply the matching process from the Complexity matrix in `agents/backend.md`
6. **C2**: read `memory/codebase-map.md` if it exists
7. Read `PRD_v0.2.md` in full: the "FR-009 detail" section is the spec for this task

---

## Requirement (Pillar 1 — Adapt the requirement)

The Stop hook must redact secrets in the prompt and the answer before the note is written. Each hit becomes `[REDACTED:<kind>]`. Patterns are deterministic (no model): private key blocks, AWS access key ids, GitHub tokens (`ghp_`, `gho_`, `github_pat_`), Slack tokens (`xox?-`), `sk-` and `sk-ant-` API keys, JWTs, `Authorization: Bearer ...`, and assignments where the name holds `SECRET`, `TOKEN`, `PASSWORD`, `PASSWD` or `API_KEY`.

**Restated intent** (Supervisor's interpretation, in the project's domain language):

> A note saved after this change never holds a secret in a listed shape. A note with no secret is byte-identical to what v0.1 would save. Cited-file hashes do not change. The hook stays within 2 s and still never blocks the user.

**Out of scope** (what this task explicitly does NOT do):

* Rewriting notes already saved (the `redact` command is the next task; expose a reusable function for it).
* Any change to ranking, the index, the store location, the switch or the report.
* Redacting Claude Code's own transcripts.

**Requirement Refs**:

* US-008, FR-009 (save-time part), NFR-001 (2 s), NFR-004 (exit 0), NFR-008 (1 MB ReDoS test), A6 and A10 in `PRD_v0.2.md`

### Requirement Fidelity Gate (sign off BEFORE implementation)

- [ ] Restated intent confirmed to match the user's request (by Supervisor / user — not the implementing agent)
- [ ] Domain terms align with `PROJECT_SPEC.md` glossary
- [ ] Every Acceptance Criterion below traces to a line in the Requirement
- [ ] All Requirement Refs exist in `PRD_v0.2.md` and are fully covered by the Acceptance Criteria

> An agent must NOT start implementing until this gate is checked. If anything here is unclear,
> STOP and ask the Supervisor (Karpathy: Think Before Coding).

---

## Dependencies & Reachability

**Depends on**: "Hook-prompt tests pass on any day" — the full suite must be green on any day to show this change breaks nothing.

**Entry point**: `hook-stop` subcommand of `easy_memory.py` → `save_stop_note` (`easy_memory.py:299`)

**Build in a worktree.** The live hooks run from this checkout (A9). Nothing merges until the user approves.

---

## Acceptance Criteria

| \# | Criterion (testable) | Traces to requirement |
| -- | -- | -- |
| 1 | One fixture per pattern kind: after `hook-stop`, the saved `prompt` and `answer` hold no secret text and hold `[REDACTED:<kind>]`. | FR-009 |
| 2 | A no-secret fixture saves a note whose `prompt` and `answer` are byte-identical to the input. | FR-009 |
| 3 | `files` (cited-file hashes) is the same with and without a secret in the answer; `MIN_ANSWER_CHARS` and `cited_files()` use the raw answer. | FR-009 call site |
| 4 | A private key block with no `END` line is redacted to the end of the text (fail closed). The fallback is written as `|.*`, not `|\Z`. | FR-009 |
| 5 | `risk-…` and `task-…` are not redacted (`sk-` look-behind `(?<![A-Za-z0-9_-])`). `token: string` is not redacted; `TOKEN=abc` and `token: <8+ chars>` are. | FR-009 |
| 6 | A 1 MB adversarial input (repeated `BEGIN`, long `NAME` runs, long lines) redacts in well under 2 s; the time is printed in the test output. | NFR-008 |
| 7 | If the redactor raises, the hook exits 0, prints nothing, logs one line to `hook.log` and writes no note. The redactor itself does not catch errors. | NFR-004, fail closed |
| 8 | `tests/bench_t004.py` p95 is not worse than before the change (before and after numbers pasted). | Gate 0 |
| 9 | All v0.1 tests still pass. | Gate 0 |

---

## Evaluation & Acceptance (How we know the agent worked correctly)

> The reviewer fills **Evidence** at Stage 4/5 in `tasks/TASK_REVIEW_<ID>.md`, copied from
> `templates/TASK_REVIEW_template.md`. A task is **not done** until every row has evidence.

### Success Criteria (observable, pass/fail)

| \# | Given (input/state) | Expect (output/behavior) | How it's checked |
| -- | -- | -- | -- |
| 1 | Stop JSON whose answer holds `ghp_` + 36 chars | note answer holds `[REDACTED:github_token]`, not the token | unittest |
| 2 | Stop JSON with no secret | note text byte-identical to input | unittest |
| 3 | 1 MB input of repeated `-----BEGIN RSA PRIVATE KEY-----` | redacted, under 2 s | unittest with timing |
| 4 | Redactor patched to raise | exit 0, no note, one `hook.log` line | unittest |

### Verification Command (exact, runnable)

```bash
python3 -m unittest discover -s tests -v 2>&1 | tail -5 && python3 tests/bench_t004.py
```

### Evidence (filled by reviewer at Stage 4/5)

> **Moved.** See `tasks/TASK_REVIEW_HUN-85.md` (review sections are never taken from the board).

## Demonstration

> **Moved.** See `tasks/TASK_REVIEW_HUN-85.md` (review sections are never taken from the board).

## Approach

**Vital slice**: a `redact_text(text) -> (text, hits)` function with the pattern table, called on `prompt` and `answer` in `save_stop_note` after `last_user_prompt` and just before the `write_note` dict.
**Cut list**: Configurable patterns; entropy-based detection; per-repo allowlists.

* Private key: one whole-text DOTALL regex, run only when the text holds `PRIVATE KEY`.
* All other patterns: per line, with a bounded name part such as `[A-Z0-9_.-]{0,64}`.
* `hits` (kind → count) is for the next task's dry-run output. Never log matched text.
* Keep it in `easy_memory.py` (the module split is gated to Gate 1).

**Conventions**: Python 3, standard library only (NFR-005). `unittest`. Follow `docs/claude-md/code-naming-conventions.md`. Tests use `EASY_MEMORY_HOME` temp dirs. Fixture secrets are fake and obviously so (for example `ghp_` + `0123456789abcdef...`); never paste a real key.

---

## Edge Case Checklist

- [ ] Two secrets on one line.
- [ ] A secret at the very start or end of the text.
- [ ] Windows line endings.
- [ ] `sk-ant-` is reported as one kind, not as `sk-` too.
- [ ] A JWT inside a URL.
- [ ] Non-ASCII text around a secret.
- [ ] Empty prompt.

---

## Files to Change (Predicted)

| File | Change |
| -- | -- |
| easy_memory.py | `redact_text` and pattern table; call in `save_stop_note` |
| tests/test_t010_redact.py | new |

## Files Must NOT Touch

| File | Reason |
| -- | -- |
| ranking, index, switch, report code in easy_memory.py | Gate 2a / measurement must not change |
| experiments/\*\* | read-only evidence |

---

## Test Plan

Unit tests per pattern, a no-secret byte-identity test, a 1 MB timing test, a fail-closed test, and the full suite. Benchmark before and after with `tests/bench_t004.py`.

---

## Completion Checklist

- [ ] Implementation done
- [ ] Self-review: `Skill({ skill: "code-review" })` run
- [ ] Security review: `Skill({ skill: "security-review" })` run (Risk High)
- [ ] Lint passes (`python3 -m py_compile easy_memory.py`)
- [ ] Tests written AND pass — output pasted into the TASK_REVIEW Evidence table (Hard-Stop Gate 5)
- [ ] `Skill({ skill: "verify" })` run
- [ ] Supervisor notified: task ready for Stage 4 review