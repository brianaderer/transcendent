"""The three-day window a post has to fall into a cluster (atlas OPEN-14)."""

from datetime import date, timedelta

LOOKAHEAD_DAYS = 3


def window_start(day: date) -> date:
    """The first day of the window that ends on `day`."""
    return day - timedelta(days=LOOKAHEAD_DAYS - 1)
