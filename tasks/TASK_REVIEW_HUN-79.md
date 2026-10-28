# TASK_REVIEW — HUN-79: install and uninstall (user-level hooks)

> Sibling of `tasks/TASK_GUIDE_HUN-79.md`. Everything here is **filled by the reviewer at Stage
> 4/5** — it is deliberately NOT in the guide, because the implementing agent re-reads the guide on
> every turn and never fills these two sections.
>
> Consumers resolve each section **guide first, this file second** (`.claude/hooks/lib/guide_sections.py`):
> a legacy guide that still carries these sections inline keeps working unchanged, and a stray
> review file can never override an inline section.

---

<!-- Optional: the final report, only for a task run in auto mode (the user's `[auto]` tag,
`docs/claude-md/tracks.md` `## Auto mode`). To use it, copy the block below out of this comment, to this
place, and replace every <...>. Keep `Mode: auto` as its first line, exactly as written: T182's hook reads
it. Write it to this file before the run ends; the chat message is a copy, not the report. The same
block is the Supervisor's final chat message. It is not the `delivery-report` page and not
Evidence. A taste decision (what the user wants) also ends with the flag. Write `DEBATED` only when ≥2
Advocate `Agent` calls ran for that question, naming each Advocate's option. A decision with no Advocates is
labelled `RULE`, `FACT` or `SAFER OPTION`, never `DEBATED`. A decision flagged `⚠ decided for you` is a choice, and is never labelled `FACT`. A
safety action a rule requires (for example the backup before a delete) is `RULE` without the flag.
At Risk Medium or High, a `RULE:` counts only when it names a written rule (`path:line`,
`path § <heading>`, or `docs/claude-md/tracks.md` `### <section>`), and a `FACT:` needs a Citation
(`path:line "quoted text"`); without one it is a choice and must be `DEBATED`. Good: `2. backed up the CSV
— RULE: `docs/claude-md/tracks.md` `### Stops that stay``. Bad: `1. kept recurring.csv — RULE: Surgical Changes`.

## Auto decisions

Mode: auto
1. <what was decided> — RULE: <the rule>
2. <what was decided> — FACT: <path>:<line> "<quoted text>"
3. <what was decided> — DEBATED: <option> (Advocate 1: <its option>; Advocate 2: <its option>) ⚠ decided for you — please review
4. <what was decided> — SAFER OPTION: <why> ⚠ decided for you — please review
Paused: <only when a stop that stays paused the task: which one, and why>
Checks: tests `<command>` — <result>; reviews <skill — result>; real run `<command>` — printed `<what it printed>` (auto-checked, not /verify)
Not done: merge (yours); <auto verify: running (T182) | auto verify: <result> | /verify (yours)>

-->

## Evidence

| Check | Result | Notes / output snippet |
|-------|--------|------------------------|
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☑ pass | (implementer-supplied, Supervisor to confirm) `tests/test_t006_install.py`, 31 tests, written in this task. AC1 `DryRunTest.*`; AC2 `test_install_backs_up_first_then_adds_both_hooks`; AC3 `test_settings_dir_is_claude_config_dir_else_dot_claude`; AC4 `test_second_install_leaves_the_file_unchanged`; AC5 `test_other_keys_and_hooks_are_preserved`; AC6 `InvalidSettingsTest.*`; AC7 `test_uninstall_removes_only_our_entries_and_keeps_the_store`, `test_purge_prints_the_size_then_deletes_the_store`, `test_purge_refuses_unsafe_store_paths`; AC8 `test_install_then_uninstall_restores_the_original_json`; AC9 setUp guard (temp `CLAUDE_CONFIG_DIR`, `EASY_MEMORY_HOME`, `HOME`, patched `Path.home`) + `test_runs_as_a_script_with_the_temp_config_dir`. RED first: before `easy_memory.py` changed, `Ran 29 tests ... FAILED (errors=29)`. |
| Verification command run | ☑ pass | `python3 -m unittest discover -s tests -p 'test_t006*.py' -v` at 2026-10-28T05:48:00Z, env pinned to empty guard dirs (`CLAUDE_CONFIG_DIR`, `EASY_MEMORY_HOME`, `HOME`): 31 lines `... ok`, then `Ran 31 tests in 0.270s` / `OK`. Guard dirs untouched afterwards (`guard entries: 3`). |
| Negative cases hold | ☑ pass | invalid JSON and 4 unexpected shapes abort for install, `--dry-run` and uninstall: exit 1, file bytes and folder listing unchanged, no backup; missing config folder exits 1; a concurrent edit between read and write aborts and keeps the other edit; `--purge` refuses `/`, the home folder, a parent of it, `data`, `easy-memory-mcp` and a `.easy-memory-link` symlink to `data`, before any settings edit; purge does not run when settings are invalid. |
| verify | ☐ N/A (pending) | not run: the implementing agent has no Skill tool. Real run instead (temp dirs, see Demonstration AFTER): install, idempotent re-install, uninstall --purge, JSON-equal to original — pass for the real run; `/verify` still owed by Supervisor. |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☑ pass | self-review only (no Skill tool, so no `code-review` / `security-review` skill run yet): new install/uninstall section of `easy_memory.py`, the `_atomic_write` `mode=` parameter (default 0o600 = old behaviour, existing callers unchanged), `main()` flags, one-line skip change in `tests/test_t001_store.py`. Found and fixed: purge name check too loose (`easy-memory-mcp` passed), lost-update race, merged diff lines on a one-line file, backup name collision within one second. |
| Full smoke suite still green (no regression) | ☑ pass | `python3 -m unittest discover -s tests` (guard env): `Ran 209 tests in 5.620s` / `OK`; `[NFR-001] 7000 files, 20 runs: ... p95=0.067s`. `python3 -m py_compile easy_memory.py` ok. |
| **UI: Visual regression (diff or verdict pasted)** | ☐ N/A | pure backend CLI, no UI (PROJECT_SPEC: Frontend not used) |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ N/A | pure backend CLI, no UI |
| **UI: Responsiveness at target viewports** | ☐ N/A | pure backend CLI, no UI |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (captured by backend-developer at HEAD `bc5a509`, before any HUN-79 commit; temp
`CLAUDE_CONFIG_DIR` and `EASY_MEMORY_HOME` under the session scratchpad, fixture settings.json with
`model` and one other Stop hook):

```
2026-10-28T05:41:46Z
$ git rev-parse --short HEAD
bc5a509
$ CLAUDE_CONFIG_DIR=<tmp>/cfg EASY_MEMORY_HOME=<tmp>/store python3 easy_memory.py install --dry-run
usage: easy_memory [-h]
                   {hook-stop,hook-prompt,serve,report,install,uninstall,build-weights,switch} ...
easy_memory: error: unrecognized arguments: --dry-run
exit=2
$ ... python3 easy_memory.py install
easy-memory install: not implemented
exit=0
$ ... python3 easy_memory.py uninstall --purge
usage: easy_memory [-h]
                   {hook-stop,hook-prompt,serve,report,install,uninstall,build-weights,switch} ...
easy_memory: error: unrecognized arguments: --purge
exit=2
$ ls -A <tmp>/cfg
settings.json
```

**AFTER** (backend-developer at `dfc14b3`, same fixture; temp `CLAUDE_CONFIG_DIR`, `EASY_MEMORY_HOME`
and `HOME`; the store folder held one 3-byte note; `<tmp>` replaces the scratchpad path):

```
2026-10-28T05:47:44Z
$ git rev-parse --short HEAD
dfc14b3
$ CLAUDE_CONFIG_DIR=<tmp>/cfg EASY_MEMORY_HOME=<tmp>/.easy-memory python3 easy_memory.py install --dry-run
settings: <tmp>/cfg/settings.json
python: /usr/bin/python3
--- <tmp>/cfg/settings.json
+++ <tmp>/cfg/settings.json
@@ -1,6 +1,35 @@
 {
   "model": "opus",
   "hooks": {
-    "Stop": [{"hooks": [{"type": "command", "command": "echo other"}]}]
+    "Stop": [
+      {
+        "hooks": [
+          {
+            "type": "command",
+            "command": "echo other"
+          }
+        ]
+      },
+      {
+        "hooks": [
+          {
+            "type": "command",
+            "command": "/usr/bin/python3 /home/hungnguyenhuu/workspace/pets/hungnguyen111/easy-memory-mcp-wt-HUN-79/easy_memory.py hook-stop",
+            "timeout": 10
+          }
+        ]
+      }
+    ],
+    "UserPromptSubmit": [
+      {
+        "hooks": [
+          {
+            "type": "command",
+            "command": "/usr/bin/python3 /home/hungnguyenhuu/workspace/pets/hungnguyen111/easy-memory-mcp-wt-HUN-79/easy_memory.py hook-prompt",
+            "timeout": 5
+          }
+        ]
+      }
+    ]
   }
 }
dry run: nothing was written
exit=0
$ ls -A <tmp>/cfg
settings.json
$ ... python3 easy_memory.py install
settings: <tmp>/cfg/settings.json
python: /usr/bin/python3
backup: <tmp>/cfg/settings.json.easy-memory.bak.20261028T054744Z
installed: Stop and UserPromptSubmit hooks
exit=0
$ ... python3 easy_memory.py install   # second run
settings: <tmp>/cfg/settings.json
already installed; nothing was changed
exit=0
$ ... python3 easy_memory.py uninstall --purge
settings: <tmp>/cfg/settings.json
python: /usr/bin/python3
backup: <tmp>/cfg/settings.json.easy-memory.bak.20261028T054744Z-1
uninstalled: easy-memory hooks removed
store: <tmp>/.easy-memory holds 3 bytes
store: deleted <tmp>/.easy-memory
exit=0
$ python3 -c 'json-equal to original?'
True
$ ls -A <tmp>/cfg <tmp>
settings.json
settings.json.easy-memory.bak.20261028T054744Z
settings.json.easy-memory.bak.20261028T054744Z-1
cfg
original.json
```

Note: the fixture's one-line `"Stop": [...]` comes back JSON-equal but expanded (re-serialisation).
A file in Claude Code's own 2-space style comes back byte for byte (asserted in AC8 test).

**DELTA**: The user can now register both hooks for all repos with one `install` command (after
previewing the exact diff with `--dry-run`), and remove them again with `uninstall`; before, both
were stubs.

**WITNESS**: [Supervisor: derive from `memory/event-trace/HUN-79.jsonl`; not the implementing agent alone]
