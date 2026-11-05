# TASK_REVIEW — HUN-220: Release page speed charts

> Sibling of `tasks/TASK_GUIDE_HUN-220.md`. Everything here is **filled by the reviewer at Stage
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
| **New test(s) cover Acceptance Criteria (file paths pasted)** | ☐ pass / ☐ fail | [test file path(s) — required before Done] |
| Verification command run | ☐ pass / ☐ fail | [paste actual output] |
| Negative cases hold | ☐ pass / ☐ fail | |
| verify | ☐ pass / ☐ fail / ☐ N/A | [what was observed — must literally state "pass" or "fail" here too, e.g. "skill run, feature confirmed working — pass": the merge gate scans this Notes column for the word "pass", not just the Result column] |
| Review scope bounded to the change's blast radius (affected set, not whole repo) | ☐ pass / ☐ fail | [what was reviewed vs. skipped, and why] |
| Full smoke suite still green (no regression) | ☐ pass / ☐ fail | |
| **Companion score (easy-verifier)** | ☐ pass / ☐ fail / ☐ N/A | [`overall` and `change_risk` as the tool returned them, the scope, the ref, and the absolute path of the verifier report after a literal `report:` label — e.g. "overall 86 (>= 80), change_risk pass, scope changes, ref `main...HEAD`, report: `/home/me/.easy-verifier-reports/kit/score_changes_20261028T0530Z.html`". The gate reads the path that follows `report:` and nothing else, so with no label, or a path that is absent, the row is unscored — write ☑ N/A instead. ☑ N/A with a reason when neither companion tool was run: the merge gate blocks on ☑ fail only, never on an absent or N/A row] |
| **UI: Visual regression (diff or verdict pasted)** | ☐ pass / ☐ fail / ☐ N/A | [screenshot path or LLM verdict — required for UI tasks, Hard-Stop Gate 6] |
| **UI: Design-system compliance (tokens/colors/typography verified)** | ☐ pass / ☐ fail / ☐ N/A | [method used + output] |
| **UI: Responsiveness at target viewports** | ☐ pass / ☐ fail / ☐ N/A | [viewports tested, any overflow findings] |

---

## Demonstration

> Anchors what this task delivered to an observable before/after pair. BEFORE has no `N/A` path:
> if the task changes executable code, BEFORE is a pasted, timestamped terminal capture taken
> **before any implementation commit exists**; if it does not (docs, templates, skill-instruction
> text), BEFORE is the **verbatim prior content** of what changed — a quoted excerpt, not a command.

**BEFORE** (2026-11-05T11:30Z, before any implementation commit; HEAD `618f082`, branch `site-speed-charts`). Not executable code: verbatim prior content of `site/index.html` (lines 833-857, the Measured section, and the Known limits table and its first detail entry (the other detail entries are unchanged and not quoted), lines 859-888):

```html
<section id="numbers">
  <h2>Measured</h2>
  <p class="caption">p95 of each hook, against its limit.</p>
  <div class="chart">
    <div class="bar-row">
      <div class="bar-top"><span class="bar-name">Prompt hook</span><span class="bar-ctx">7,831-file repo, 200 notes</span><span class="bar-val">0.212 s <small>of 1 s</small></span></div>
      <div class="bar" role="img" aria-label="Prompt hook p95: 0.212 s of a 1 s limit"><span style="width:21.2%"></span></div>
    </div>
    <div class="bar-row">
      <div class="bar-top"><span class="bar-name">Stop hook</span><span class="bar-val">0.066 s <small>of 2 s</small></span></div>
      <div class="bar" role="img" aria-label="Stop hook p95: 0.066 s of a 2 s limit"><span style="width:3.3%"></span></div>
    </div>
  </div>
  <ul class="strip stats c3">
    <li><span class="num">0.024 s</span><span class="label">word weights load</span></li>
    <li><span class="num">1.69 MB</span><span class="label">word-weights file</span></li>
    <li><span class="num">307</span><span class="label">tests pass (3 skipped: opt-in or host-dependent)</span></li>
  </ul>
  <details class="more">
    <summary>More detail</summary>
    <div class="more-body">
      <p>An independent QA task checked the full cycle: install, save, index, MCP read, report, uninstall. It also checked file modes, no network traffic (a socket shim and <code>strace</code>), garbage input, and that the repo tree hash does not change.</p>
    </div>
  </details>
</section>
```

```html
<section id="limits">
  <h2>Known limits</h2>
  <div class="table-wrap" role="region" aria-label="Known limits" tabindex="0"><table>
    <thead><tr><th>Limit</th><th>Impact</th><th>Status</th></tr></thead>
    <tbody>
      <tr><td>Notes pile up</td><td>The hook gets about 1 ms slower per note.</td><td><span class="status">open</span></td></tr>
      <tr><td>Big transcripts</td><td>A 400 MB transcript used 808 MB.</td><td><span class="status">open</span></td></tr>
      <tr><td>Non-git folder</td><td>The weights build has no cap.</td><td><span class="status">open</span></td></tr>
      <tr><td>Clear text</td><td>Notes are saved unencrypted (mode 0600).</td><td><span class="status">accepted</span></td></tr>
      <tr><td>Permission prompt</td><td>The live check has not run.</td><td><span class="status">to run</span></td></tr>
    </tbody>
  </table></div>
  <details class="more">
    <summary>More detail</summary>
    <div class="more-body">
      <dl>
        <dt>Notes pile up</dt>
        <dd>The prompt hook gets about 1 ms slower per saved note. It passes the 1 s limit at roughly 1,000 to 3,000 notes. At about 5 s the hook timeout kills it and the index silently disappears.</dd>
```

Headless Chrome full-page screenshots of the page as it is now (not committed; `.screens/` is a scratch folder): `/home/hungnguyenhuu/workspace/pets/hungnguyen111/easy-memory-mcp-HUN-220/.screens/before-1280.png`, `.screens/before-375.png`.

**AFTER**: [same command, post-change] OR [verbatim excerpt of the new content]

**DELTA**: [one sentence — what a user can now do that they could not before]

**WITNESS**: [who ran it and when — derived from `memory/event-trace/HUN-220.jsonl`, never the
implementing agent alone]
