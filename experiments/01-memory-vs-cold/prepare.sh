#!/usr/bin/env bash
# Make the four read-only copies of the repo under test that harness.py expects.
# Usage: ./prepare.sh /path/to/tapchat-apis
set -euo pipefail
src="${1:?usage: prepare.sh /path/to/tapchat-apis}"
cd "$(dirname "$0")"
for d in repo_clean repo_A_M repo_A_D repo_A_P; do
  rsync -a --exclude node_modules --exclude dist --exclude coverage \
    --exclude reports --exclude .git "$src/" "$d/"
done
