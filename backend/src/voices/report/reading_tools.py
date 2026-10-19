"""Version A's one tool (atlas plate 60, OPEN-39): reading posts, with no retrieval by meaning.

`read_posts` hands back whole posts written in the window, a few at a time, in a fixed shuffle
of the run's own (never ranked by relevance), up to a budget per phase so the agent can't keep
reading in a loop. The budget is shared out evenly over the window's days, and a day's share
can't be overspent, so the reads cover the whole period (Brian: the model, left to itself,
spent them on the first two days). Reads aren't retrieval, so they aren't counted as
retrievals (OPEN-12), and like version B's tools they see only their window: for the
prediction, the days before the range.
"""

import json
from collections.abc import Sequence
from datetime import date
from typing import Protocol

from voices.explore.day_range import DayRange
from voices.report.tools import ToolResult, said

READ_BATCH = 5  # posts handed back by one read
READ_BUDGET = 35  # posts one phase may read in all (atlas OPEN-39)
READ_POSTS = "read_posts"
NOTHING_LEFT_TO_READ = "No posts left to read; answer now with what you have."


class PostReader(Protocol):
    def sample_posts(
        self, days: DayRange, limit: int, seed: str, exclude_ids: Sequence[str]
    ) -> list[dict]: ...


class ReadingTools:
    def __init__(self, reader: PostReader, window: DayRange, seed: str):
        self.reader = reader
        self.window = window
        self.seed = seed  # the run's, so the same run reads the same posts
        self.ids_given: list[str] = []
        self.shares_left = _even_shares(window)

    @property
    def schemas(self) -> list[dict]:
        return READING_SCHEMAS

    def run(self, name: str, arguments: dict) -> ToolResult:
        if name != READ_POSTS:
            return said(f"There is no tool named {name}; use {READ_POSTS}.")
        if not any(self.shares_left.values()):
            return said(NOTHING_LEFT_TO_READ)
        try:
            day = self._day_to_read(arguments.get("day"))
        except ValueError as reason:
            return said(str(reason))
        return self._read(day)

    def _day_to_read(self, day: str | None) -> date:
        """The day asked for, or else the one with the most of its share left (earliest first);
        raises ValueError naming what's wrong."""
        if day is None:
            return max(self.shares_left, key=self.shares_left.__getitem__)
        try:
            asked = date.fromisoformat(day)
        except ValueError:
            raise ValueError(f"'{day}' is not a date; give the day as YYYY-MM-DD.") from None
        if asked not in self.window:
            raise ValueError(
                f"{asked} is outside what you can see: {self.window.start} to {self.window.end}."
            )
        if not self.shares_left[asked]:
            raise ValueError(f"You have read your share of {asked}; read {self._unread_days()}.")
        return asked

    def _unread_days(self) -> str:
        days = [day.isoformat() for day, left in self.shares_left.items() if left]
        return "one of " + ", ".join(days)

    def _read(self, day: date) -> ToolResult:
        limit = min(READ_BATCH, self.shares_left[day])
        posts = self.reader.sample_posts(DayRange(day, day), limit, self.seed, self.ids_given)
        self._spend_share(day, limit, len(posts))
        if not posts:
            return said(f"No more posts on {day}.")
        post_ids = [post["post_id"] for post in posts]
        self.ids_given.extend(post_ids)
        return ToolResult(json.dumps(posts, default=str), post_ids)

    def _spend_share(self, day: date, asked_for: int, found: int) -> None:
        if found < asked_for:  # a quiet day has nothing more to give
            self.shares_left[day] = 0
        else:
            self.shares_left[day] -= found


def _even_shares(window: DayRange) -> dict[date, int]:
    """READ_BUDGET split over the window's days, the first few taking one more if it doesn't
    divide evenly."""
    each, extra = divmod(READ_BUDGET, window.length)
    return {day: each + (n < extra) for n, day in enumerate(window.days())}


READING_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": READ_POSTS,
            "description": f"Read up to {READ_BATCH} r/sailing posts and comments written in "
            "the period you can see, in full, with their authors, dates and thread titles. "
            "Each read gives posts from one day, in no particular order, ones you haven't "
            f"seen; you may read {READ_BUDGET} in all, shared evenly over the days, so each "
            "day has its own share. Leave out the day to read the next day in turn, or give "
            "a day (YYYY-MM-DD) to read that day's share.",
            "parameters": {
                "type": "object",
                "properties": {"day": {"type": "string", "description": "YYYY-MM-DD"}},
            },
        },
    },
]
