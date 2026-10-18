#!/usr/bin/env bash
# Isolation for /commit-chain: the chain works on one commit in its own worktree,
# so other work going on in the main folder never leaks in, and lands its
# documentation commit back without touching anything else staged there.
#
#   chain-worktree.sh create <sha>          print the path of a new worktree at <sha>
#   chain-worktree.sh land <base> <docs>    apply <docs> (made on top of <base>) to the
#                                           current branch, committing only its paths;
#                                           print the new commit, or park it on a branch
#                                           and exit 3 if those paths have local edits
#   chain-worktree.sh remove <path>         delete the worktree
set -euo pipefail

repo_root=$(git rev-parse --show-toplevel)
worktrees_dir="$repo_root/.chain-worktrees"
usage_exit_code=2
parked_exit_code=3
message_file=""   # script-level so the exit trap can still see it

create_worktree() {
  local sha=$1 path
  path="$worktrees_dir/$(git rev-parse --short "$sha")-$$"
  mkdir -p "$worktrees_dir"
  git worktree add --quiet --detach "$path" "$sha"
  echo "$path"
}

has_local_edits() {
  git -C "$repo_root" status --porcelain -- "$@" | grep -q .
}

park_on_branch_and_exit() {
  local base=$1 docs=$2 branch
  branch="docs-sync/$(git rev-parse --short "$base")"
  git branch --force "$branch" "$docs"
  echo "parked: $branch" >&2
  exit "$parked_exit_code"
}

land_docs_commit() {
  local base=$1 docs=$2 path paths=()
  while IFS= read -r path; do paths+=("$path"); done < <(git diff --name-only "$base" "$docs")
  [ "${#paths[@]}" -gt 0 ] || { echo "land: $docs changes nothing" >&2; exit "$usage_exit_code"; }
  has_local_edits "${paths[@]}" && park_on_branch_and_exit "$base" "$docs"
  message_file=$(mktemp "$worktrees_dir/message.XXXXXX")
  trap 'rm -f "$message_file"' EXIT
  git log -1 --format=%B "$docs" > "$message_file"
  git -C "$repo_root" diff --binary "$base" "$docs" | git -C "$repo_root" apply
  # New files must be known to git before a path-limited commit will take them.
  git -C "$repo_root" add --intent-to-add -- "${paths[@]}"
  git -C "$repo_root" commit --quiet --only --file "$message_file" -- "${paths[@]}"
  git -C "$repo_root" rev-parse --short HEAD
}

remove_worktree() {
  git worktree remove --force "$1"
}

case "${1:-}" in
  create) create_worktree "$2" ;;
  land)   land_docs_commit "$2" "$3" ;;
  remove) remove_worktree "$2" ;;
  *) echo "usage: chain-worktree.sh create <sha> | land <base> <docs> | remove <path>" >&2; exit "$usage_exit_code" ;;
esac
