#!/usr/bin/env bash
# Exit 0 when the commit must NOT trigger the post-commit steps:
#   - it carries the Docs-Sync trailer (the documentation agent's own output —
#     reacting to it would loop forever), or
#   - it changes nothing outside docs/ and README.md.
# Exit 1 when the commit should be processed; exit 2 on error.
# This is the single loop guard shared by both hooks and every post-commit skill.
set -euo pipefail
sha="${1:-HEAD}"

changed_files=$("$(dirname "$0")/changed-files.sh" "$sha")

if git log -1 --format='%(trailers:key=Docs-Sync,valueonly)' "$sha" | grep -q .; then
  exit 0
fi

non_doc_files=$(grep -v -E '^(docs/|README\.md$)' <<<"$changed_files" || true)
[ -z "$non_doc_files" ]
