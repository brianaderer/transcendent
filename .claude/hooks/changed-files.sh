#!/usr/bin/env bash
# Print the paths a commit changed, one per line.
# Exit 2 with a message when the commit doesn't exist, so callers never mistake
# an error for an answer.
set -euo pipefail
sha="${1:-HEAD}"

if ! git rev-parse --verify --quiet "$sha^{commit}" >/dev/null; then
  echo "changed-files: no such commit: $sha" >&2
  exit 2
fi
git diff-tree --no-commit-id --name-only -r --root "$sha"
