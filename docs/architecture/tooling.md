# tooling

**Source:** `.claude/`, `.githooks/`   ·   **Tests:** none yet

## Purpose
The repo's own workflow machinery. Right now that means two things:

- **The automatic documentation sync.** After every commit that changes code,
  `/document-commit` runs, documents the change, follows every reference outward, and
  makes one documentation-only commit. The rules this serves are in
  [`CLAUDE.md`](../../CLAUDE.md) §6.
- **The boot test.** `/test-boot` plays the reviewer from the challenge brief: it
  clones the repo into an empty folder, follows the README's install and run steps
  exactly as written, tries the demo, and reports what worked and what did not. The
  rule this serves is in [`CLAUDE.md`](../../CLAUDE.md) §7 (*The README is the demo*).

This module contains no application code.

## Public interface
- **`/document-commit [commit | from..to]`**, the skill at
  `.claude/skills/document-commit/SKILL.md`. With no argument it documents `HEAD`. It
  resolves the commits, drops the ones the loop guard says to skip, and hands the rest
  to the agent. When the agent reports that the boot steps changed, the skill then
  runs `/test-boot` on the new documentation commit, so the README being tested is the
  updated one, and reports a boot failure plainly rather than folding it into a
  "documentation done" summary.
- **The `document-commit` agent**, `.claude/agents/document-commit.md`. Launched only by
  the skill, with an already-filtered list of commits. Before starting, it reads the
  rules it documents against: `CLAUDE.md` §1 (plain language), §3 (never change an
  atlas plate), §6 (where documentation lives and the module template) and §7 (the
  challenge rules), and the README's *Primary objective*. It updates
  `docs/architecture/` and the README, with the README's install, configure and run
  steps treated as the most important text in the repo. It then traces the fan-out wave
  by wave, sweeps every doc for stale paths and names, logs any plan-versus-code
  difference in `docs/atlas/90-open-questions.md`, and makes one commit carrying the
  `Docs-Sync: <range>` trailer. Its report says whether the commits touched anything
  that affects booting the app (dependency files, container and compose files, scripts
  the README runs, `.env.example` and environment variables, ports, required services,
  data loading, tool versions, the start command). It never pushes.
- **`/test-boot [ref] [github]`**, the skill at `.claude/skills/test-boot/SKILL.md`.
  Tests a commit or branch (default `HEAD`), cloned from the local repo, or from
  GitHub when `github` is given (GitHub only has what has been pushed, and while the
  repo is private a clone needs this machine's GitHub login). It tests the commit, not
  uncommitted changes in the working folder. It refuses to run unless `.boot-test/` is
  listed in `.gitignore`, then hands off to the agent and relays its report. It never
  applies the fixes it suggests; those go in a normal commit.
- **The `test-boot` agent**, `.claude/agents/test-boot.md`. Launched only by the skill.
  It makes a fresh clone under `.boot-test/<date-time>/app`, reads the README once,
  checks the listed prerequisites on this machine, runs every step exactly as written,
  then follows the README's demo steps to prove the app really works. It reports
  **Boot succeeded** or **Boot failed at step N**, a table of every step, the friction
  points worst first with the exact README change that would remove each, the total
  time, what it could not test, and where the logs are. It changes nothing in the repo
  and never commits.
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
edits accepted automatically, and a short list of allowed tools: file reading, editing,
and searching; read-only git commands (`log`, `diff`, `show`, `diff-tree`, `rev-parse`,
`rev-list`, `grep`, `status`) plus `git add` and `git commit`; `ls`; and the loop guard
script. It cannot push.

**The boot test.** `/test-boot` resolves the commit, checks that `.boot-test/` is
ignored by git, and launches the `test-boot` agent. The agent uses a clone rather than
a git worktree because a clone carries none of this machine's local git settings,
untracked files, or ignored files such as `.env`, which is exactly the reviewer's
situation. Because the clone sits inside the main repo folder, some tools may find
config files (`.env`, `package.json`, compose files) in a parent folder; the agent
treats a step that only worked because of that as a finding. When a step fails, it
records the exact error, makes only the smallest move a reasonable reviewer would make
to continue, and writes down what it did. If the README asks for an API key, it copies
that one value from the main repo's local `.env` into the clone's `.env` without
printing it. When it finishes it stops every process and container it started and
leaves the `.boot-test/` folder in place so the logs can be read.

**The headless git hook does not run the boot test.** Its short list of allowed tools
has no general shell access, so it cannot clone, install, or start anything. A boot
check after a terminal commit has to be run by hand with `/test-boot`.

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
- The `test-boot` agent also uses whatever tools the README tells a reviewer to
  install (none yet, because there is no application code yet), and reads the main
  repo's local `.env` for any API key the README asks for.

## Used by
- Claude Code, which runs the `PostToolUse` hook from `.claude/settings.json`.
- git, which runs `.githooks/post-commit` once `core.hooksPath` points at `.githooks`.
- The `/document-commit` skill runs `/test-boot` when its agent reports that the boot
  steps changed. `CLAUDE.md` §7 also requires `/test-boot` before calling boot-affecting
  work finished and before submitting.
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
- `.gitignore`: ignores `.boot-test/` (the throwaway clones made by `/test-boot`) and
  `.env` (local secrets).
- `.boot-test/<date-time>/`: one folder per boot test, holding the clone in `app/` and
  the command output in `logs/`. Never committed; left in place after each run.
- Writes: `/document-commit` writes files under `docs/`, `README.md`, and comments or
  docstrings in source files. `/test-boot` writes only inside its own `.boot-test/`
  folder. Nothing outside the repo.
