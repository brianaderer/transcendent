# CLAUDE.md — transcendent

> Project description, stack, and run/test commands go here once the code exists.
> Until then, the rules below apply to everything.

---

## 1. Hard rule — no decision gates

**Never put a decision in front of Brian as a gate.** No multiple-choice menus, no
`AskUserQuestion` prompts, no plan-mode approval stops, no "Option A / Option B"
lists, no "want me to proceed?" endings.

When something genuinely needs Brian's decision, pass it back **in prose**:

- **Full explanation.** What the situation is, what each path actually does, what it
  costs, what it risks, and what happens afterward. Write it so it can be understood
  cold, without having followed the session.
- **No jargon.** If a technical term is unavoidable, explain it in plain words the
  first time it appears. Never invent vocabulary or abbreviations.
- **No two-word reductions.** Never compress a choice into a label like "quick fix",
  "full refactor", "safe path", or "ship it". A label is not an explanation. Every
  option is described in complete sentences.
- **Give a recommendation and the reasoning behind it**, then stop. Do not wait at a
  prompt — the prose is the hand-off.

Everything that does *not* need Brian's decision gets done without asking. Asking
about something that has an obvious answer is also a decision gate.

---

## 2. Working rules

- **Evidence over inference.** Logs, traces, and test runs are evidence. Comments,
  docstrings, and plan documents are not — they describe intent at some past moment
  and nothing verifies them. In every write-up, say which claims were *verified* (you
  ran it or read the code) and which were *inferred* (you reasoned it).
- **Diagnose and fix outside the main worktree.** Bugs are investigated in a separate
  git worktree and nothing comes back to the main worktree until it is proven. See
  `/isolate-and-pin`.
- **A defect stays open until a passing test proves the fix.** A claim, a code read,
  or a green run that doesn't cover the bug does not close it.
- **Report faithfully.** If tests fail, say so with the output. If a step was skipped,
  say that. Distinguish "the cause is understood and covered by a unit test" from
  "the path a real user drives has been re-run" — they are different claims.

## 3. Git

- **Never push** unless Brian says "push" in the current message.
- **Never** `git add -A`, `git add .`, or `git add -u`. Stage files by name.
- No stash, rebase, amend, force-push, or history rewrite without explicit permission.
- Commit locally after each meaningful slice of work.
- Never write to a server, database, or other remote system without permission.
  Reading is fine.

## 4. Skills

| Skill | Use for |
|---|---|
| `/isolate-and-pin` | Any bug, regression, or "why is this failing". Gathers evidence, forms competing explanations, and tests each one in parallel in its own worktree to measure what each fix would actually do before anything is installed. |
| `/tdd` | One explanation or one defect, taken from a failing test to a proven fix in an isolated worktree. Used by `/isolate-and-pin` for each explanation, or directly for a single known bug. |
