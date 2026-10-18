# transcendent

> A description of the project goes here once there is code.

**Atlas:** not published yet. The link goes here once the first plan is drawn.

Plans and design for this project live in the **atlas**: `docs/atlas/atlas.html`.

---

## What the atlas is

The atlas is a single interactive web page that shows how the system is put together
and how it's planned to work. It works like an exploded-view diagram, the kind that
shows a machine whole and then lets you pull each part out to see what's inside.

- **The front view is the system map.** Every major part of the system is a box,
  grouped into labeled lanes, with arrows showing how the parts talk to each other.
- **Click any box to open its plate.** A plate is the breakout for that one part. It
  has its own diagram of what's inside, a short explanation, and a row of facts such as
  which source files it lives in and what limits or settings matter.
- **Keep clicking to go deeper.** Inside a plate, a box with a highlighted outline has
  a plate of its own; click it to drill down another level. A back button takes you up
  the way you came. You can go from the whole system down to a single step and back
  without leaving the page.
- **Jump straight to a plate** with the buttons across the top of the page, or by
  sharing a link that ends in the plate's name, such as `atlas.html#ratify`.

### Reading the diagrams

Every plate uses the same visual language, and shows a key:

- **The color of a box says what it is:** a call to an AI model, a tool, a separate
  service or job queue, a place data is stored, a screen in the app, or a final result.
- **The style of a line says how things move:**
  - A solid line is a plain call from one part to the next.
  - A dotted line is a step that only happens under some condition.
  - A dashed line in the model color is a loop that repeats a limited number of times.
  - A heavy dashed line is a part that calls itself again from the top.
- **A box with a dashed outline is proposed but not decided yet.** It has a matching
  entry on the open questions list.
- **Where the system behaves differently in different modes,** a switch at the top
  lights up the path each mode takes. The boxes on that path are numbered in the order
  a request travels through them, and a row of numbered buttons under the map steps
  through it.

The working example to compare against is the
[Vintly Flow Atlas](https://claude.ai/artifact/PPfWjhKfmb6zXUoA6H5xSJ).

---

## How to open it

- **The easiest way is the published link** at the top of this README. It's a private
  page on claude.ai that always shows the latest version.
- **From a checkout, open `docs/atlas/atlas.html` in any browser.** It's one
  self-contained file with no setup and no server.
- On GitHub, the file shows as code rather than as the page, so use one of the two
  options above.

## Decisions and open questions

[`docs/atlas/90-open-questions.md`](docs/atlas/90-open-questions.md) has two tables:

- **The first lists what's still undecided,** and names the plate each question
  affects.
- **The second, "Resolved",** lists what has been decided, and when.

If something on a plate looks odd, check whether it's waiting on an open question or
was changed by a recent decision.

## Seeing how a plan changed

Every atlas change is committed on its own, with a message starting `Atlas:`:

```bash
git log --oneline -- docs/atlas/
git log -p -- docs/atlas/atlas.html
```

## How to add to the atlas

The rules are in [`CLAUDE.md`](CLAUDE.md), section 3. In short, the diagrams are stored
as tables of boxes, arrows and plates inside the page, and the page draws itself from
those tables. Changing a plan means editing rows. Every box that has a plate must be
listed as drillable. After each change, commit it and republish to the same link.

---

## Other things in this repo

- [`CLAUDE.md`](CLAUDE.md) is the set of rules Claude Code follows when working here.
- [`.claude/skills/`](.claude/skills/) holds the Claude Code skills for this project:
  - `/isolate-and-pin` investigates a bug by testing every likely explanation in parallel.
  - `/tdd` takes a single defect from a failing test to a proven fix.
