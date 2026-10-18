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

## 3. Plans live in the atlas

**All plans are written as atlas plates in `docs/atlas/`.** No plan exists only in
chat, in plan mode, or in a loose markdown file somewhere else. If it isn't in the
atlas, it isn't the plan.

How the atlas is laid out:

- **One plate per subject.** A plate is a single markdown file covering one area:
  the system map, a module, a pipeline, a data model, an environment.
- **Numbered by area, in tens.** `00` is the index, `01`–`09` are the system-wide
  plates, each later group of ten is one area (for example `20`–`29` is the data
  model, `30`–`39` the frontend), and `90` is open questions. An area with several
  plates gets a subfolder: `20-data-model/21-<name>.md`, `22-<name>.md`.
- **Every plate starts the same way:** `# NN — Title`, then a link back to the index
  (and to open questions where relevant), then a short paragraph saying what the plate
  covers.
- **Diagrams in Mermaid**, with prose underneath that explains them. The diagram shows
  the shape; the prose says why.
- **A plate still being worked out is marked `(DRAFT)`** in its title and in the
  index. Anything unresolved inside a plate is marked `?` and listed in a short
  "Open in this draft" section on that plate.
- **`00-index.md`** lists every plate in a table: plate number and link, then one
  line saying what it shows. Add a row whenever a plate is added.
- **`90-open-questions.md` is where decisions wait for Brian, and where they're
  recorded once made.** Each open question gets an ID (`OPEN-1`, `OPEN-2`, …),
  is written in full sentences (§1), and links to the plate that raised it. When
  Brian decides, the row moves to the Resolved table with the decision and the date,
  and the affected plates are updated to match.
- **Plates record what was specified, not what was guessed.** Where a plate states
  something Brian hasn't decided, mark it as a proposal.
- Commit atlas changes on their own, with messages starting `Atlas:` — for example
  `Atlas: 21 (draft): job table and status values`.

## 4. Git

- **Never push** unless Brian says "push" in the current message.
- **Never** `git add -A`, `git add .`, or `git add -u`. Stage files by name.
- No stash, rebase, amend, force-push, or history rewrite without explicit permission.
- Commit locally after each meaningful slice of work.
- Never write to a server, database, or other remote system without permission.
  Reading is fine.

## 5. Skills

| Skill | Use for |
|---|---|
| `/isolate-and-pin` | Any bug, regression, or "why is this failing". Gathers evidence, forms competing explanations, and tests each one in parallel in its own worktree to measure what each fix would actually do before anything is installed. |
| `/tdd` | One explanation or one defect, taken from a failing test to a proven fix in an isolated worktree. Used by `/isolate-and-pin` for each explanation, or directly for a single known bug. |
