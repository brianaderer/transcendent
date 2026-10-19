"""Posts that are never stored: removed or deleted ones, and bots (atlas OPEN-14)."""

from voices.ingestion.items import Item

REMOVED_TEXT = {"[deleted]", "[removed]", "[ Removed by Reddit ]"}
DELETED_AUTHOR = "[deleted]"
BOTS_NOT_NAMED_BOT = {"automoderator"}


def is_unwanted(item: Item) -> bool:
    return _is_removed(item) or _is_bot(item.author)


def _is_removed(item: Item) -> bool:
    return item.author == DELETED_AUTHOR or item.text.strip() in REMOVED_TEXT


def _is_bot(author: str) -> bool:
    name = author.lower()
    return name.endswith("bot") or name in BOTS_NOT_NAMED_BOT
