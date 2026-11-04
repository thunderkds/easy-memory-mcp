# PROJECT_KANBAN.md
**Last updated**: 2026-11-04

> Board cache, pulled from the board by `python3 scripts/board_sync.py pull`. Do not edit it by hand:
> the board is the source of truth, and the next pull overwrites this file.

---

## Board

### Todo
- [ ] **HUN-137** — Event turns borrow the last typed prompt as the note question | backend-developer | C2 | Risk: Medium | P1 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-137.md`
- [ ] **HUN-138** — A note cites only files its answer names and its turn touched | backend-developer | C2 | Risk: Medium | P2 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-138.md`
- [ ] **HUN-139** — A file missing on this branch is flagged NOT-ON-BRANCH, not DELETED | backend-developer | C2 | Risk: Medium | P2 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-139.md`
- [ ] **HUN-140** — Ranking adjusts for note length and needs one rare prompt word | backend-developer | C2 | Risk: Medium | P2 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-140.md`

### In Progress
- [ ] **HUN-204** — Site: Easy Kit link to easy-kits.vercel.app; problem/solution + flow + token chart; Easy Personal memory section; drop release notes | ? | ? | Risk: ? | P2 | Guide: `tasks/TASK_GUIDE_HUN-204.md`

### Ready for Review

### Done
- [x] **HUN-74** — Package skeleton, repo key and atomic note store | common-infrastructure | C1 | Risk: Low | P0 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-74.md`
- [x] **HUN-75** — Stop hook saves one note per turn | backend-developer | C2 | Risk: Medium | P0 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-75.md`
- [x] **HUN-76** — Word weights built in the background, with a parity check | backend-developer | C2 | Risk: Medium | P0 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-76.md`
- [x] **HUN-77** — Prompt hook injects the index | backend-developer | C2 | Risk: High | P0 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-77.md`
- [x] **HUN-78** — Per-repo on/off/auto switch and prompt log | backend-developer | C1 | Risk: Low | P1 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-78.md`
- [x] **HUN-79** — Install and uninstall into user-level Claude Code settings | backend-developer | C2 | Risk: High | P1 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-79.md`
- [x] **HUN-80** — Report: memory on vs off from Claude session logs | backend-developer | C2 | Risk: Medium | P1 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-80.md`
- [x] **HUN-81** — MCP server with search, read, list and forget | backend-developer | C2 | Risk: Medium | P1 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-81.md`
- [x] **HUN-82** — End-to-end smoke and NFR checks | qa-expert | C2 | Risk: Medium | P1 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-82.md`
- [x] **HUN-84** — Hook-prompt tests pass on any day | backend-developer | C1 | Risk: Low | P0 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-84.md`
- [x] **HUN-85** — Stop hook redacts secrets before a note is saved | backend-developer | C2 | Risk: High | P0 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-85.md`
- [x] **HUN-86** — redact command rewrites notes already saved | backend-developer | C2 | Risk: High | P0 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-86.md`
- [x] **HUN-87** — Gate 0 pass check before the redaction release | qa-expert | C1 | Risk: Medium | P0 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-87.md`
- [x] **HUN-122** — Report compares only auto-switch sessions | backend-developer | C1 | Risk: Medium | P0 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-122.md`
- [x] **HUN-123** — Release page restyled as a dark indigo dashboard | frontend-developer | C1 | Risk: Low | P2 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-123.md`
- [x] **HUN-125** — Release page in the Graphite Mint family theme | frontend-developer | C2 | Risk: Low | P1 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-125.md`
- [x] **HUN-127** — Release page — centred container, visual guide, highlight-only release notes | frontend-developer | C2 | Risk: Low | P1 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-127.md`
- [x] **HUN-130** — Release page — Graphite Mint neon highlight layer | frontend-developer | C2 | Risk: Low | P1 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-130.md`
- [x] **HUN-133** — Install stepper — equal code boxes across the three steps | frontend-developer | C1 | Risk: Low | P2 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-133.md`
- [x] **HUN-134** — easy-memory installs as a Claude Code plugin (hooks + MCP server, no clone, no settings edit) | backend-developer | C2 | Risk: Medium | P1 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-134.md`
- [x] **HUN-135** — memory_forget moves a note to the trash; memory_restore brings it back | backend-developer | C2 | Risk: High | P1 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-135.md`
- [x] **HUN-136** — A saved note is found by memory_search within 1 s of the Stop hook | qa-expert | C1 | Risk: Low | P2 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-136.md`
- [x] **HUN-197** — report --json writes report.json for the easy-personal dashboard | backend-developer | C2 | Risk: Medium | P1 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-197.md`
- [x] **HUN-199** — report --json with a wrong --repo must not create a store folder | ? | ? | Risk: ? | P2 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-199.md`
- [x] **HUN-208** — Prompt hook splits each word once per run, with the same ranking | backend-developer | C2 | Risk: Medium | P1 | @hungnh1110 | Guide: `tasks/TASK_GUIDE_HUN-208.md`

### Closed (will not do)

## Blocked

---

## Stage Tracker
