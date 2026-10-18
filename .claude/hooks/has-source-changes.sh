#!/usr/bin/env bash
# Exit 0 when the commit changes source code or tests (worth a Clean Code review);
# exit 1 when it only touches markdown, config, data, or lockfiles; exit 2 on error.
set -euo pipefail
sha="${1:-HEAD}"

source_extensions='\.(py|ts|tsx|js|jsx|mjs|cjs|go|rs|java|kt|rb|sql|sh)$'
# Git hook scripts have no extension, so the folder itself marks them as source.
extensionless_hook_dir='(^|/)\.githooks/'

changed_files=$("$(dirname "$0")/changed-files.sh" "$sha")
grep -qE "$source_extensions|$extensionless_hook_dir" <<<"$changed_files"
