#!/usr/bin/env bash
# Print the paths a commit changed, one per line. A merge commit is compared with
# its first parent — the branch it was merged into — since diff-tree alone prints
# nothing for a merge.
# Exit 2 with a message when the commit doesn't exist, so callers never mistake
# an error for an answer.
set -euo pipefail
sha="${1:-HEAD}"

if ! git rev-parse --verify --quiet "$sha^{commit}" >/dev/null; then
  echo "changed-files: no such commit: $sha" >&2
  exit 2
fi
parent_count=$(git rev-list --parents -n 1 "$sha" | wc -w)
if [ "$parent_count" -gt 2 ]; then
  git diff --name-only "$sha^1" "$sha"
else
  git diff-tree --no-commit-id --name-only -r --root "$sha"
fi
