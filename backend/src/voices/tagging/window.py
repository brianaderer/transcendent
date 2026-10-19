"""A thread's three days: it is decided on its first day and again on its third (atlas
OPEN-29), and the agent's searches look across the three days ending today."""

from datetime import date, timedelta

THREAD_DAYS = 3


def window_start(day: date) -> date:
    """The first of the three days ending on `day`: the day the threads decided a second
    time today were first seen."""
    return day - timedelta(days=THREAD_DAYS - 1)


def third_day(first_seen_on: date) -> date:
    """The day a thread first seen on `first_seen_on` is decided the second and last time."""
    return first_seen_on + timedelta(days=THREAD_DAYS - 1)
