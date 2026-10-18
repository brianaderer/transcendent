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

**All plans are made in the atlas.** No plan exists only in chat, in plan mode, or in
a loose markdown file. If it isn't in the atlas, it isn't the plan. The model to
follow is the Vintly Flow Atlas (https://claude.ai/artifact/PPfWjhKfmb6zXUoA6H5xSJ).

**What the atlas is.** One self-contained, interactive HTML page,
`docs/atlas/atlas.html`, which renders in a browser like an exploded-view diagram:

- **The system map** is the page's front view: every major part of the system as a
  box, arranged in labeled lanes, with arrows for how they talk to each other.
- **Every box is clickable.** Clicking it opens that box's **plate**: a breakout
  showing what's inside it, with its own diagram, a one-paragraph explanation, and
  fact chips (source files, limits, models, queues — whatever bears weight).
- **Boxes inside a plate drill further.** A box that has a plate of its own is drawn
  with a highlighted outline and opens that plate when clicked. A back button retraces
  the trail. You can go from the whole system down to a single function and back.
- **Plates also have their own buttons in the header**, so any plate can be opened
  directly, and a plate's name in the address (`atlas.html#ratify`) opens it on load.
- **One visual language everywhere.** Box color says what a thing *is* (model call,
  tool, service or queue, data store, app screen, result). Line style says how
  control moves (a plain call, a conditional step, a bounded loop, recursion). Every
  plate shows the key.
- **Paths can be lit up.** Where the system behaves differently in different modes,
  a toggle highlights the boxes and arrows each mode uses, numbered in the order a
  request travels.

**How it's built.**

- **The diagrams are data, not drawings.** The page holds tables — boxes (position,
  title, sub-lines, kind, the source file it lives in), arrows (from, to, label,
  style), plates, and the drill table that says which box opens which plate — and a
  small renderer draws SVG from them. Changing the plan means changing rows, never
  hand-placing shapes.
- **Every box that has a plate must be in the drill table.** A box that should drill
  and doesn't is a bug in the atlas.
- **Light and dark themes**, readable at phone width, no external scripts beyond
  fonts. It must open straight from disk and as a published page.
- **It is published as a private claude.ai artifact**, always to the same URL, so the
  link never changes. The URL is recorded at the top of `README.md`. After each
  change: commit, then republish.

**Plates record what Brian has specified, not what was guessed.** Anything proposed
but not decided is drawn as pending (dashed outline) and has an entry in
`docs/atlas/90-open-questions.md`.

**Open questions.** `90-open-questions.md` is where decisions wait for Brian and
where they're recorded once made. Each open question gets an ID (`OPEN-1`,
`OPEN-2`, …), is written in full sentences (§1), and names the plate it affects. When
Brian decides, the row moves to the Resolved table with the decision and the date,
and the affected plates are updated to match.

Commit atlas changes on their own, with messages starting `Atlas:` — for example
`Atlas: ratify plate — add the escalation loop`.

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
