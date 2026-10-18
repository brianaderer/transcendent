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
a loose markdown file. If it isn't in the atlas, it isn't the plan.

The atlas has two layers, and they always say the same thing:

1. **The plates** — markdown files in `docs/atlas/`. These are the source of truth:
   every decision, every detail, every open question is written here first. Modeled
   on the kontraktr atlas (`~/vintly/kontraktr/atlas`).
2. **The presentation page** — `docs/atlas/atlas.html`, one interactive web page built
   from the plates, for viewing. Modeled on the Vintly Flow Atlas
   (https://claude.ai/artifact/PPfWjhKfmb6zXUoA6H5xSJ). It adds no information of its
   own; it shows the plates as an exploded-view diagram you click through.

**Order of work: plate first, then page.** A change to the plan is made in the plate,
then carried into the page. Never change the page to change the plan. If the two
disagree, the plate is right and the page is out of date.

### 3.1 The plates (source of truth)

- **One plate per subject.** A plate is a single markdown file covering one area:
  the system map, a module, a pipeline, a data model, an environment.
- **Numbered by area, in tens.** `00` is the index, `01`–`09` are the system-wide
  plates (`01` is always the system map), each later group of ten is one area (for
  example `20`–`29` is the data model, `30`–`39` the frontend), and `90` is open
  questions. An area with several plates gets a subfolder:
  `20-data-model/21-<name>.md`, `22-<name>.md`.
- **Every plate starts the same way:** `# NN — Title`, then a link back to the index
  (and to open questions where relevant), then a short paragraph saying what the plate
  covers.
- **Diagrams in Mermaid**, with prose underneath that explains them. The diagram shows
  the shape; the prose says why. Mermaid keeps the plates readable on GitHub and in
  any markdown viewer.
- **Every box that has its own plate says so in the plate.** Put the link in the box
  label or in the prose beside the diagram (`see [03](03-messaging.md)`). These links
  are what the page turns into clickable drill-downs, so a missing link is a missing
  drill-down.
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

### 3.2 The presentation page (built from the plates)

`docs/atlas/atlas.html` is one self-contained page, built the way the Vintly Flow
Atlas is built:

- **The front view is plate `01`, the system map**, drawn as boxes in labeled lanes
  with arrows between them.
- **Every box is clickable** and opens that part's plate as a breakout: its diagram,
  its opening paragraph, and fact chips for the details that bear weight (source
  files, limits, models, queues).
- **Boxes inside a breakout drill further.** A box whose plate links to another plate
  is drawn with a highlighted outline and opens that plate when clicked. A back button
  retraces the trail. A header button opens any plate directly, and the plate's number
  in the address (`atlas.html#21`) opens it on load.
- **Open questions and draft status show on the page.** A plate marked `(DRAFT)` shows
  as a draft; a `?` detail or proposal is drawn with a dashed outline; the `90` plate
  has its own view.
- **One visual language everywhere.** Box color says what a thing *is* (model call,
  tool, service or queue, data store, app screen, result). Line style says how control
  moves (plain call, conditional step, bounded loop, recursion). Every breakout shows
  the key.
- **Diagrams are data, not drawings.** The page holds tables — boxes, arrows, plates,
  and the drill table that says which box opens which plate — and a small renderer
  draws SVG from them. Mermaid is not used on the page.
- Light and dark themes, readable at phone width, no external scripts beyond fonts.
  It must open straight from disk and as a published page.

**Keeping the two layers in sync.** Whenever a plate changes, the page is updated in
the same piece of work, and checked against the plates before committing:

- every plate in `00-index.md` has a breakout on the page, and no breakout exists
  without a plate;
- every box and arrow on a plate's Mermaid diagram appears in that plate's breakout,
  with the same names;
- every plate-to-plate link from a box is in the drill table, and every drill-table
  entry matches a link in a plate.

**Publishing.** The page is published as a private claude.ai artifact, always to the
same URL, so the link never changes. The URL is recorded at the top of `README.md` and
in `00-index.md`. After each change: commit, then republish.

Commit atlas changes on their own, with messages starting `Atlas:` — for example
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
