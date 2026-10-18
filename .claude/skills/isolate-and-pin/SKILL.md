---
name: isolate-and-pin
description: Defect investigation protocol — gather logs and code traces, write down every plausible explanation as a testable hypothesis, then send one subagent per hypothesis into its own git worktree to run /tdd and prove it true or false. Confirmed fixes are then combined in a separate worktree to see how they interact. Produces a measured comparison of every candidate fix before anything touches the main worktree. Use for ANY bug, regression, flaky test, or "why is this failing". Not for new features.
---

# Isolate and pin

Brian's standing protocol: **open a new worktree, exercise it, write tests, isolate
and pin** — and **nothing comes back to the main worktree until it's rock solid.**

This version scales that up: instead of betting on one theory, write down every
plausible explanation, test them all in parallel, each in its own worktree, and come
back with evidence about what each fix actually does.

**Read `CLAUDE.md` §1 first.** No decision gates anywhere in this protocol — not in
the orchestrator, not in subagents. Decisions go back to Brian in full prose.

The order of the phases is load-bearing. Theorizing before reproducing, or fixing
before a failing test exists, is how wrong fixes get shipped confidently.

---

## Phase 1 — Reproduce and capture evidence

Get the defect to happen and capture what the system actually produced.

1. **Snapshot evidence immediately** — logs get rotated or overwritten by the next
   run:
   ```bash
   EVID="$(git rev-parse --show-toplevel)/../transcendent-evidence/$(date +%F)-<slug>"
   mkdir -p "$EVID" && cp <relevant logs> "$EVID/"
   ```
2. **Read the logs before the source.** Logs hold the real inputs, identifiers, error
   messages, and ordering of events.
3. **Trace the actual code path** from the entry point to the failure, using what the
   logs show. Cite `file::symbol` and what you read there. Comments, docstrings, and
   design documents are not evidence — trace the code.
4. If a known-good state exists (an older commit, another environment), get the
   honest difference:
   ```bash
   git log -S "<symbol>" --oneline     # has anything ever touched this symbol?
   git log --stat -1 <sha>             # what did that commit actually change?
   ```
5. **A search that finds nothing proves nothing** until you confirm the string you
   searched for is actually what the code would emit.

Redirect test and command output to files, then read the files. Don't grep live
output.

If you cannot reproduce it, say so plainly in the final report and list what you
tried. You can still form hypotheses from logs alone, but mark them as resting on an
unreproduced failure.

---

## Phase 2 — Write the hypotheses

Write down **every** plausible explanation, not just the favorite. Include the boring
ones (stale data, configuration, environment, test harness) — those are often the
answer.

Each hypothesis must have:

| Field | Content |
|---|---|
| **ID and slug** | `h1-cache-not-invalidated`, `h2-timezone-in-parser`, … |
| **Claim** | One or two full sentences: what is going wrong and where (`file::symbol`). |
| **Evidence for it** | The log lines and code you read that point here. Mark verified vs inferred. |
| **Evidence against it** | Anything that doesn't fit. |
| **Prediction** | A concrete, checkable statement: "If this is true, a test that does X will fail with Y." This is what makes it testable. |
| **Candidate fix** | The smallest change that would fix it if true. |
| **Shared resources** | Does testing it need a server, database, port, or anything else other agents might also use? |

Check that the hypotheses are distinct — two hypotheses with the same prediction can't
be told apart by testing, so merge them or sharpen the predictions until they differ.

Save the list to `$EVID/hypotheses.md`. This is the record the final report is
checked against.

---

## Phase 3 — Fan out: one subagent per hypothesis

Git worktrees require a git repository with at least one commit. Confirm that first.

For each hypothesis, create its own worktree off the same base commit:

```bash
MAIN=$(git rev-parse --show-toplevel)
BASE=$(git rev-parse HEAD)
git -C "$MAIN" worktree add -b "hyp/<id>-<slug>" "$MAIN/../transcendent-wt/<id>-<slug>" "$BASE"
```

If `.claude/` is gitignored, copy it into each worktree.

Then launch **one subagent per hypothesis, all in a single message** so they run in
parallel. Each subagent's prompt must be self-contained, because it does not see this
conversation:

- The worktree path and branch name, and an instruction to work only there.
- The full hypothesis entry from Phase 2, including the prediction and candidate fix.
- The path to the evidence folder.
- An instruction to follow `.claude/skills/tdd/SKILL.md` (invoke `/tdd` or read the
  file) from Step 0, treating its task as **finding out whether the hypothesis is
  true**, not proving it.
- An instruction that "refuted, with evidence" is a successful result.
- An instruction to commit locally, never push, never touch the main worktree, and
  never ask Brian anything — anything needing a decision goes into its final report
  as prose.
- The exact report format from `/tdd` Step 6.

**Shared resources:** hypotheses whose tests need the same server, database, or port
must not run at the same time. Run those subagents one after another, or have them
run only isolated tests and flag the shared-resource test for Phase 5.

---

## Phase 4 — Collect and combine

When every subagent has reported:

1. **Check each report against reality.** Open each worktree and confirm the commit
   exists, the test exists, and the claimed failing and passing outputs match a re-run.
   Don't take a subagent's word for it.
2. **Build the comparison** in `$EVID/results.md`, one row per hypothesis: verdict,
   the test that decided it, the fix, tests it fixed, tests it broke, and anything
   unrun.
3. **Combine the confirmed fixes.** If more than one hypothesis was supported, make an
   integration worktree off the same base, apply each confirmed fix branch in turn,
   and run the full suite after each one. Record:
   - whether the fixes conflict,
   - whether one fix makes another unnecessary,
   - whether the combination breaks something neither one breaks alone.
   ```bash
   git -C "$MAIN" worktree add -b "hyp/combined-<slug>" "$MAIN/../transcendent-wt/combined-<slug>" "$BASE"
   cd "$MAIN/../transcendent-wt/combined-<slug>"
   git cherry-pick <h1 fix commit>   # run suite, record
   git cherry-pick <h3 fix commit>   # run suite, record
   ```
4. If **no** hypothesis was supported, that is a finding: go back to Phase 1 with what
   was learned, write a new round of hypotheses, and fan out again. Say in the report
   how many rounds were run.

---

## Phase 5 — Pin

The pin is the deliverable, not the fix. For the fix (or combination) that the
evidence supports:

- Every claim has a test, and **every test has been seen to fail** when the fix was
  deliberately broken. Re-run those breaks in the combined worktree — a pin that bit
  in isolation might not bite once other fixes are present.
- The case that must still behave the old way has its own test, also seen to fail when
  the fix over-reaches.
- Any test flagged as "must run alone" in Phase 3 is run now, one at a time.

---

## Phase 6 — Report to Brian

Nothing is merged into the main worktree. The report hands Brian everything needed to
decide, in prose, with no jargon and no two-word labels.

Include:

1. **What was happening**, in plain words — the symptom and the real cause.
2. **Every hypothesis and what happened to it** — supported, refuted, or inconclusive,
   and the evidence that decided it. Refuted hypotheses matter: they show what has
   been ruled out.
3. **What each fix would actually do if installed** — what it fixes, what else it
   changes, what it breaks, measured, not predicted.
4. **How the fixes interact** when combined.
5. **The break-the-fix table** for the final pins: what was broken → which test failed
   → the exact failure message.
6. **What was verified versus inferred**, and anything that could not be run.
7. **Where everything lives** — branch names, worktree paths, commit hashes, evidence
   folder.
8. **Your recommendation and the full reasoning behind it.** If there is a real
   choice to make — for example, two fixes that both work but trade off differently —
   describe each one in full sentences: what it does, what it costs, what it risks,
   what it leaves for later. Then say which you would pick and why.

Then stop. Do not ask a question, do not present a menu, do not wait at a prompt.

---

## Hard constraints

- Never push, merge, or open a pull request.
- Never edit the main worktree during this protocol.
- Stage files by name; never `git add -A`, `.`, or `-u`.
- No stash, rebase, amend, or history rewrite without explicit permission.
- Never write to a server, database, or remote system without permission.
- Leave the worktrees in place for Brian to inspect. Only remove them when he says to.
