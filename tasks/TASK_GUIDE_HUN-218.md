**Date**: 2026-11-04
**Complexity Level**: C1
**Risk Level**: Low
**Priority**: P2
**Assigned agent**: Supervisor (minimal track)
**Agent guide**: `docs/claude-md/tracks.md`

## Requirement

User 2026-11-04 asked to replace the two legacy test-repo names "in the coding" with symbols such as Project A / Project B. Before this task, 119 lines in 35 tracked files named them, plus their parent client/org folders in two paths.

**Restated intent**: In every tracked text file, the first test repo becomes `project-a` (prose: Project A) and the second `project-b` (prose: Project B); Python names become `project_a` / `project_b`, upper-case constants `PROJECT_A` / `PROJECT_B`; the two hard-coded checkout paths in `experiments/02-auto-memory/harness.py` become env vars `EASY_MEMORY_PROJECT_A` / `EASY_MEMORY_PROJECT_B` with no client/org folder names. Git history is not rewritten.

## Acceptance Criteria

| \# | Criterion | Traces to |
| -- | -- | -- |
| 1 | `tests/test_no_legacy_names.py`: no tracked text file names a legacy project or its parent folders (the names are built from pieces inside the test) | request |
| 2 | Full suite passes; experiment scripts still import (`python3 -m py_compile` on each changed `.py`) | no breakage |
| 3 | `plugin/easy_memory.py` byte-identical to `easy_memory.py` | release rule |

### Verification Command

```bash
python3 -m unittest tests.test_no_legacy_names && python3 -m unittest discover -s tests
```