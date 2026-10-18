---
name: commit-chain
description: The post-commit chain, run automatically on every commit by the repo's hooks. In an isolated worktree at the commit, documents only that commit's diff and commits the documentation, lands that documentation commit on the current branch without touching other work, then runs a Clean Code review on exactly the two commits — the original and its documentation commit. Takes one commit (default HEAD).
argument-hint: "[commit]"
---

# /commit-chain

Argument: `$ARGUMENTS` (empty means `HEAD`). Call it `<sha>` below, resolved with
`git rev-parse --short --verify '<arg>^{commit}'`. If git rejects it, say so and stop.

**Why it's built this way.** Other work may be going on in the main folder at the same
time: uncommitted edits, staged files, newer commits. The chain must see only the
commit it was started for, and it must not spend model calls on anything else. So:
it runs in its own worktree at `<sha>`, the documentation agent works only from that
commit's diff, and the review looks only at the two commits the chain is about.

## 1. Skip what must not be processed — the loop guard

```bash
.claude/hooks/is-skippable-commit.sh <sha>
```

Exit 0 → stop: it's a documentation-sync commit (processing it would loop forever) or
it only touches `docs/` and `README.md`. Say "nothing to do for <sha>".

## 2. Open the isolated worktree

```bash
WT=$(.claude/hooks/chain-worktree.sh create <sha>)
```

## 3. Document the diff

Launch the **`document-commit`** subagent with:
- **worktree:** `$WT` — it works and commits only there;
- **range:** `<sha>` and that one commit's subject line.

Wait for it. Read its report: whether it committed (the documentation commit `<docs>`),
and whether **Boot steps changed**.

## 4. Land the documentation commit

Only if the agent committed:

```bash
.claude/hooks/chain-worktree.sh land <sha> <docs>
```

- Prints the landed commit → it is now on the current branch, containing only the
  documentation files, with the `Docs-Sync` trailer kept. Anything else staged or
  edited in the main folder is untouched.
- Exit 3 → someone has local edits to those same documentation files, so it was
  parked on the branch `docs-sync/<sha>` instead. Say so plainly; Brian merges it once
  his edits are committed.

## 5. Review the two commits

Run the review if either commit changes source code or tests (the documentation
commit can, when it corrects a comment or docstring):

```bash
.claude/hooks/has-source-changes.sh <sha>; .claude/hooks/has-source-changes.sh <docs>
```

Launch the **`uncle-bob`** subagent with:
- **worktree:** `$WT` (it now holds `<sha>` plus the documentation commit);
- **commits:** `<sha>` and `<docs>` (or just `<sha>` if no documentation commit was
  made).

If neither commit changes source, skip the review and say so.

## 6. Close the worktree

```bash
.claude/hooks/chain-worktree.sh remove "$WT"
```

## 7. Boot check

If step 3 reported **Boot steps changed: yes**, run `/test-boot` on the current HEAD.

## 8. Relay and act

Relay both reports to Brian in plain prose (`CLAUDE.md` §1): what was documented, the
landed commit (or where it was parked), and the review's findings. Never push.

Then, inside a Claude Code session:
- **Must fix** findings are fixed now, in a normal commit (tests first where behavior
  is touched). That commit runs the chain again.
- **Should fix** findings are fixed in that same commit when they're in code it
  touches; otherwise listed.
- **Consider** findings are only reported.
- **Stop after two rounds.** If the same finding comes back after a fix, don't loop:
  report it to Brian with both versions and why the fix didn't satisfy the review.
