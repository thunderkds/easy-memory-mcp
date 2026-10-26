#!/usr/bin/env bash
# Simulate code changing after session A: rename the moderation decision
# method. appeals.service.ts keeps its own, unrelated makeDecision (a decoy).
set -euo pipefail
cd "$(dirname "$0")/repo_A_M/src/moderation"
sed -i 's/\bmakeDecision\b/decideModeration/g' \
  moderation.service.ts moderation.controller.ts \
  moderation.service.spec.ts moderation.controller.spec.ts
grep -rn "makeDecision\|decideModeration" . ../appeals | sed 's/^/  /'
