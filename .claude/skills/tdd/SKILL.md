---
name: tdd
description: Test-driven loop for ONE defect or ONE hypothesis about a defect — work in an isolated git worktree, classify the problem honestly, write a test that fails for the real reason, apply the smallest fix, prove the test actually catches the bug by breaking the fix on purpose, measure side effects on the rest of the suite, commit locally, and report in prose. Never pushes, never merges. Use when the user says "/tdd <bug>", or when /isolate-and-pin hands a subagent a hypothesis to test.
---

# TDD — one defect (or one hypothesis), red to green, local only

Take a single defect, or a single hypothesis about a defect, from "suspected" to
"proven true or proven false," with a measured fix if it is true.

**Read `CLAUDE.md` §1 first.** There are no decision gates in this loop. When you hit
something that needs Brian's call, you stop and explain it in prose — never a menu,
never a two-word label.

**Inviolable constraints:**
- **Never push. Never merge. Never open a pull request.** Branches and commits stay
  local.
- **Worktree first.** No edits until you are inside your own worktree. Never edit the
  main worktree.
- **Scope is this one defect or hypothesis.** No drive-by refactors. Adjacent problems
  get noted in the report, not fixed.
- **A defect is open until a passing test proves the fix.**

Run the steps in order. If a step can't complete, stop and report why.

---

## Step 0 — Worktree

If an orchestrator (such as `/isolate-and-pin`) already created your worktree, `cd`
into the path you were given and confirm where you are:

```bash
git rev-parse --show-toplevel
git rev-parse --abbrev-ref HEAD
git log --oneline -1
```

Otherwise create one off the main branch:

```bash
MAIN=$(git rev-parse --show-toplevel)
SLUG=<short-kebab-slug>
WT="$MAIN/../transcendent-wt/$SLUG"
git -C "$MAIN" worktree add -b "fix/$SLUG" "$WT"
cd "$WT"
```

If `.claude/` is gitignored, copy it into the worktree so the skills are available.
Do the project's per-worktree setup (see `CLAUDE.md` once it documents one).

**Uncommitted changes do not cross worktrees.** Before running anything, confirm the
code you think you're testing is actually in this tree:

```bash
grep -c "<symbol you expect>" <file>     # 0 means you are about to measure nothing
```

---

## Step 1 — Classify before you trace

A report that says "X doesn't work" is a claim, not a fact. Put the problem in exactly
one class:

| Class | Meaning |
|---|---|
| **Bug** | The system does something wrong by its own contract — wrong output, crash, data loss, reporting success when it failed, security hole. |
| **Usability friction** | It works and the right result is reachable, but getting there was confusing or slow. Not a bug. |
| **Feature request** | It doesn't do something it was never built to do. Not a bug. |
| **Working as designed** | The behavior is intentional and correct; the report rests on a wrong premise. |
| **Test or infrastructure problem** | The failure is in the test harness, fixtures, environment, or stale data — not the product. |
| **Documentation drift** | The docs are wrong; the product is fine. |

Before accepting "bug," try to knock it down:
1. Did the reporter use the intended path?
2. Is the expectation itself reasonable?
3. Was it self-inflicted (stale state, wrong config, a manual workaround)?
4. If it "reported success but failed" — is the error actually delivered somewhere
   else, through a step the reporter skipped?

**When testing a hypothesis from `/isolate-and-pin`:** your job is to find out whether
the hypothesis is true, not to defend it. "This hypothesis is false, and here is the
evidence" is a fully successful run.

For a surviving bug, find the cause **in the code at this commit**: cite
`file::symbol`, quote the lines that matter. Say where the report or hypothesis was
right and where it was wrong. Name an existing place in the codebase that already does
this correctly — the fix should follow that pattern.

---

## Step 2 — Write the failing test; confirm it fails for the right reason

The test is what closes the defect. It must fail now and pass after the fix.

- **Assert on the real behavior**, not a stand-in for it.
- **Test one layer out from the thing you're fixing.** Drive the real entry point and
  check what it hands downstream. A test that calls a helper by name disappears the
  day someone deletes the helper — the guard leaves with the thing it guarded.
- **Cover every surface of the bug**, not just the first symptom you saw.
- **If a currently-passing test protects the buggy behavior, invert it** rather than
  adding a second test beside it.
- **Prefer fast, isolated tests** (no shared server, database, or network) so sibling
  subagents can run in parallel safely. If the real proof needs a slow end-to-end test
  that uses shared resources, write it, but flag it as "must run alone" and don't run
  it concurrently with other agents.

Run it. **Redirect output to a file, then read the file** — don't grep live output.
Read the actual assertion message and confirm it fails *for the reason the hypothesis
predicts*. A test that fails for a different reason has not confirmed anything. Save
the failing output verbatim for the report.

**What the result means for a hypothesis:**
- Fails for the predicted reason → the hypothesis is **supported**. Continue.
- Passes, or fails for an unrelated reason → the hypothesis is **not supported**.
  Record exactly what you saw, skip to Step 6, and report it as refuted.

---

## Step 3 — Smallest fix

The smallest change that turns the failing test green, following the pattern you
named in Step 1. No scope creep.

If the fix needs a real design choice that belongs to Brian — not an implementation
detail you can settle yourself — stop here with the failing test committed and explain
the choice in prose in your report (see `CLAUDE.md` §1).

---

## Step 4 — Prove it, and prove the test bites

1. Re-run the new test. Confirm it passes for the right reason.
2. **Break the fix on purpose and watch the test fail.** Revert the fix, flip the
   guard, or hardcode the old value — whatever a realistic future refactor might do.
   Run the test, capture the failure verbatim, restore the fix, confirm it passes
   again. A test whose failure was never actually observed is a hope, not a proof.
   One executed break per claim the test makes.
3. **Check the other inputs that reach the same code.** If the fix lands on a shared
   path, ask what else flows through that branch, and test those cases too — including
   the case that must *still* behave the old way. A fix with no counterweight test is
   an over-correction waiting to be discovered later.

---

## Step 5 — Measure impact

This is what lets fixes be compared before any of them is installed.

- Run the **full** test suite (or the widest suite that is safe to run in parallel)
  with the fix in place. Redirect to a file.
- Record precisely: tests that went from failing to passing, tests that went from
  passing to failing, and anything that was already failing before your change (run
  the suite on the unmodified base commit if you need the baseline).
- Note any behavior change outside the bug's own path, any performance or resource
  effect you observed, and any end-to-end check you could not run.

---

## Step 6 — Commit locally and report

```bash
git add <named files only>
git commit -m "<area>: <one-line summary>

<what was found, what changed, which test proves it>

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

Commit even when the hypothesis was refuted — the test that refuted it is evidence.
**Never push.**

Your final message is the report. Write it in plain prose, no jargon, and fill in:

- **Verdict:** supported, refuted, or inconclusive — and in one or two full sentences,
  why.
- **Classification** and an honest severity (how many people, how badly, how often —
  don't inflate).
- **Cause**, with `file::symbol` and the quoted code. Mark each claim verified or
  inferred.
- **The fix**, with the files and symbols it touched. Branch name and commit hash.
- **Evidence:** the failing test output, then the passing output.
- **Break-the-fix results:** a table of what you broke → which test failed → the exact
  failure message.
- **Impact:** what else changed in the suite, and anything you could not run.
- **Anything that needs Brian's decision**, explained in full prose with your
  recommendation. No menus.
