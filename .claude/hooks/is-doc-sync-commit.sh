#!/usr/bin/env bash
# Exit 0 when the given commit must NOT trigger /document-commit:
#   - it carries the Docs-Sync trailer (the agent's own output), or
#   - it changes nothing outside docs/ and README.md (pure documentation).
# Exit 1 when the commit should be documented.
# This is the single loop guard shared by every hook and by the skill.
set -euo pipefail
sha="${1:-HEAD}"

if git log -1 --format='%(trailers:key=Docs-Sync,valueonly)' "$sha" | grep -q .; then
  exit 0
fi

code_files=$(git diff-tree --no-commit-id --name-only -r --root "$sha" \
  | grep -v -E '^(docs/|README\.md$)' || true)
[ -z "$code_files" ] && exit 0
exit 1
