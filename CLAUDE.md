# CLAUDE.md — transcendent

**What this is:** our solution to the Transcendent Endeavors "Community Voices" code
challenge. The objective and requirements are in `README.md` → *Primary objective*.
Everything built here serves that objective; §7 turns it into working rules.

> Stack and run/test commands go here once the code exists.

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

- **All work happens in this repo. Anything outside it is out of scope for edits —
  no exceptions.** Other repos and folders (kontraktr, Vintly, datalinx, anything
  else) may be *read* for patterns to copy here. They are never changed, committed
  to, or pushed from this project. References to them in this repo are read-only
  pointers to examples.

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
   on the kontraktr atlas (`~/vintly/kontraktr/atlas`, read-only reference).
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
| `/document-commit [sha \| from..to]` | Documents a commit or range, then traces everything it touches or is referenced by and updates that documentation too, until nothing reachable is stale. Runs automatically after every commit (§6). |

---

## 6. Documentation is part of every code step

The reviewers are very big on documentation. **No code change is finished until its
documentation is.** Documentation is written *with* the code, in the same commit —
not saved for later.

### Where documentation lives

| Place | What it holds |
|---|---|
| The code itself | Self-documenting names and compact functions first (§7). Docstrings on public functions, classes, and modules where the name alone can't say what it promises. Comments only for *why*, never restating *what*. |
| `docs/architecture/` | How the code is **actually built**, one file per module, plus `README.md` as the module index. |
| `docs/atlas/` | The **plan** — what Brian has decided should be built (§3). Architecture docs describe what *is*; atlas plates describe what *should be*. |
| `README.md` | The objective, and the exact steps to install, configure, run, and test from a fresh clone. |

### Module doc template — `docs/architecture/<module>.md`

```markdown
# <module>

**Source:** `path/to/module/`   ·   **Tests:** `path/to/tests/`

## Purpose
One paragraph: what this module is for and why it exists.

## Public interface
Each function, class, route, or command other code may use, and what it promises.

## How it works
The flow, in prose. A diagram if it helps.

## Uses
Modules, services, and data stores this module depends on — linked.

## Used by
Modules that depend on this one — linked.

## Configuration and data
Environment variables, config keys, tables, files it reads or writes.
```

"Uses" and "Used by" are mandatory and must match the code. They are what makes the
fan-out tracing in `/document-commit` reliable.

### Every commit, in order

1. Write the code and its tests.
2. Update the documentation for what you changed, in the same commit.
3. Commit.
4. `/document-commit` runs automatically on the new commit (below). It checks your
   documentation, follows every reference outward, fixes anything stale, and makes a
   separate documentation commit.

### The automatic hook

- **Inside Claude Code:** a `PostToolUse` hook (`.claude/settings.json` →
  `.claude/hooks/post-commit-document.sh`) notices each successful `git commit` and
  tells Claude to run `/document-commit <sha>`. When told, run it before making any
  further code change.
- **Outside Claude Code** (a commit from a terminal): the git hook
  `.githooks/post-commit` runs `/document-commit` headlessly. Enable it once per clone
  with `git config core.hooksPath .githooks`. Skip it for one commit with
  `SKIP_DOC_SYNC=1 git commit …`.

### The loop guard — never weaken it

`/document-commit` produces a commit, so without a guard it would trigger itself
forever. Three layers stop that:

1. **Every documentation-sync commit carries a `Docs-Sync: <range>` trailer.** Never
   make a commit with that trailer by hand, and never remove it from one.
2. **`.claude/hooks/is-doc-sync-commit.sh` is the single check** used by both hooks
   and by the skill. It skips any commit carrying the trailer, and any commit that
   changes only `docs/` and `README.md`.
3. **The git hook also skips** when running inside Claude Code or while a sync is
   already running (`DOC_SYNC_RUNNING`).

Any change to the hooks or the skill must keep all three layers working.

---

## 7. Rules for the challenge

These come straight from the challenge brief and what the reviewers have said they
value. The brief is summarized in `README.md` → *Primary objective*.

### The README is the demo

- Reviewers will `git clone`, follow the README **exactly**, and demo the app
  locally. **Every step in the README must work, in order, from a fresh clone on a
  clean machine.** If a change adds a dependency, an environment variable, a service,
  a port, or a setup step, the README changes in the same commit.
- One command to start everything is the goal (for example `docker compose up`, or a
  single `make` target). Every extra manual step is a chance for the demo to fail.
- Secrets never go in the repo. Provide `.env.example` with every variable named and
  explained, and say in the README exactly which keys the reviewer must supply.
- **The demo must work without live crawling.** Ship a small, committed snapshot of
  one week of community data and a command that loads it, so the app runs even if
  the source site is slow, rate-limits, or blocks the crawler. Live ingestion is a
  separate, optional command.
- Before calling anything finished, re-run the README from a fresh clone in a scratch
  folder and say whether it worked.
- **Submission needs a public repo.** The GitHub repo is private today; making it
  public is Brian's call, and happens only when he says so.

### Comparing with and without retrieval (the A/B test)

The brief asks how a model does at writing the Community Voices Document **without**
retrieval from our own data store, versus **with** it. Treat that comparison as a
core feature, not an afterthought:

- **Both versions are produced by one code path.** A single document generator takes
  a switch: retrieval off (version A, the model on its own) or retrieval on (version
  B, the model given passages pulled from our store). Everything else — model,
  settings, prompt wording, the week covered, output format — is identical, so the
  only difference between the two documents is the retrieval.
- **Every comparison run is saved** with its inputs: the week and data snapshot, the
  model name and settings, the full prompt sent for each version, the passages
  retrieved for version B, and both outputs. A run can be re-opened and re-read
  later.
- **The app shows the comparison side by side**, with measurements, not just two
  blocks of text. Measurements worth showing:
  - how many specific claims each version makes that can be traced back to a real post
    from the week, and how many cannot (the second number is invented content);
  - which real topics from the week each version covered, and which it missed;
  - how specific each version is: named people, events, dates, and threads, versus
    generic statements that would fit any week;
  - time taken and tokens used.
- **Measurements are computed by code where possible**, and, where a model is used to
  judge, the judging prompt is saved with the result and is the same for both
  versions.
- The README links to a saved example comparison, so reviewers can see the result
  even before running anything.

### Retrieval, ingestion, and visualization

- **Ingestion is automated and repeatable:** one command fetches a week of community
  data, splits it into passages, turns each into a numeric fingerprint for similarity
  search (an *embedding*), and stores it. Running it twice on the same week must not
  create duplicates.
- **Plan for too much data:** filter to the week, remove duplicates, cap the number
  of posts per thread, and summarize long threads before storing. Document the limits
  chosen and why.
- **Record retrieval statistics:** every time a stored passage is retrieved, count
  it. The app shows which passages are retrieved most.
- **Show a flattened picture of the embeddings:** squash them down to two dimensions
  and plot them, colored by topic or thread, so a reviewer can see how the week's
  conversation clusters.

### Code quality the reviewers asked for

The brief names these explicitly: self-documenting code, unit tests, compact
functions, and Robert C. Martin's *Clean Code* principles.

- **Names say what things do.** If a function needs a comment to explain what it does,
  rename or split it instead.
- **Functions are small and do one thing.** As a working limit, a function longer
  than about 20 lines, or taking more than three arguments, gets split unless there's
  a stated reason.
- **Every unit of logic has unit tests,** written first (`/tdd`). Tests never call a
  real model or a real website; those are replaced with stand-ins, so the whole suite
  runs offline in seconds. A separate, clearly labeled test may hit the real services.
- **Keep the pieces apart:** ingestion, storage, retrieval, generation, comparison,
  and the web app are separate modules that talk through small, documented interfaces.
  That separation is also what makes the comparison honest, because generation can't
  reach the store when retrieval is switched off.
- No dead code, no commented-out code, no duplicated logic.

### Workflow notes for the submission

The brief invites candidates to share how they work. This repo's `CLAUDE.md`, skills,
hooks, and atlas *are* that workflow. Keep them tidy and accurate, because reviewers
may read them.
