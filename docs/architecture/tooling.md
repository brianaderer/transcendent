# tooling

**Source:** `.claude/`, `.githooks/`   ·   **Tests:** none yet

## Purpose
The repo's own workflow machinery. Right now that means the automatic documentation
sync: after every commit that changes code, `/document-commit` runs, documents the
change, follows every reference outward, and makes one documentation-only commit. The
rules this serves are in [`CLAUDE.md`](../../CLAUDE.md) §6. This module contains no
application code.

## Public interface
- **`/document-commit [commit | from..to]`**, the skill at
  `.claude/skills/document-commit/SKILL.md`. With no argument it documents `HEAD`. It
  resolves the commits, drops the ones the loop guard says to skip, and hands the rest
  to the agent.
- **The `document-commit` agent**, `.claude/agents/document-commit.md`. Launched only by
  the skill, with an already-filtered list of commits. It updates `docs/architecture/`,
  traces the fan-out wave by wave, sweeps every doc for stale paths and names, logs any
  plan-versus-code difference in `docs/atlas/90-open-questions.md`, and makes one commit
  carrying the `Docs-Sync: <range>` trailer. It never pushes.
- **`.claude/hooks/is-doc-sync-commit.sh [sha]`** (default `HEAD`), the single loop
  guard. Exit 0 means "do not document this commit": it carries a `Docs-Sync` trailer,
  or it changes nothing outside `docs/` and `README.md`. Exit 1 means document it.
- **`.claude/hooks/post-commit-document.sh`**, a Claude Code `PostToolUse` hook,
  registered in `.claude/settings.json` for the `Bash` tool.
- **`.githooks/post-commit`**, a git hook for commits made outside Claude Code.

## How it works
There are two ways a commit gets noticed, and both end at the same guard and skill.

**Inside Claude Code.** After every Bash tool call, `post-commit-document.sh` reads the
call from standard input. If the command was a `git commit` (also `git -C <dir>
commit`), it moves to the repo, and checks that `HEAD` was committed in the last 60
seconds, which is how it tells a commit that happened from one that failed. It then
asks the loop guard. If the commit should be documented, the hook adds a note to
Claude's context telling it to run `/document-commit <sha>` before any further code
change. The hook only asks; Claude runs the skill.

**Outside Claude Code.** The git hook `.githooks/post-commit` runs after a terminal
commit, once enabled with `git config core.hooksPath .githooks`. It exits quietly when
`CLAUDECODE` is set (the commit came from Claude Code, so the other hook handles it),
when `SKIP_DOC_SYNC` is set, when `DOC_SYNC_RUNNING` is set (a sync is already running),
or when the `claude` command is not installed. Otherwise it asks the loop guard and, if
needed, runs `claude -p "/document-commit <sha>"` headlessly with `DOC_SYNC_RUNNING=1`,
edits accepted automatically, and a short list of allowed tools and git commands.

**The loop guard.** The documentation commit would itself trigger both hooks. Three
layers stop that: the `Docs-Sync` trailer on every sync commit, the guard skipping
documentation-only commits, and the git hook's environment-variable checks. The skill
also runs the guard on each commit before launching the agent, and confirms the agent's
commit passes it afterwards.

## Uses
- `git`, for every check.
- `jq`, used by `post-commit-document.sh` to read the hook input and write its output.
  The Claude Code hook fails without it.
- The `claude` command-line tool, used by `.githooks/post-commit`. Without it the git
  hook does nothing.

## Used by
- Claude Code, which runs the `PostToolUse` hook from `.claude/settings.json`.
- git, which runs `.githooks/post-commit` once `core.hooksPath` points at `.githooks`.
- No application module uses it.

## Configuration and data
- `.claude/settings.json`: registers the `PostToolUse` hook, run as
  `"$CLAUDE_PROJECT_DIR"/.claude/hooks/post-commit-document.sh`.
- `core.hooksPath` (git config, set once per clone): enables `.githooks/post-commit`.
- `SKIP_DOC_SYNC`: set for one commit to skip the git hook.
- `DOC_SYNC_RUNNING`: set by the git hook while a headless sync runs.
- `CLAUDECODE`: set by Claude Code; the git hook stands aside when it is present.
- `Docs-Sync: <range>` commit trailer: marks a documentation-sync commit. It must be
  the first trailer line.
- Writes: files under `docs/`, `README.md`, and comments or docstrings in source files.
  Nothing outside the repo.
