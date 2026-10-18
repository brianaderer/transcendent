#!/usr/bin/env bash
# Offline tests for the commit-hook scripts in .claude/hooks/: the decision checks
# and the /commit-chain worktree landing.
# Each test group builds one throwaway git repo and adds commits to it; each check
# mostly looks at the newest commit.
# Run: tests/hooks/test_commit_checks.sh
set -uo pipefail

REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
HOOKS="$REPO_ROOT/.claude/hooks"
mkdir -p "$REPO_ROOT/.test-tmp"
SCRATCH_ROOT=$(mktemp -d "$REPO_ROOT/.test-tmp/run.XXXXXX")
trap 'rm -rf "$SCRATCH_ROOT"' EXIT
failures=0

new_repo() {
  local dir
  dir=$(mktemp -d "$SCRATCH_ROOT/repo.XXXXXX")
  git -C "$dir" init -q
  git -C "$dir" config user.email test@example.com
  git -C "$dir" config user.name test
  echo "$dir"
}

commit_files() {
  local dir=$1 message=$2; shift 2
  local path
  for path in "$@"; do
    mkdir -p "$dir/$(dirname "$path")"
    echo "$RANDOM" >> "$dir/$path"
  done
  git -C "$dir" add -- "$@"
  git -C "$dir" commit -q -m "$message"
}

expect_exit() {
  local expected=$1 description=$2; shift 2
  "$@" >/dev/null 2>&1
  local actual=$?
  if [ "$actual" -eq "$expected" ]; then
    echo "ok   - $description"
  else
    echo "FAIL - $description (expected exit $expected, got $actual)"
    failures=$((failures + 1))
  fi
}

expect_output() {
  local expected=$1 description=$2; shift 2
  local raw actual status
  raw=$("$@" 2>/dev/null); status=$?
  actual=$(tr '\n' ' ' <<<"$raw" | sed 's/ $//')
  if [ "$status" -eq 0 ] && [ "$actual" = "$expected" ]; then
    echo "ok   - $description"
  else
    echo "FAIL - $description (expected '$expected' and exit 0, got '$actual' and exit $status)"
    failures=$((failures + 1))
  fi
}

in_repo() { (cd "$1" && shift && "$@"); }

test_has_source_changes() {
  local repo
  repo=$(new_repo); commit_files "$repo" "first" setup.sh
  expect_exit 0 "first commit with a .sh file has source changes" in_repo "$repo" "$HOOKS/has-source-changes.sh" HEAD
  commit_files "$repo" "readme" README.md
  expect_exit 1 "README-only commit has no source changes" in_repo "$repo" "$HOOKS/has-source-changes.sh" HEAD
  commit_files "$repo" "json" config/foo.json
  expect_exit 1 "JSON-only commit has no source changes" in_repo "$repo" "$HOOKS/has-source-changes.sh" HEAD
  commit_files "$repo" "python" src/a.py
  expect_exit 0 "commit adding a .py file has source changes" in_repo "$repo" "$HOOKS/has-source-changes.sh" HEAD
  commit_files "$repo" "hook" .githooks/post-commit
  expect_exit 0 "commit touching an extensionless git hook has source changes" in_repo "$repo" "$HOOKS/has-source-changes.sh" HEAD
  local many=() i
  for i in $(seq 1 2000); do many+=("src/bulk/f$i.py"); done
  commit_files "$repo" "bulk" "${many[@]}"
  expect_exit 0 "commit adding 2,000 .py files has source changes" in_repo "$repo" "$HOOKS/has-source-changes.sh" HEAD
  expect_exit 2 "an unknown commit is an error, not a 'no'" in_repo "$repo" "$HOOKS/has-source-changes.sh" deadbeef
}

test_is_skippable_commit() {
  local repo
  repo=$(new_repo); commit_files "$repo" "code" src/a.py
  expect_exit 1 "a code commit is not skippable" in_repo "$repo" "$HOOKS/is-skippable-commit.sh" HEAD
  commit_files "$repo" "docs" docs/a.md README.md
  expect_exit 0 "a docs-and-README-only commit is skippable" in_repo "$repo" "$HOOKS/is-skippable-commit.sh" HEAD
  echo change >> "$repo/src/a.py"; git -C "$repo" add -A
  git -C "$repo" commit -q -m "docs: sync" -m "Docs-Sync: abc"
  expect_exit 0 "a commit with the Docs-Sync trailer is skippable even if it touches code" in_repo "$repo" "$HOOKS/is-skippable-commit.sh" HEAD
  expect_exit 2 "an unknown commit is an error, not a 'skip'" in_repo "$repo" "$HOOKS/is-skippable-commit.sh" deadbeef
}

test_changed_files() {
  local repo
  repo=$(new_repo); commit_files "$repo" "base" README.md
  git -C "$repo" checkout -q -b feature
  commit_files "$repo" "feature" src/feature.py
  git -C "$repo" checkout -q -
  commit_files "$repo" "main moves on" docs/main.md
  git -C "$repo" merge -q --no-ff feature -m "merge feature"
  expect_output "src/feature.py" "a merge lists only what the merged branch brought in" in_repo "$repo" "$HOOKS/changed-files.sh" HEAD
}

# Make a documentation commit for <base> in a fresh chain worktree. Echoes
# "<worktree> <docs sha>". <doc file> is edited if it exists, created if not.
make_docs_commit_on() {
  local repo=$1 base=$2 doc_file=$3 worktree
  worktree=$(in_repo "$repo" "$HOOKS/chain-worktree.sh" create "$base")
  mkdir -p "$worktree/$(dirname "$doc_file")"
  echo "documented" >> "$worktree/$doc_file"
  git -C "$worktree" add -- "$doc_file"
  git -C "$worktree" commit -q -m "docs: sync" -m "Docs-Sync: $base"
  echo "$worktree $(git -C "$worktree" rev-parse HEAD)"
}

test_chain_worktree_lands_docs_without_touching_other_work() {
  local repo base worktree docs
  repo=$(new_repo); commit_files "$repo" "code" src/a.py docs/a.md
  base=$(git -C "$repo" rev-parse HEAD)
  read -r worktree docs <<<"$(make_docs_commit_on "$repo" "$base" docs/a.md)"
  commit_files "$repo" "other work" src/b.py
  echo "staged" >> "$repo/src/a.py"; git -C "$repo" add src/a.py
  expect_exit 0 "landing the docs commit succeeds with other work staged" in_repo "$repo" "$HOOKS/chain-worktree.sh" land "$base" "$docs"
  expect_output "docs/a.md" "the landed commit contains only the docs" git -C "$repo" show --name-only --format= HEAD
  expect_exit 0 "the landed commit keeps the Docs-Sync trailer" in_repo "$repo" "$HOOKS/is-skippable-commit.sh" HEAD
  expect_output "M  src/a.py" "the other staged work is still staged" git -C "$repo" status --porcelain -- src
  in_repo "$repo" "$HOOKS/chain-worktree.sh" remove "$worktree"
}

test_chain_worktree_lands_a_docs_commit_that_adds_a_file() {
  local repo base worktree docs
  repo=$(new_repo); commit_files "$repo" "code" src/a.py
  base=$(git -C "$repo" rev-parse HEAD)
  read -r worktree docs <<<"$(make_docs_commit_on "$repo" "$base" docs/new-module.md)"
  expect_exit 0 "landing a docs commit that creates a file succeeds" in_repo "$repo" "$HOOKS/chain-worktree.sh" land "$base" "$docs"
  expect_output "docs/new-module.md" "the landed commit contains the new file" git -C "$repo" show --name-only --format= HEAD
  expect_output "" "nothing is left behind untracked" git -C "$repo" status --porcelain -- docs
  in_repo "$repo" "$HOOKS/chain-worktree.sh" remove "$worktree"
}

test_chain_worktree_parks_docs_when_their_files_have_local_edits() {
  local repo base worktree docs
  repo=$(new_repo); commit_files "$repo" "code" src/a.py docs/a.md
  base=$(git -C "$repo" rev-parse HEAD)
  read -r worktree docs <<<"$(make_docs_commit_on "$repo" "$base" docs/a.md)"
  echo "someone else is editing" >> "$repo/docs/a.md"
  expect_exit 3 "landing is refused when the docs' files have local edits" in_repo "$repo" "$HOOKS/chain-worktree.sh" land "$base" "$docs"
  expect_exit 0 "the docs commit is parked on a branch" git -C "$repo" rev-parse --verify "docs-sync/$(git -C "$repo" rev-parse --short "$base")"
  in_repo "$repo" "$HOOKS/chain-worktree.sh" remove "$worktree"
}

test_has_source_changes
test_is_skippable_commit
test_changed_files
test_chain_worktree_lands_docs_without_touching_other_work
test_chain_worktree_lands_a_docs_commit_that_adds_a_file
test_chain_worktree_parks_docs_when_their_files_have_local_edits

if [ "$failures" -gt 0 ]; then
  echo "$failures test(s) failed"; exit 1
fi
echo "all tests passed"
