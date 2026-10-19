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

### 3.3 Scoping by conversation — turning what Brian says into plates

Brian scopes by talking. He describes what he wants in whatever order it occurs to
him; the agent's job is to break it down into plates without being told how. After
each thing Brian says:

1. **Sort every statement onto the plate it belongs to.** Whole-system shape goes on
   `01`; a part with its own inner workings goes on that part's plate. If no plate
   fits, create one with the next free number in the right area (§3.1) and add it to
   `00-index.md`.
2. **Start broad, split when a box gets crowded.** Everything begins as a box on `01`.
   When Brian has said enough about one box that it needs its own diagram, give it a
   plate, move the detail there, leave the box on `01` with a link to it.
3. **Keep his words and yours apart.** What Brian said is written as specified. Anything
   the agent had to fill in to make the plate coherent is marked as a proposal. Never
   promote a proposal to specified without Brian saying so.
4. **Don't interrupt the flow.** Ambiguities don't stop the conversation. Each one is
   marked `?` on its plate and written up as an `OPEN-N` question (full sentences, §1)
   — with the agent's recommendation. Where something has an obvious default, write the
   default as a proposal instead of asking.
5. **Record decisions as they're made.** When Brian answers an open question, move it to
   Resolved with the date and update every plate it affects.
6. **Commit and reply.** Commit the plates (`Atlas:` message), carry the change into the
   presentation page (§3.2), then answer Brian in a few lines of prose: which plates
   changed, what new open questions there are, and the agent's recommendation on each.

Scope stays with what Brian has said. Don't design ahead of him; a plate with three
specified boxes is better than one with ten guessed ones.

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
| `/commit-chain [sha]` | Runs automatically after every commit (§6): documents the commit's diff in an isolated worktree, lands the documentation commit, then Clean Code reviews both commits. |
| `/document-commit [sha \| from..to]` | By hand, for a range: documents it, then traces everything it touches or is referenced by and updates that documentation too, until nothing reachable is stale. Runs inside `/commit-chain` automatically. Holds every change to the rules in §1, §3, §6 and §7 and the README's *Primary objective*; treats the README's boot steps as the most important document. |
| `/uncle-bob [sha \| from..to]` | Clean Code review (§8) of the source changed by a commit or range, with ranked findings and a concrete fix for each. Runs inside `/commit-chain` automatically; Must-fix findings are fixed before new work. |
| `/refetch-day [YYYY-MM-DD]` | Tests the automated daily retrieval on the running local app: health-checks Celery (worker, a task round trip, Beat), deletes one loaded day and moves the day ledger (the high-water mark) back past it, fires the daily catch-up as Beat would, and confirms the page's loading states, the live events, the embeddings and the model calls until the day settles, timing each stage. Changes only the local database. |
| `/test-boot [ref] [github]` | Plays the reviewer: fresh clone in a blank folder, README boot steps followed exactly, demo checked. Reports success or every friction point with the fix for each. Changes nothing. |

---

## 6. Documentation is part of every code step

The reviewers are very big on documentation. **No code change is finished until its
documentation is.** Documentation is written *with* the code, in the same commit —
not saved for later.

### Where documentation lives

| Place | What it holds |
|---|---|
| The code itself | Self-documenting names and compact functions first (§8). Docstrings on public functions, classes, and modules where the name alone can't say what it promises. Comments only for *why*, never restating *what*. |
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
4. The hooks (below) run **`/commit-chain`** on the new commit.

### The commit chain

`/commit-chain <sha>` composes the documentation pass and the Clean Code review into
one isolated run per commit:

1. **Open a worktree at `<sha>`** (`.chain-worktrees/`, ignored by git). Other work
   going on in the main folder — uncommitted edits, staged files, newer commits —
   never leaks in.
2. **Document the diff.** The `document-commit` agent works only from `<sha>`'s diff,
   traces outward from it, and commits the documentation in the worktree.
3. **Land the documentation commit** on the current branch, committing only its
   documentation files and leaving anything else staged or edited untouched. If those
   same files have local edits, it's parked on the branch `docs-sync/<sha>` instead.
4. **Review exactly two commits** — `<sha>` and its documentation commit — with the
   `uncle-bob` agent. The second matters because documentation passes correct comments
   and docstrings, which the review checks. Skipped if neither commit touches source.
5. **Close the worktree**, run `/test-boot` if boot steps changed, and report.

Must-fix review findings are fixed in the next commit, before new work; that commit
runs the chain again. If the same finding survives two rounds, stop and explain it to
Brian. Two model calls per commit, no more.

### The automatic hook

- **Inside Claude Code:** a `PostToolUse` hook (`.claude/settings.json` →
  `.claude/hooks/claude-post-commit.sh`) notices each successful `git commit` and
  tells Claude to run `/commit-chain <sha>`. When told, run it before making any
  further code change.
- **Outside Claude Code** (a commit from a terminal): the git hook
  `.githooks/post-commit` starts `/commit-chain` headlessly **in the background** and
  returns at once; the log is `.chain-worktrees/logs/<sha>.log`. Enable it once per
  clone with `git config core.hooksPath .githooks`. Skip it for one commit with
  `SKIP_POST_COMMIT_STEPS=1 git commit …` (the older name `SKIP_DOC_SYNC` still works).
- **Tests:** `tests/hooks/test_commit_checks.sh` covers the hook decisions and the
  worktree landing. Run it after any change to `.claude/hooks/` or `.githooks/`.
- **Requirements:** the Claude Code hook needs `jq` on the path; the git hook needs the
  `claude` command and silently does nothing without it. Details in
  `docs/architecture/tooling.md`.

### The loop guard — never weaken it

The chain produces a commit, so without a guard it would trigger itself forever.
Three layers stop that:

1. **Every documentation commit carries a `Docs-Sync: <sha>` trailer**, and landing
   keeps it. Never make a commit with that trailer by hand, and never remove it.
2. **`.claude/hooks/is-skippable-commit.sh` is the single check** used by both hooks
   and the skills. It skips any commit carrying the trailer, and any commit that
   changes only `docs/` and `README.md`.
3. **The git hook also skips** whenever it runs inside a Claude Code session — which
   includes the headless chain's own commits.

Any change to the hooks or the skills must keep all three layers working, and
`tests/hooks/test_commit_checks.sh` must pass.

---

## 7. Rules for the challenge

Some of these come from the challenge brief (summarized in `README.md` → *Primary
objective*); the rest are Brian's decisions or working rules for this project. The
atlas plates hold the detailed decisions.

### The README is the demo

- Reviewers will `git clone`, follow the README **exactly**, and demo the app
  locally. **Every step in the README must work, in order, from a fresh clone on a
  clean machine.** If a change adds a dependency, an environment variable, a service,
  a port, or a setup step, the README changes in the same commit.
- One command to start everything is the goal (for example `docker compose up`, or a
  single `make` target). Every extra manual step is a chance for the demo to fail.
- Secrets never go in the repo. Provide `.env.example` with every variable named and
  explained, and say in the README exactly which keys the reviewer must supply.
- **Before calling boot-affecting work finished, run `/test-boot`.** It clones the
  repo into a blank folder, follows the README exactly as a reviewer would, and
  reports success or every friction point. `/document-commit` runs it automatically
  when a commit changes the boot steps. Run it again before submitting.
- **Submission needs a public repo.** The GitHub repo is private today; making it
  public is Brian's call, and happens only when he says so.

### Comparing with and without retrieval (the A/B test)

The brief asks how a model does at writing the Community Voices Document **without**
retrieval from our own data store, versus **with** it. Treat that comparison as a
core feature, not an afterthought:

- **Both versions are produced by one code path.** A single document generator takes
  a switch: retrieval off (version A, which may read a few of the range's posts, at most
  thirty-five per step, spread evenly over the days and picked without regard to meaning, but cannot search them) or retrieval on
  (version B, which searches our store by meaning; atlas OPEN-39). Everything else — model,
  settings, prompt wording, the week covered, output format — is identical, so the
  only difference between the two documents is the retrieval.
- **Reports are ephemeral.** A comparison run's reports and scores are shown when it
  finishes and are not stored (atlas OPEN-24); they may be made downloadable.
- **The app shows the comparison side by side**, with measurements, not just two
  blocks of text. The document's conclusions are aggregate (which topics, how big,
  which way they're moving), so both versions are scored against one answer key
  computed from the topic and engagement data, not sentence by sentence against
  individual posts (atlas OPEN-21, plate 70):
  - which of the period's real main topics each version found, and which it invented;
  - whether it ranked them in the right order of importance;
  - whether it called each topic's direction (rising, steady, fading) correctly;
  - whether its predictions came true;
  - time taken and tokens used.
- **Measurements are computed by code where possible**, and, where a model is used to
  judge, the judging prompt is saved with the result and is the same for both
  versions.

### Retrieval, ingestion, and visualization

- **Ingestion is automated and repeatable:** posts are fetched and processed day by
  day through one catch-up operation (atlas plate 40); each post or comment is
  embedded whole, once. Fetching the same day twice must not create duplicates.
- **Topics are found thread by thread** (atlas OPEN-29): each thread is encoded as one
  text, its post and its top comments, on day one and again on day three, and the
  tagging agent attaches it to a topic, starts a new one, or calls it noise. Comments
  arriving later, and old threads that come back to life, count as heat. A thread whose
  post we don't have (removed, or older than our history) is tagged from its title and
  comments, counting its days from the first comment we see (OPEN-30).
- **Too much data** is handled as Brian decided (atlas OPEN-14, OPEN-19, OPEN-29): drop
  deleted, removed and bot posts, fold short agreeing replies into their parent's
  upvotes, and delete threads the agent calls noise.
- **Record retrieval statistics:** every time a stored passage is retrieved, count
  it. The app shows which passages are retrieved most.
- **Show a flattened picture of the embeddings:** squash them down to two dimensions
  and plot them, colored by topic or thread, so a reviewer can see how the week's
  conversation clusters.

### Code quality the reviewers asked for

The brief names these explicitly: self-documenting code, unit tests, compact
functions, and Robert C. Martin's *Clean Code* principles. The full guidelines are
§8, and `/uncle-bob` reviews every commit against them. Two project-specific points:

- **Tests never call a real model or a real website;** those are replaced with
  stand-ins, so the whole suite runs offline in seconds. A separate, clearly labeled
  test may hit the real services.
- **Keep the pieces apart:** ingestion, storage, retrieval, generation, comparison,
  and the web app are separate modules that talk through small, documented interfaces.
  That separation is also what makes the comparison honest, because generation can't
  search the store when retrieval is switched off: it only gets the few posts it reads.

### Workflow notes for the submission

The brief invites candidates to share how they work. This repo's `CLAUDE.md`, skills,
hooks, and atlas *are* that workflow. Keep them tidy and accurate, because reviewers
may read them.

---

## 8. Clean Code guidelines

Condensed from Robert C. Martin, *Clean Code* (2008), and applied to every line of
source and test code. `/uncle-bob` reviews each commit against this section
automatically (§6 hooks). The book's central idea: **code is read far more often than
it's written, so optimize for the reader.**

### Names
- A name says what a thing is or does, so it needs no comment. If it needs one, rename.
- Pronounceable and searchable; no abbreviations, no type prefixes (`str_name`), no
  numbered variants (`data2`).
- Classes and data are nouns (`WeeklyDigest`); functions are verbs
  (`fetch_week_of_posts`). One word per concept, used everywhere (not `fetch`, `get`,
  and `retrieve` for the same idea).
- Longer names for wider scope; a loop index can be `i`, a module-level value can't.
- A name mentions side effects: `load_or_create_index`, not `load_index`, if it may
  create.

### Functions
- **Small**: about 20 lines is this repo's working limit; most should be shorter.
- **Do one thing.** If you can extract another function with a name that isn't just a
  restatement of the code, it was doing more than one thing.
- **One level of abstraction per function**, and the file reads top-down like a
  newspaper: high-level functions first, the helpers they call below them (the
  *stepdown rule*).
- **Arguments**: zero to two; three needs a reason; more means group them into an
  object. **No true/false flag arguments** — write two functions. No output arguments.
- **No hidden side effects.** A function either does something or answers a question
  — not both (*command–query separation*).
- **Don't repeat yourself.** Duplication is the root problem the other rules attack.

### Comments
- A comment explaining *what* the code does is a failure to make the code say it.
  Rename or extract instead.
- Good comments: *why* (intent, a non-obvious decision), warnings of consequences,
  `TODO` with an owner, docstrings on public interfaces (§6).
- Never: redundant comments, misleading or stale comments, change logs in comments
  (git has the history), commented-out code.

### Formatting
- Related code sits close together; a function sits just below the one that calls it.
- One concept per paragraph of code, separated by a blank line.
- One formatter and one linter per language, configured in the repo, run in CI.

### Objects and data
- Objects hide their data and expose behavior; plain data structures expose data and
  have no behavior. Don't build hybrids that do half of each.
- Talk to friends, not strangers: avoid chains like `a.b().c().d()` (the *Law of
  Demeter*).

### Errors
- Raise exceptions; don't return error codes or `None` to mean failure.
- Keep error handling apart from the main logic — a `try` block calls one function.
- Never swallow an exception silently.
- Don't return or pass `None` where a value is expected: return an empty list, a
  special-case object, or raise.
- Wrap third-party libraries (the model provider, the vector store, the crawler) behind
  our own small interface, so the rest of the code doesn't depend on their quirks — and
  so tests can swap them for stand-ins.

### Tests
- **Test first** (`/tdd`): write a failing test, make it pass, then clean up.
- Tests are **F.I.R.S.T.**: Fast, Independent of each other, Repeatable anywhere
  (offline), Self-checking (pass or fail, no reading output), Timely (written with the
  code).
- One idea per test, and the test name says what it proves.
- Test the boundaries: empty input, one item, the maximum, the week edges.
- Test code is held to the same standard as production code.

### Classes and modules
- Small, with **one reason to change** (*single responsibility*).
- High-level logic depends on small interfaces, not on concrete details (*dependency
  inversion*) — the generator depends on "something that retrieves passages", not on
  Postgres.
- Add behavior by adding code, not by editing a growing `if/else` (*open–closed*).

### The rules of simple design (Kent Beck, quoted in the book), in priority order
1. All the tests pass.
2. No duplication.
3. The code says what it means.
4. As few classes and functions as possible, once the first three hold.

### Smells to watch for (from the book's chapter 17)
Dead code, commented-out code, duplication, magic numbers (use named constants),
negative conditionals (`if not is_not_ready`), long argument lists, flag arguments,
code at the wrong level of abstraction, a function more interested in another
module's data than its own, calls that must happen in a hidden order, configuration
buried deep instead of kept at the top, and building or testing that takes more than
one command.

### The Boy Scout rule
Leave the code a little cleaner than you found it — in the code you're already
touching, without wandering into unrelated refactors (§2 scope).

