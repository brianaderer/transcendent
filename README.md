# transcendent

> A description of the project goes here once there is code.

**Atlas presentation page:** not published yet. The link goes here once the first plan
is drawn.

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

---

## Other things in this repo

- [`CLAUDE.md`](CLAUDE.md) is the set of rules Claude Code follows when working here.
- [`.claude/skills/`](.claude/skills/) holds the Claude Code skills for this project:
  - `/isolate-and-pin` investigates a bug by testing every likely explanation in parallel.
  - `/tdd` takes a single defect from a failing test to a proven fix.
