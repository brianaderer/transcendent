"""A thread as the tagging step sees it: one text, its post and its best-scored replies, so
the comments' meaning counts but generic replies don't drown the post (atlas OPEN-29)."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

TOP_REPLIES_IN_THREAD_TEXT = 5
THREAD_TEXT_CHARACTERS = 3000


class Scored(Protocol):
    body: str
    score: int


@dataclass(frozen=True)
class Reply:
    body: str
    score: int


@dataclass(frozen=True)
class DueThread:
    """A thread on its first or third day, with the replies it has so far."""

    source_id: str
    post: str  # the post's title and text
    replies: list[Reply]


def thread_text(post: str, replies: Sequence[Scored]) -> str:
    best = sorted(replies, key=lambda reply: -reply.score)[:TOP_REPLIES_IN_THREAD_TEXT]
    return "\n\n".join([post, *(reply.body for reply in best)])[:THREAD_TEXT_CHARACTERS]
