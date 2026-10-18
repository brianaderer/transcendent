#!/usr/bin/env bash
# Exit 0 when the given commit changes source code or tests (worth a Clean Code
# review); exit 1 when it only touches markdown, config, data, or lockfiles.
set -euo pipefail
sha="${1:-HEAD}"
source_pattern='\.(py|ts|tsx|js|jsx|mjs|cjs|go|rs|java|kt|rb|sql|sh)$|(^|/)\.githooks/'
git diff-tree --no-commit-id --name-only -r --root "$sha" \
  | grep -E "$source_pattern" | grep -q .
