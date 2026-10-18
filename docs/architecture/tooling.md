# tooling

**Source:** `.claude/`, `.githooks/`   ·   **Tests:** `tests/hooks/test_commit_checks.sh`

## Purpose
The repo's own workflow machinery. Right now that means three things:

- **The commit chain.** After every commit that changes anything outside `docs/` and
  `README.md`, `/commit-chain` runs on it. In a separate worktree checked out at that
  commit, it documents the commit's changes, follows every reference outward, and makes
  one documentation-only commit; it then puts that commit on the current branch without
  touching any other work in progress, and finally reviews both commits against Robert
  C. Martin's *Clean Code*. The rules this serves are in
  [`CLAUDE.md`](../../CLAUDE.md) §6.
- **The boot test.** `/test-boot` plays the reviewer from the challenge brief: it
  clones the repo into an empty folder, follows the README's install and run steps
  exactly as written, tries the demo, and reports what worked and what did not. The
  rule this serves is in [`CLAUDE.md`](../../CLAUDE.md) §7 (*The README is the demo*).
- **The code review.** Inside the commit chain, `/uncle-bob` reviews the code commit and
  its documentation commit against *Clean Code* and lists what to fix and how. It can
  also be run by hand on any commit or range. The reviewers asked for exactly this,
  and the guidelines it checks are in [`CLAUDE.md`](../../CLAUDE.md) §8.

This module contains no application code.

## Public interface
- **`/commit-chain [commit]`**, the skill at `.claude/skills/commit-chain/SKILL.md`,
  run automatically after every commit (default `HEAD`). It skips the commit if the
  loop guard says so, opens a worktree at the commit with `chain-worktree.sh create`,
  launches the `document-commit` agent there with only that commit, lands the agent's
  documentation commit with `chain-worktree.sh land`, launches the `uncle-bob` agent in
  the same worktree on exactly the two commits (skipped when neither changes source
  code or tests), removes the worktree, runs `/test-boot` if the boot steps changed,
  and relays both reports. Inside a Claude Code session it then handles the review
  findings the same way `/uncle-bob` does (below), stopping after two rounds. That is
  two model calls per commit. It never pushes.
- **`/document-commit [commit | from..to]`**, the skill at
  `.claude/skills/document-commit/SKILL.md`, now the by-hand way to document a range;
  it works in the main folder, so use it when no other work is in progress. With no
  argument it documents `HEAD`. It
  resolves the commits, drops the ones the loop guard says to skip, and hands the rest
  to the agent. When the agent reports that the boot steps changed, the skill then
  runs `/test-boot` on the new documentation commit, so the README being tested is the
  updated one, and reports a boot failure plainly rather than folding it into a
  "documentation done" summary.
- **The `document-commit` agent**, `.claude/agents/document-commit.md`. Launched by
  `/commit-chain` or `/document-commit`, with an already-filtered list of commits. When
  given a worktree (`/commit-chain` always gives one), it reads, edits and commits only
  there, and works only from the diff of the commits it was given, tracing outward
  from that diff and from nothing else. Before starting, it reads the
  rules it documents against: `CLAUDE.md` §1 (plain language), §3 (never change an
  atlas plate), §6 (where documentation lives and the module template), §7 (the
  challenge rules) and §8 (the Clean Code guidelines, which apply to any comment or
  docstring it corrects), and the README's *Primary objective*. It updates
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
- **`/uncle-bob [commit | from..to]`**, the skill at `.claude/skills/uncle-bob/SKILL.md`,
  the by-hand way to review any commit or range (`/commit-chain` launches its agent
  directly). With no argument it reviews `HEAD`. It resolves the commits, drops any the loop guard
  says to skip and any that change no source code or tests, and hands the rest to the
  agent. It relays the review to Brian. Inside a Claude Code session, Must-fix findings
  are then fixed in a normal commit before any new work, Should-fix findings are fixed
  when they sit in code already being touched, and Consider findings are only reported.
  It stops after two rounds: if the same finding comes back after a fix, it reports
  both versions to Brian instead of looping.
- **The `uncle-bob` agent**, `.claude/agents/uncle-bob.md`. Launched by `/commit-chain`
  or `/uncle-bob`. When given a worktree it reads only there. From `/commit-chain` it
  gets exactly two commits, the code commit and its documentation commit, and reviews
  both, because a documentation pass may correct comments and docstrings, which are
  part of what it checks. It reads `CLAUDE.md` §8 and reviews only the source and test files the commits
  changed, reading the whole function or class around each changed line, not just the
  changed lines. Each finding has a severity (Must fix, Should fix, Consider), the file
  and function, what is wrong, and a concrete fix. Its report opens with a one-sentence
  verdict and ends with what was done well. It changes nothing and never commits.
- **`.claude/hooks/changed-files.sh [sha]`** (default `HEAD`). Prints the paths the
  commit changed, one per line. A merge commit is compared with its first parent, the
  branch it was merged into, so the list is everything the merge brought in; before
  commit `666dc6a` a merge listed nothing, so merges were never reviewed or
  documented. Exits 2 with a message when the commit does not exist, so no caller can
  mistake an error for an answer. The other three check scripts get their file list
  from it, so they treat a merge the same way.
- **`.claude/hooks/has-source-changes.sh [sha]`** (default `HEAD`). Exit 0 means the
  commit changes source code or tests, so it is worth a code review; exit 1 means it
  only touches markdown, config, data, or lockfiles; exit 2 means the commit does not
  exist. "Source" means files ending in `.py`, `.ts`, `.tsx`, `.js`, `.jsx`, `.mjs`,
  `.cjs`, `.go`, `.rs`, `.java`, `.kt`, `.rb`, `.sql` or `.sh`, plus anything under
  `.githooks/` (git hook scripts have no file extension). It gives the right answer
  for commits of any size, including ones that change thousands of files.
- **`.claude/hooks/is-skippable-commit.sh [sha]`** (default `HEAD`), the single loop
  guard. Exit 0 means "run no post-commit steps for this commit": it carries a
  `Docs-Sync` trailer, or it changes nothing outside `docs/` and `README.md`. Exit 1
  means process it; exit 2 means the commit does not exist. It was called
  `is-doc-sync-commit.sh` before commit `b97420e`.
- **`.claude/hooks/chain-worktree.sh`**, the isolation for `/commit-chain`, with three
  commands:
  - `create <sha>` makes a worktree at `<sha>` under `.chain-worktrees/` (named after
    the short commit id and the process id) and prints its path.
  - `land <base> <docs>` takes the documentation commit `<docs>`, made on top of
    `<base>`, applies its changes to the main folder, and commits only the files it
    changed, with its message (and so its `Docs-Sync` trailer) kept. Anything else
    staged or edited in the main folder is left alone. It prints the new commit. If
    any of those files already has uncommitted edits in the main folder, it lands
    nothing: it points the branch `docs-sync/<base>` at the documentation commit,
    prints `parked: docs-sync/<base>`, and exits 3. It exits 2 if the documentation
    commit changes nothing.
  - `remove <path>` deletes the worktree.
- **`.claude/hooks/claude-post-commit.sh`**, a Claude Code `PostToolUse` hook,
  registered in `.claude/settings.json` for the `Bash` tool. It was called
  `post-commit-document.sh` before commit `b97420e`.
- **`.githooks/post-commit`**, a git hook for commits made outside Claude Code.
- Before commit `47db3e5`, a script called `post-commit-steps.sh` decided which skills
  ran after a commit (`/uncle-bob`, then `/document-commit`). It is gone; both hooks
  now start `/commit-chain`, which decides the rest.
- **`tests/hooks/test_commit_checks.sh`**, the tests for the scripts above. Run
  it after any change to `.claude/hooks/` or `.githooks/`; it prints one `ok` or
  `FAIL` line per case and exits 1 if any case failed.

## How it works
There are two ways a commit gets noticed, and both end at the same guard and the same
skill, `/commit-chain`.

**Inside Claude Code.** After every Bash tool call, `claude-post-commit.sh` reads the
call from standard input. If the command was a `git commit` (also `git -C <dir>
commit`), it moves to the repo, and checks that `HEAD` was committed in the last 60
seconds, which is how it tells a commit that happened from one that failed. Unless the
loop guard says to skip the commit, the hook adds a note to Claude's context telling it
to run `/commit-chain <sha>` before any further code change. The hook only asks;
Claude runs the chain.

**Outside Claude Code.** The git hook `.githooks/post-commit` runs after a terminal
commit, once enabled with `git config core.hooksPath .githooks`. It exits quietly when
`CLAUDECODE` is set (the commit came from Claude Code, so the other hook handles it),
when `SKIP_POST_COMMIT_STEPS` is set (this skips the whole chain; the older name
`SKIP_DOC_SYNC` still works), when the `claude` command is not installed, or when the
loop guard says to skip the commit. Otherwise it prints one line saying the chain has
started and where its log is, starts
`claude -p "/commit-chain <sha>"` in the background, and returns at once, so the
terminal is free while the chain runs. The chain's output goes to
`.chain-worktrees/logs/<sha>.log`. The headless run accepts edits automatically and
may use only: file reading, searching, editing and writing, launching agents, the git
commands `log`, `diff`, `show`, `diff-tree`, `rev-parse`, `rev-list`, `grep`, `status`,
`add`, `commit` and `git -C`, `ls`, and the scripts `changed-files.sh`,
`has-source-changes.sh`, `is-skippable-commit.sh` and `chain-worktree.sh`. It cannot
push. Review findings are written to the log; nothing is fixed automatically after a
terminal commit.

**Inside the chain.** The chain opens a worktree at the commit, so whatever else is
going on in the main folder (uncommitted edits, staged files, newer commits) cannot
leak into the documentation or the review. The documentation agent commits in that
worktree. `chain-worktree.sh land` then copies the change onto the current branch by
applying the difference between the two commits and committing only those files, so
another person's staged work is not swept into the documentation commit. If the same
documentation files are being edited in the main folder, landing would collide with
those edits, so the commit is parked on `docs-sync/<sha>` instead, for Brian to merge
once his edits are committed. The review then runs in the same worktree, which now
holds both commits.

**The tests.** `tests/hooks/test_commit_checks.sh` builds throwaway git repos in a
folder of its own under `.test-tmp/` in the repo (ignored by git, deleted when the
tests finish; each run gets a separate folder, so two runs at once cannot collide).
Its 18 checks cover which commits count as having source changes (including a
2,000-file commit), which are skippable (including one with the `Docs-Sync` trailer),
that a merge commit lists only what the merged branch brought in, that an unknown
commit is an error rather than a "no", and the worktree landing: a documentation
commit lands while other work is staged, contains only the documentation, keeps its
`Docs-Sync` trailer, and leaves the staged work staged; and when its files have local
edits it is refused and parked on a branch. Each group of checks builds one
throwaway repo and adds commits to it, and each check looks only at the newest
commit. A check of printed output passes only when the output matches and the script
also exited successfully, so a script that prints the right text and then fails is
still caught. It needs no network. It does not test
`claude-post-commit.sh`, `.githooks/post-commit` or the `/commit-chain` skill
themselves, only the scripts they use.

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

**The code review.** `/uncle-bob` resolves the commits, drops documentation-sync
commits and commits with no source changes, and launches the `uncle-bob` agent, which
checks every changed function, class and test against `CLAUDE.md` §8: names, function
size and arguments, comments, error handling, duplication and structure, tests, and
the warning signs listed in chapter 17 of the book. It ranks what it finds and
reports each pattern once with every place it occurs, rather than repeating it.

**The headless chain does not run the boot test.** Its short list of allowed tools
has no general shell access, so it cannot clone, install, or start anything. A boot
check after a terminal commit has to be run by hand with `/test-boot`.

**The loop guard.** The documentation commit would itself trigger both hooks. Three
layers stop that: the `Docs-Sync` trailer on every documentation commit (landing
keeps it), the guard skipping documentation-only commits, and the git hook standing
aside whenever `CLAUDECODE` is set, which includes the headless chain's own commits.
`/commit-chain` runs the guard before doing anything, and so do `/document-commit` and
`/uncle-bob` when run by hand; the documentation agent confirms its own commit passes
the guard.

## Uses
- `git`, for every check.
- `grep`, used by `has-source-changes.sh` and `is-skippable-commit.sh` to match
  changed file names.
- `jq`, used by `claude-post-commit.sh` to read the hook input and write its output.
  The Claude Code hook fails without it.
- `git worktree`, used by `chain-worktree.sh` to give each chain run its own checkout.
- The `claude` command-line tool, used by `.githooks/post-commit` to run the commit
  chain in the background. Without it the git hook does nothing.
- The `test-boot` agent also uses whatever tools the README tells a reviewer to
  install (none yet, because there is no application code yet), and reads the main
  repo's local `.env` for any API key the README asks for.

## Used by
- Claude Code, which runs the `PostToolUse` hook from `.claude/settings.json`.
- git, which runs `.githooks/post-commit` once `core.hooksPath` points at `.githooks`.
- `claude-post-commit.sh` and `.githooks/post-commit` both call
  `is-skippable-commit.sh` and then start `/commit-chain`.
- `/commit-chain` calls `is-skippable-commit.sh`, `chain-worktree.sh` and
  `has-source-changes.sh`, launches the `document-commit` and `uncle-bob` agents, and
  runs `/test-boot` when the documentation agent reports that the boot steps changed.
  The `/document-commit` skill does the same `/test-boot` step when run by hand.
  `CLAUDE.md` §7 also requires `/test-boot` before calling boot-affecting work finished
  and before submitting.
- `is-skippable-commit.sh` and `has-source-changes.sh` both call `changed-files.sh`.
- The `/document-commit` skill, its agent, and the `/uncle-bob` skill call
  `is-skippable-commit.sh`; the `/uncle-bob` skill also calls `has-source-changes.sh`.
- `tests/hooks/test_commit_checks.sh` runs `has-source-changes.sh`,
  `is-skippable-commit.sh`, `changed-files.sh` and `chain-worktree.sh`.
- No application module uses it.

## Configuration and data
- `.claude/settings.json`: registers the `PostToolUse` hook, run as
  `"$CLAUDE_PROJECT_DIR"/.claude/hooks/claude-post-commit.sh`.
- `core.hooksPath` (git config, set once per clone): enables `.githooks/post-commit`.
- `SKIP_POST_COMMIT_STEPS`: set for one commit (`SKIP_POST_COMMIT_STEPS=1 git commit …`)
  to make the git hook skip the commit chain. The older name, `SKIP_DOC_SYNC`, still
  works. (`DOC_SYNC_RUNNING`, which the git hook used to set while a headless sync ran,
  was removed in commit `47db3e5`; `CLAUDECODE` now covers that case.)
- `CLAUDECODE`: set by Claude Code, including the headless chain; the git hook stands
  aside when it is present.
- `Docs-Sync: <range>` commit trailer: marks a documentation-sync commit. It must be
  the first trailer line.
- `.gitignore`: ignores `.boot-test/` (the throwaway clones made by `/test-boot`),
  `.test-tmp/` (the throwaway repos made by the hook tests), `.chain-worktrees/` (the
  worktrees and logs made by `/commit-chain`), and `.env` (local secrets).
- `.chain-worktrees/<short sha>-<process id>/`: one worktree per chain run, removed
  when the run finishes. `.chain-worktrees/logs/<sha>.log` holds the output of a chain
  started by the git hook; logs are kept.
- `docs-sync/<sha>` branches: where a documentation commit is parked when it could not
  be landed.
- `.boot-test/<date-time>/`: one folder per boot test, holding the clone in `app/` and
  the command output in `logs/`. Never committed; left in place after each run.
- Writes: `/commit-chain` and `/document-commit` write files under `docs/`,
  `README.md`, and comments or docstrings in source files; the chain also writes its
  worktrees and logs under `.chain-worktrees/`. `/uncle-bob` writes nothing. `/test-boot` writes only
  inside its own `.boot-test/` folder. The hook tests write only inside `.test-tmp/`,
  and delete it when they finish. Nothing outside the repo.
