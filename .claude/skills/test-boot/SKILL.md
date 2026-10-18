---
name: test-boot
description: Tests the README's boot steps the way a reviewer will — a fresh clone in an empty folder, every install and run step followed exactly, then the demo itself — and reports success or every friction point with the fix for each. Takes an optional commit or branch (default HEAD) and "github" to clone from GitHub instead of the local repo. Use before calling any boot-affecting work finished, after /document-commit reports boot steps changed, and before submitting.
argument-hint: "[ref] [github]"
---

# /test-boot

Arguments: `$ARGUMENTS`

## 1. Work out what to test

- **Ref:** the first argument that isn't `github`; if none, `HEAD`. Resolve it to a
  commit hash with `git rev-parse --verify '<ref>^{commit}'`. If git rejects it, say so
  in a sentence and stop.
- **Source:** the local repo, unless `github` was given. GitHub only contains what has
  been pushed, and while the repo is private, a clone needs this machine's GitHub
  login, which a reviewer wouldn't have. Say so in the report if you clone from GitHub.
- **Uncommitted changes are not tested.** If `git status --porcelain` shows any,
  say that the test covers the commit, not the working folder.

## 2. Make sure the test folder is ignored

`.boot-test/` must be listed in `.gitignore`. If it isn't, stop and report that.
Never commit a boot-test folder.

## 3. Hand off to the agent

Launch the **`test-boot`** subagent (Agent tool, `subagent_type: "test-boot"`) with the
commit hash, the source, and a note of any uncommitted changes. Wait for it to finish.

## 4. Relay

Relay the agent's report to Brian in plain prose: success or the failing step first,
then the friction points with their fixes. Don't apply the fixes yourself as part of
this skill — they are code or README changes, made in a normal commit (which then
goes through `/document-commit`).
