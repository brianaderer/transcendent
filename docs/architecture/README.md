# Architecture — as built

How the code is **actually built**, one document per module. Plans for what *should*
be built live in the [atlas](../atlas/00-index.md). These documents describe what
*is*, and `/document-commit` keeps them in step with every commit.

Each module document follows the template in [`CLAUDE.md`](../../CLAUDE.md) §6:
purpose, public interface, how it works, what it uses, what uses it, and its
configuration and data.

| Module | Source | What it does |
|---|---|---|
| [tooling](tooling.md) | `.claude/`, `.githooks/` | Commit hooks, loop guard, and the `/document-commit` skill and agent that keep documentation in step with every commit; the `/test-boot` skill and agent that follow the README from a fresh clone the way a reviewer will |
