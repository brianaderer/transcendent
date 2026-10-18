#!/usr/bin/env bash
# Claude Code PostToolUse hook (matcher: Bash).
# After a successful `git commit` inside a Claude Code session, tells Claude to run
# /commit-chain on it. Silent for skippable commits and for anything else.
set -euo pipefail

fresh_commit_max_age_seconds=60   # older HEAD means the commit command failed

is_git_commit_command() {
  [[ "$1" =~ git([[:space:]]+-C[[:space:]]+[^[:space:]]+)?[[:space:]]+commit ]]
}

head_commit_is_fresh() {
  local committed_at
  committed_at=$(git log -1 --format=%ct HEAD)
  [ $(( $(date +%s) - committed_at )) -le "$fresh_commit_max_age_seconds" ]
}

instructions_for() {
  local sha=$1
  jq -n --arg text "Commit $sha was just made. Per CLAUDE.md §6, run /commit-chain $sha now, before any further code changes." \
    '{hookSpecificOutput: {hookEventName: "PostToolUse", additionalContext: $text}}'
}

input=$(cat)
is_git_commit_command "$(jq -r '.tool_input.command // ""' <<<"$input")" || exit 0
cd "$(jq -r '.cwd // "."' <<<"$input")"
cd "$(git rev-parse --show-toplevel 2>/dev/null)" || exit 0
head_commit_is_fresh || exit 0

sha=$(git rev-parse --short HEAD)
.claude/hooks/is-skippable-commit.sh "$sha" && exit 0
instructions_for "$sha"
