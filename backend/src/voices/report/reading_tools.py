"""Version A's one tool (atlas plate 60, OPEN-39): reading posts, with no retrieval by meaning.

`read_posts` hands back whole posts written in the window, a few at a time, in a fixed shuffle
of the run's own (never ranked by relevance), up to a budget per phase so the agent can't keep
reading in a loop. Reads aren't retrieval, so they aren't counted as retrievals (OPEN-12), and
like version B's tools they see only their window: for the prediction, the days before the
range.
"""

import json
from collections.abc import Sequence
from datetime import date
from typing import Protocol

from voices.explore.day_range import DayRange
from voices.report.tools import ToolResult, said

READ_BATCH = 5  # posts handed back by one read
READ_BUDGET = 10  # posts one phase may read in all
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

    @property
    def schemas(self) -> list[dict]:
        return READING_SCHEMAS

    def run(self, name: str, arguments: dict) -> ToolResult:
        if name != READ_POSTS:
            return said(f"There is no tool named {name}; use {READ_POSTS}.")
        if len(self.ids_given) >= READ_BUDGET:
            return said(NOTHING_LEFT_TO_READ)
        try:
            days = self._days_asked(arguments.get("day"))
        except ValueError as reason:
            return said(str(reason))
        return self._read(days)

    def _days_asked(self, day: str | None) -> DayRange:
        """The whole window, or the one day asked for; raises ValueError naming what's wrong."""
        if day is None:
            return self.window
        try:
            asked = date.fromisoformat(day)
        except ValueError:
            raise ValueError(f"'{day}' is not a date; give the day as YYYY-MM-DD.") from None
        if asked not in self.window:
            raise ValueError(
                f"{asked} is outside what you can see: {self.window.start} to {self.window.end}."
            )
        return DayRange(asked, asked)

    def _read(self, days: DayRange) -> ToolResult:
        limit = min(READ_BATCH, READ_BUDGET - len(self.ids_given))
        posts = self.reader.sample_posts(days, limit, self.seed, self.ids_given)
        if not posts:
            return said("No more posts in that period.")
        post_ids = [post["post_id"] for post in posts]
        self.ids_given.extend(post_ids)
        return ToolResult(json.dumps(posts, default=str), post_ids)


READING_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": READ_POSTS,
            "description": f"Read up to {READ_BATCH} r/sailing posts and comments written in "
            "the period you can see, in full, with their authors, dates and thread titles. "
            "They come in no particular order, and each read gives ones you haven't seen; "
            f"you may read {READ_BUDGET} in all. Give a day (YYYY-MM-DD) to read only that "
            "day's.",
            "parameters": {
                "type": "object",
                "properties": {"day": {"type": "string", "description": "YYYY-MM-DD"}},
            },
        },
    },
]
