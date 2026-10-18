# transcendent

> A description of the project goes here once there is code.

Plans and design for this project live in the **atlas**, in [`docs/atlas/`](docs/atlas/00-index.md).

---

## What an atlas file is

An atlas is a set of short documents that together describe how the system is put
together and how it's planned to work. Like the pages of a printed atlas, each one
covers a single area. Each document is called a **plate**.

A plate is one markdown file about one subject. That might be the overall map of the
system, one part of it, how code gets from a laptop to production, or the layout of
the database. A plate usually has a diagram plus the prose that explains it: the
diagram shows the shape of things, and the prose says why it's shaped that way.

The atlas is the single place where plans are written down. A plan discussed in a
chat or a meeting doesn't count until it's in a plate.

### How plates are numbered

Each plate's number tells you where it belongs:

| Number | What lives there |
|---|---|
| `00` | The index: a table of every plate, with one line on what each shows |
| `01`–`09` | Plates about the whole system, such as the system map, environments, or how code is delivered |
| `10`–`89` | One block of ten per area. For example, `20`–`29` might be the data model and `30`–`39` the user interface. An area with several plates gets its own folder, such as `20-data-model/21-users.md` |
| `90` | Open questions: decisions still waiting to be made, and a record of decisions already made |

### Markings you'll see

- **`(DRAFT)`** in a plate's title means the plate is still being worked out. Read it
  as a proposal, not a settled design.
- **`?`** inside a plate marks a single detail that isn't decided yet. Each one is
  listed in a short "Open in this draft" section on that plate.
- **`OPEN-12`** (or any `OPEN-` number) refers to a question on the open questions
  plate. Look it up there to see what's being asked and whether it has been answered.

---

## How to read the atlas

1. **Start at the index**, [`docs/atlas/00-index.md`](docs/atlas/00-index.md). It lists
   every plate and says in one line what each covers. Pick the plate for the area you
   care about.
2. **If you're new, read the low-numbered plates first.** The `01`–`09` plates give the
   big picture, and the later plates assume you have it.
3. **Every plate links back to the index** at the top, so you can always get back to
   the full list.
4. **Check open questions before relying on a detail.**
   [`90-open-questions.md`](docs/atlas/90-open-questions.md) has two tables. The first
   lists what's still undecided, and links each question to the plate it affects. The
   second, "Resolved", lists what has been decided and when. If something on a plate
   looks odd, check whether it's waiting on an open question or was changed by a
   recent decision.
5. **Use a viewer that draws diagrams.** The diagrams are written in Mermaid, a plain
   text format that some viewers turn into pictures. GitHub draws them automatically
   when you open a plate in the browser. In VS Code, the built-in markdown preview
   (Cmd+Shift+V) draws them once you install a Mermaid preview extension. In a plain
   text editor, they show up as text.
6. **To see how a plan changed over time**, read the git history of the plate. Atlas
   changes are committed separately, with messages that start with `Atlas:`:
   ```bash
   git log --oneline -- docs/atlas/
   git log -p -- docs/atlas/21-users.md     # every change to one plate
   ```

## How to add to the atlas

The rules are in [`CLAUDE.md`](CLAUDE.md), section 3. In short: one subject per plate,
numbered by area. Each plate opens with a numbered title and a link back to the index,
and gets a row in the index. Anything undecided goes on the open questions plate as a
full-sentence question.

---

## Other things in this repo

- [`CLAUDE.md`](CLAUDE.md) is the set of rules Claude Code follows when working here.
- [`.claude/skills/`](.claude/skills/) holds the Claude Code skills for this project:
  - `/isolate-and-pin` investigates a bug by testing every likely explanation in parallel.
  - `/tdd` takes a single defect from a failing test to a proven fix.
