#!/usr/bin/env bash
# Claude Code PostToolUse hook (matcher: Bash).
# After a successful `git commit` made inside a Claude Code session, tells Claude
# to run /document-commit on the new commit. Skips the agent's own commits.
set -euo pipefail
input=$(cat)
command=$(jq -r '.tool_input.command // ""' <<<"$input")

[[ "$command" =~ git([[:space:]]+-C[[:space:]]+[^[:space:]]+)?[[:space:]]+commit ]] || exit 0

cd "$(jq -r '.cwd // "."' <<<"$input")"
repo=$(git rev-parse --show-toplevel 2>/dev/null) || exit 0
cd "$repo"
sha=$(git rev-parse --short HEAD 2>/dev/null) || exit 0

# Only react to a commit that was made in the last minute (the command may have failed).
[ $(( $(date +%s) - $(git log -1 --format=%ct HEAD) )) -le 60 ] || exit 0

"$repo/.claude/hooks/is-doc-sync-commit.sh" "$sha" && exit 0

jq -n --arg sha "$sha" '{
  hookSpecificOutput: {
    hookEventName: "PostToolUse",
    additionalContext: ("Commit " + $sha + " was just made. Per CLAUDE.md §6, run /document-commit " + $sha + " now, before any further code changes.")
  }
}'
