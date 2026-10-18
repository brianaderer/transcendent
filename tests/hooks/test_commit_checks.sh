#!/usr/bin/env bash
# Offline tests for the commit-hook decision scripts in .claude/hooks/.
# Each test group builds one throwaway git repo and adds commits to it; each check
# looks only at the newest commit.
# Run: tests/hooks/test_commit_checks.sh
set -uo pipefail

REPO_ROOT=$(cd "$(dirname "$0")/../.." && pwd)
HOOKS="$REPO_ROOT/.claude/hooks"
SCRATCH_ROOT="$REPO_ROOT/.test-tmp"
failures=0

new_repo() {
  mkdir -p "$SCRATCH_ROOT"
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
  git -C "$dir" add -A
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

test_post_commit_steps() {
  local repo
  repo=$(new_repo); commit_files "$repo" "code" src/a.py
  expect_output "uncle-bob document-commit" "a code commit is reviewed, then documented" in_repo "$repo" "$HOOKS/post-commit-steps.sh" HEAD
  commit_files "$repo" "config" config/foo.json
  expect_output "document-commit" "a config-only commit is documented, not reviewed" in_repo "$repo" "$HOOKS/post-commit-steps.sh" HEAD
  commit_files "$repo" "docs" docs/a.md
  expect_output "" "a docs-only commit needs no steps" in_repo "$repo" "$HOOKS/post-commit-steps.sh" HEAD
  git -C "$repo" checkout -q -b feature
  commit_files "$repo" "feature" src/feature.py
  git -C "$repo" checkout -q -
  git -C "$repo" merge -q --no-ff feature -m "merge feature"
  expect_output "uncle-bob document-commit" "a merge commit that brings in a .py file is reviewed, then documented" in_repo "$repo" "$HOOKS/post-commit-steps.sh" HEAD
  expect_exit 2 "an unknown commit is an error, not a list of steps" in_repo "$repo" "$HOOKS/post-commit-steps.sh" deadbeef
}

test_has_source_changes
test_is_skippable_commit
test_post_commit_steps
rm -rf "$SCRATCH_ROOT"

if [ "$failures" -gt 0 ]; then
  echo "$failures test(s) failed"; exit 1
fi
echo "all tests passed"
