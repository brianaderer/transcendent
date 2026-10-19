"""A topic's measured direction over a range (atlas plate 31): the Explore page's badge."""

from datetime import date
from typing import Literal

from voices.explore.day_range import DayRange

Direction = Literal["new", "rising", "steady", "fading"]

CHANGE_THAT_COUNTS = 0.25  # up or down by more than a quarter against the period before


def is_new(first_seen: date, days: DayRange) -> bool:
    """First seen inside the range (or after it began)."""
    return first_seen >= days.start


def direction(new: bool, now: int, before: int) -> Direction:
    """New, or how the range's engagement (`now`) compares with the period of the same length
    just before it (`before`)."""
    if new:
        return "new"
    if now > before * (1 + CHANGE_THAT_COUNTS):
        return "rising"
    if now < before * (1 - CHANGE_THAT_COUNTS):
        return "fading"
    return "steady"
