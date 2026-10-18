# transcendent — Community Voices

Our solution to the Transcendent Endeavors 2026 engineering code challenge.

## Primary objective

**Build a web or mobile app that produces a *Community Voices Document* for one
active online community. The document covers what the community talked about in the
past week and predicts what it will talk about in the coming week. It's written with
help from our own searchable store of the community's posts. The app also shows, side
by side, how the same document turns out when a language model writes it without that
store.**

### What the brief requires

1. **Pick a community** with an online presence active enough to have frequent
   discussion every week. The brief's examples are the Argentine tango community, indie
   game makers on Discord, and Redditors who make fantasy maps; any active community is
   allowed.
2. **Generate the Community Voices Document**: last week's discussion and next week's
   predicted discussion, as a web page, Word document, slide deck, or any text and
   visual format.
3. **Use retrieval to power the document.** Retrieval-augmented generation means the
   model is handed relevant passages pulled from our own data before it writes. The
   brief suggests:
   - storing the passages in a vector database, or a table with vector search in a
     relational database such as Postgres;
   - showing a flattened, two-dimensional picture of the stored embeddings (the
     numeric fingerprints used for similarity search);
   - keeping statistics on which passages get retrieved most.
4. **Fill the data store automatically** with the community's posts, for example with
   web crawlers or agent-driven workflows that collect each week's data. Have a plan
   for handling too much data.
5. **Compare with and without retrieval.** Show how a model writes the document on
   its own, how our retrieval-powered system writes it, and present the comparison
   inside the app.

### How it will be judged

- Reviewers will `git clone` this repo, **follow this README's install and run
  instructions exactly**, and demo the app running locally to their engineering team.
  The instructions below must work from a fresh clone.
- Any front-end and back-end technology and any tools are allowed. The brief says
  there are no tricks, and suggests a couple of hours of work.
- The reviewers value **self-documenting code, unit tests, compact functions, and
  Robert C. Martin's *Clean Code***.
- Optional: share the output of Claude Code's `/insights` command and other parts of
  our coding workflow. This repo's `CLAUDE.md`, skills, hooks, and atlas are that
  workflow.
- Submission is a link to the **public** GitHub repo, emailed to jobs@t19s.com.

## Install and run

Everything runs inside Docker, so Docker is the only thing you need to install.

### 1. Install Docker

- **macOS:** install [Docker Desktop for Mac](https://docs.docker.com/desktop/setup/install/mac-install/)
  (choose the Apple silicon or Intel download to match your Mac), open it once, and
  wait until it says Docker is running.
- **Windows:** install [Docker Desktop for Windows](https://docs.docker.com/desktop/setup/install/windows-install/),
  open it once, and wait until it says Docker is running.
- **Linux:** install [Docker Engine](https://docs.docker.com/engine/install/) for your
  distribution, including the Compose plugin.

Check that both Docker and Docker Compose are installed:

```bash
docker --version
docker compose version
```

You should see a version number from each, such as `Docker version 27.5.1` and
`Docker Compose version v2.32.4`.

### 2. Check that Docker can run a container

```bash
docker run --rm hello-world
```

You should see `Hello from Docker!` followed by a short explanation. If you see
`Cannot connect to the Docker daemon` instead, Docker isn't running yet: open Docker
Desktop (or on Linux run `sudo systemctl start docker`) and try again.

### 3. Add the API key

The app's AI models are reached through [OpenRouter](https://openrouter.ai), which
needs one key. **The key is in the email that submitted this repo.** You don't need
to create an OpenRouter account.

From the folder you cloned this repo into, copy the example settings file and paste
the key into it:

```bash
cp .env.example .env
```

Open `.env` in any text editor and set the key on the `OPENROUTER_API_KEY=` line,
with no spaces or quotes:

```
OPENROUTER_API_KEY=sk-or-v1-...
```

The `.env` file stays on your machine. Git is set to ignore it, so the key can't be
committed by accident.

### 4. Start the app

> The app isn't built yet. When it is, this step will be a single command, run from
> the folder you cloned this repo into.

**Atlas presentation page:** [https://claude.ai/artifact/VUfVs6dZ9gjBJFKwE1enLJ](https://claude.ai/artifact/VUfVs6dZ9gjBJFKwE1enLJ) (private; the clickable view of the plan).

Plans and design for this project live in the **atlas**, in
[`docs/atlas/`](docs/atlas/00-index.md).

---

## What the atlas is

The atlas is where every plan for this project is written down. It has two layers that
always say the same thing.

**1. The plates: the written plan.** A plate is a short markdown document about one
part of the system: the overall map, one module, how code gets to production, the
layout of the database. Each plate has a diagram and the prose that explains it. The
plates are the source of truth. Every decision is written in a plate first, and if
anything else disagrees with a plate, the plate wins.

**2. The presentation page: the plan you can click through.** `docs/atlas/atlas.html`
is a single interactive web page built from the plates. It works like an exploded-view
diagram, the kind that shows a machine whole and then lets you pull each part out to
see what's inside:

- **The front view is the system map.** Every major part of the system is a box,
  grouped into labeled lanes, with arrows showing how the parts talk to each other.
- **Click any box to open its plate**: that part's own diagram, a short explanation,
  and a row of facts such as which source files it lives in and what limits matter.
- **Keep clicking to go deeper.** Inside a plate, a box with a highlighted outline has
  a plate of its own; click it to drill down another level. A back button takes you up
  the way you came.
- **Jump straight to a plate** with the buttons across the top, or with a link ending
  in the plate's number, such as `atlas.html#21`.

The page adds nothing that isn't in the plates. It's a way of looking at them.

---

## Reading the plates

### How plates are numbered

| Number | What lives there |
|---|---|
| `00` | The index: a table of every plate, with one line on what each shows |
| `01`–`09` | Plates about the whole system. `01` is always the system map |
| `10`–`89` | One block of ten per area. For example, `20`–`29` might be the data model and `30`–`39` the user interface. An area with several plates gets its own folder, such as `20-data-model/21-users.md` |
| `90` | Open questions: decisions still waiting to be made, and a record of decisions already made |

### Markings you'll see

- **`(DRAFT)`** in a plate's title means the plate is still being worked out. Read it
  as a proposal, not a settled design.
- **`?`** inside a plate marks one detail that isn't decided yet. Each one is listed in
  a short "Open in this draft" section on that plate.
- **`OPEN-12`** (or any `OPEN-` number) refers to a question on the open questions
  plate. Look it up there to see what's being asked and whether it's been answered.

### Where to start

1. **Start at the index**, [`docs/atlas/00-index.md`](docs/atlas/00-index.md), and pick
   the plate for the area you care about.
2. **If you're new, read `01`, the system map, first.** Later plates assume you've seen
   the big picture.
3. **Every plate links back to the index** at the top.
4. **Check open questions before relying on a detail.**
   [`90-open-questions.md`](docs/atlas/90-open-questions.md) has two tables. The first
   lists what's still undecided, with a link to the plate each question affects. The
   second, "Resolved", lists what has been decided and when.

Plates read fine on GitHub, which also draws their diagrams. The diagrams on GitHub
are pictures only, though. For the clickable version, use the presentation page.

## Opening the presentation page

- **The easiest way is the published link** at the top of this README. It's a private
  page on claude.ai that always shows the latest version.
- **From a checkout, open `docs/atlas/atlas.html` in any browser.** It's one
  self-contained file with no setup and no server.
- On GitHub, the file shows as code rather than as the page, so use one of the options
  above.

### Reading the page's diagrams

Every view uses the same visual language, and shows a key:

- **The color of a box says what it is:** a call to an AI model, a tool, a separate
  service or job queue, a place data is stored, a screen in the app, or a final result.
- **The style of a line says how things move:**
  - A solid line is a plain call from one part to the next.
  - A dotted line is a step that only happens under some condition.
  - A dashed line in the model color is a loop that repeats a limited number of times.
  - A heavy dashed line is a part that calls itself again from the top.
- **A box with a dashed outline is proposed but not decided,** and has a matching open
  question.
- **Where the system behaves differently in different modes,** a switch at the top
  lights up the path each mode takes, numbered in the order a request travels.

The working example to compare against is the
[Vintly Flow Atlas](https://claude.ai/artifact/PPfWjhKfmb6zXUoA6H5xSJ).

---

## Seeing how a plan changed

Every atlas change is committed on its own, with a message starting `Atlas:`:

```bash
git log --oneline -- docs/atlas/
git log -p -- docs/atlas/21-users.md     # every change to one plate
```

## How to add to the atlas

The rules are in [`CLAUDE.md`](CLAUDE.md), section 3. In short:

- Change the plate first, then carry the change into the page. Never change the page on
  its own.
- When a box in a diagram has its own plate, link to that plate from the box. The page
  turns those links into drill-downs.
- Add every new plate to the index.
- Write anything undecided as a full-sentence question on the open questions plate.
- Commit, then republish the page to the same link.

Most plates are written while Brian describes what he wants in conversation. Claude
sorts each thing he says onto the plate it belongs to, starting with boxes on the
system map and giving a box its own plate once there is enough detail to need one.
What Brian said is written as specified; anything Claude filled in is marked as a
proposal, and anything unclear becomes an open question with Claude's recommendation
rather than a pause in the conversation. The full steps are in `CLAUDE.md` §3.3.

---

## Other things in this repo

- [`CLAUDE.md`](CLAUDE.md) is the set of rules Claude Code follows when working here.
- [`.claude/skills/`](.claude/skills/) holds the Claude Code skills for this project:
  - `/isolate-and-pin` investigates a bug by testing every likely explanation in parallel.
  - `/tdd` takes a single defect from a failing test to a proven fix.
  - `/commit-chain` runs automatically after every commit that changes more than
    documentation. It works on that one commit in a separate checkout, so nothing
    else you are doing in the repo folder gets mixed in. First it documents the
    commit (`/document-commit`), then adds that documentation commit to your branch
    without touching anything else you have staged or edited, then reviews both
    commits for clean code (`/uncle-bob`). Inside Claude Code it needs `jq`
    installed. To enable it for commits made outside Claude Code, run
    `git config core.hooksPath .githooks` once after cloning; that hook also needs the
    `claude` command, and it runs the chain in the background, writing its output to
    `.chain-worktrees/logs/<commit>.log`. How it all fits together is in
    [`docs/architecture/tooling.md`](docs/architecture/tooling.md).
  - `/document-commit` documents a commit or a range of commits and follows every
    reference outward, updating anything the change made stale. The chain runs it
    for you; run it by hand to document a range.
  - `/uncle-bob` reviews code against Robert C. Martin's *Clean Code*: clear names,
    small single-purpose functions, few arguments, honest comments, proper error
    handling, and tests. It lists what to fix and how. The chain runs it for you;
    run it by hand to review any commit or range. The guidelines are summarized in
    [`CLAUDE.md`](CLAUDE.md), section 8.
    The scripts these hooks rely on have their own offline tests: run
    `tests/hooks/test_commit_checks.sh` from the repo folder, and it should end with
    `all tests passed`.
  - `/test-boot` checks this README's install and run steps the way you'll use them.
    It clones the repo into an empty folder, follows those steps exactly, tries the
    demo, and reports anything that failed or was harder than it should be. Details
    are in [`docs/architecture/tooling.md`](docs/architecture/tooling.md).
- [`docs/architecture/`](docs/architecture/README.md) describes how the code is
  actually built, one document per module.
- [`design/`](design/) holds mockups of the app's screens, made in Claude Design from
  the design brief on [atlas plate 31](docs/atlas/30-frontend/31-screens.md). Open
  `design/Community Voices Screens.html` in a browser to see them. They are a proposal
  for review, not the built app.
