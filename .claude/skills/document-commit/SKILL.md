---
name: document-commit
description: Documents a commit or a range of commits, then traces every file, doc, and cross-reference the change reaches and updates those too, repeating until nothing reachable is stale. Produces one documentation commit marked with a Docs-Sync trailer so it never triggers itself. Takes a commit (abc123), a range (abc123..def456), or nothing (HEAD). Called automatically after every commit by the repo's hooks; also run it by hand on any range.
argument-hint: "[commit | from..to]"
---

# /document-commit

Argument: `$ARGUMENTS` (empty means `HEAD`).

## 1. Resolve the commits

Use the argument above as `<arg>`; if it is empty, use `HEAD`.

```bash
git rev-list --reverse <arg>                 # when <arg> is a range (contains "..")
git rev-parse --verify '<arg>^{commit}'      # when <arg> is a single commit
```

If git rejects the argument, report that in a sentence and stop.

## 2. Drop commits that must not be documented — the loop guard

For each commit, run:

```bash
.claude/hooks/is-doc-sync-commit.sh <sha>
```

Exit code 0 means **skip it**: it is a documentation-sync commit (it carries a
`Docs-Sync:` trailer, so documenting it would loop forever), or it only touches
`docs/` and `README.md`, so there is no code to document.

If nothing is left, say "nothing to document in <range>" and stop. No agent, no commit.

## 3. Hand off to the agent

Launch the **`document-commit`** subagent (Agent tool, `subagent_type:
"document-commit"`) with a self-contained prompt containing:
- the range exactly as given (or the single sha);
- the list of remaining commits, oldest first, with each one's subject line;
- the list of commits that were skipped and why.

Wait for it to finish. Do not edit documentation yourself while it runs.

## 4. Verify and relay

- If the agent says it committed, confirm the new commit carries the trailer:
  `.claude/hooks/is-doc-sync-commit.sh HEAD && echo "guard OK"`. If it does not, say so
  plainly — the next hook run would loop.
- Confirm the agent's commit touched nothing but documentation, comments, and
  docstrings: `git show --stat HEAD`.
- Relay the agent's report to Brian in prose. Never push.
