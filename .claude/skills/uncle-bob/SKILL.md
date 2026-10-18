---
name: uncle-bob
description: Clean Code review (Robert C. Martin) of the source code changed by a commit or range — names, function size and arguments, comments, error handling, duplication, levels of abstraction, tests — with ranked findings and a concrete fix for each. Takes a commit, a range (from..to), or nothing (HEAD). Runs automatically inside /commit-chain after every commit; run it by hand on any range.
argument-hint: "[commit | from..to]"
---

# /uncle-bob

**This is the by-hand version, for reviewing any commit or range.** After every
commit, the hooks run `/commit-chain`, which runs this review automatically on the
commit and its documentation commit.

Argument: `$ARGUMENTS` (empty means `HEAD`).

## 1. Resolve the commits

Use the argument above as `<arg>`; if it is empty, use `HEAD`.

```bash
git rev-list --reverse <arg>                 # when <arg> is a range (contains "..")
git rev-parse --verify '<arg>^{commit}'      # when <arg> is a single commit
```

If git rejects the argument, say so in a sentence and stop.

## 2. Drop commits with nothing to review

For each commit:
- `.claude/hooks/is-skippable-commit.sh <sha>` exits 0 → skip it (a documentation-sync
  commit, or documentation only).
- `.claude/hooks/has-source-changes.sh <sha>` exits 1 → skip it (no source code or
  tests changed — only markdown, config, or data).

If nothing is left, say "nothing to review in <range>" and stop.

## 3. Hand off to the agent

Launch the **`uncle-bob`** subagent (Agent tool, `subagent_type: "uncle-bob"`) with the
range as given and the remaining commits, oldest first, with subject lines. Wait for it.

## 4. Act on the findings

Relay the review to Brian in plain prose. Then, inside a Claude Code session:
- **Must fix** findings are fixed now, in a normal commit (tests first where behavior
  is touched), before any new work. That commit is reviewed again by the hook.
- **Should fix** findings are fixed in the same commit when they're in the code you're
  already touching; otherwise list them in the relay.
- **Consider** findings are only reported.
- **Stop after two rounds.** If the same finding comes back after a fix, don't loop:
  report it to Brian with both versions and why the fix didn't satisfy the review.
