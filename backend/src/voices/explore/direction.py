"""A topic's measured direction over a range (atlas plate 31): the Explore page's badge."""

from datetime import date
from typing import Literal

Direction = Literal["new", "rising", "steady", "fading"]

CHANGE_THAT_COUNTS = 0.25  # up or down by more than a quarter against the period before


def direction(first_seen: date, start: date, now: int, before: int) -> Direction:
    """New if the topic was first seen inside the range; otherwise how the range's engagement
    (`now`) compares with the period of the same length just before it (`before`)."""
    if first_seen >= start:
        return "new"
    if now > before * (1 + CHANGE_THAT_COUNTS):
        return "rising"
    if now < before * (1 - CHANGE_THAT_COUNTS):
        return "fading"
    return "steady"
