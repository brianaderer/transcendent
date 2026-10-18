"""Posts that are never stored: removed or deleted ones, and bots (atlas OPEN-14)."""

from voices.ingestion.items import Item

REMOVED_TEXT = {"[deleted]", "[removed]", "[ Removed by Reddit ]"}
DELETED_AUTHOR = "[deleted]"
KNOWN_BOTS = {
    "automoderator",
    "remindmebot",
    "sneakpeekbot",
    "wikisummarizerbot",
    "repostsleuthbot",
}


def is_unwanted(item: Item) -> bool:
    return _is_removed(item) or _is_bot(item.author)


def _is_removed(item: Item) -> bool:
    return item.author == DELETED_AUTHOR or item.body.strip() in REMOVED_TEXT


def _is_bot(author: str) -> bool:
    # Reddit bots almost always say so in their name; a handful of common ones don't end in "bot".
    name = author.lower()
    return name in KNOWN_BOTS or name.endswith("bot")
