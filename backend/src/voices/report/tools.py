"""The report agent's tools for version B (atlas plate 60): search, lookup, topic trends and
upcoming events. Version A gets none of them, so it can't reach the store (CLAUDE.md §7).

Every post they return is counted as the report agent's retrieval (atlas OPEN-12). They see
only their window: for the prediction, the days before the range, so it can't peek inside.
"""

import json
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from voices.db.tagging_store import PostNotFound
from voices.explore.day_range import DayRange

SEARCH_RESULTS = 20
EVENT_RESULTS = 15
# What a post announcing a dated plan reads like, for the upcoming-events search.
UPCOMING_EVENTS_QUERY = "an upcoming regatta, race, boat show, festival or meetup on a coming date"
# Each tool's one required argument (None for tools that take none); tool `x` runs `_x`.
TOOL_ARGUMENT = {
    "search": "term",
    "lookup": "post_id",
    "topic_trends": None,
    "upcoming_events": None,
}


class ReportStore(Protocol):
    def search_posts(
        self, embedding: Sequence[float], first_day: date, last_day: date, limit: int
    ) -> list[dict]: ...
    def lookup_post(self, post_id: str) -> dict: ...
    def record_retrievals(
        self, post_ids: Sequence[str], run: str, agent: str, tool: str
    ) -> None: ...


class QueryEmbedder(Protocol):
    def embed_query(self, text: str) -> list[float]: ...


@dataclass(frozen=True)
class ToolResult:
    text: str  # what the agent reads back
    post_ids: list[str]  # the posts it returned, for the live events


class ReportTools:
    def __init__(
        self,
        store: ReportStore,
        embedder: QueryEmbedder,
        window: DayRange,
        run_name: str,
        trends: Callable[[], list[dict]],
    ):
        self.store = store
        self.embedder = embedder
        self.window = window
        self.run_name = run_name
        self.trends = trends

    def run(self, name: str, arguments: dict) -> ToolResult:
        if name not in TOOL_ARGUMENT:
            return _said(f"There is no tool named {name}; use {', '.join(TOOL_ARGUMENT)}.")
        needed = TOOL_ARGUMENT[name]
        if needed and needed not in arguments:
            return _said(f"Tool {name} needs the argument '{needed}'.")
        return getattr(self, f"_{name}")(arguments)

    def _search(self, arguments: dict) -> ToolResult:
        return self._posts_like(arguments["term"], SEARCH_RESULTS, "search")

    def _upcoming_events(self, _arguments: dict) -> ToolResult:
        return self._posts_like(UPCOMING_EVENTS_QUERY, EVENT_RESULTS, "search")

    def _lookup(self, arguments: dict) -> ToolResult:
        post_id = arguments["post_id"]
        try:
            post = self.store.lookup_post(post_id)
        except PostNotFound:
            return _said(f"There is no post with id {post_id}; ids come from search results.")
        if post["date"] > self.window.end:
            return _said(
                f"Post {post_id} was written after {self.window.end}, past what you can see."
            )
        self._count([post_id], "lookup")
        return ToolResult(json.dumps(post, default=str), [post_id])

    def _topic_trends(self, _arguments: dict) -> ToolResult:
        return ToolResult(json.dumps(self.trends(), default=str), [])

    def _posts_like(self, text: str, limit: int, tool: str) -> ToolResult:
        embedding = self.embedder.embed_query(text)
        hits = self.store.search_posts(embedding, self.window.start, self.window.end, limit)
        post_ids = [hit["post_id"] for hit in hits]
        self._count(post_ids, tool)
        return ToolResult(json.dumps(hits, default=str), post_ids)

    def _count(self, post_ids: list[str], tool: str) -> None:
        if post_ids:
            self.store.record_retrievals(post_ids, self.run_name, "report", tool)


def _said(text: str) -> ToolResult:
    return ToolResult(text, [])


# The schemas the model sees; they must match TOOL_ARGUMENT.
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Find r/sailing posts and comments in the period you can see that are "
            "closest in meaning to a term. Returns ids, authors, dates, thread titles and text.",
            "parameters": {
                "type": "object",
                "properties": {"term": {"type": "string"}},
                "required": ["term"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup",
            "description": "Read one post or comment in full by its id, with what it replies to.",
            "parameters": {
                "type": "object",
                "properties": {"post_id": {"type": "string"}},
                "required": ["post_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "topic_trends",
            "description": "The community's topics with their engagement numbers and how each is "
            "moving, measured from the stored data.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "upcoming_events",
            "description": "Posts in the period you can see that mention dated plans: regattas, "
            "races, boat shows, festivals, meetups.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]
