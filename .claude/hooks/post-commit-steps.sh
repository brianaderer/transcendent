#!/usr/bin/env bash
# Print the skills to run after a commit, one per line, in order:
#   uncle-bob        when source code or tests changed (review first, so a fix
#                    commit it prompts is documented once, not twice)
#   document-commit  for every commit that isn't skippable
# Prints nothing for a skippable commit. Shared by both commit hooks.
set -euo pipefail
sha="${1:-HEAD}"
hooks=$(dirname "$0")

"$hooks/changed-files.sh" "$sha" >/dev/null   # exit 2 here on an unknown commit

if "$hooks/is-skippable-commit.sh" "$sha"; then
  exit 0
fi
if "$hooks/has-source-changes.sh" "$sha"; then
  echo uncle-bob
fi
echo document-commit
