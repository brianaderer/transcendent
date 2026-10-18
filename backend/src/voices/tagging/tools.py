"""The tagging agent's tools: search, lookup and search_tags (atlas plate 60).

Search and lookup are counted in the retrieval statistics, as the tagging agent's, so the
report agent's retrievals can be shown apart (atlas OPEN-12).
"""

import json
from collections.abc import Sequence
from datetime import date
from typing import Protocol

from voices.db.tagging_store import PostNotFound
from voices.tagging.window import window_start

SEARCH_RESULTS = 20
REQUIRED_ARGUMENT = {"search": "term", "lookup": "post_id", "search_tags": "term"}
TAG_RESULTS = 10


class ToolStore(Protocol):
    def search_posts(
        self, embedding: Sequence[float], first_day: date, last_day: date, limit: int
    ) -> list[dict]: ...
    def lookup_post(self, post_id: str) -> dict: ...
    def search_topics(self, embedding: Sequence[float], limit: int) -> list[dict]: ...
    def record_retrievals(
        self, post_ids: Sequence[str], run: str, agent: str, tool: str
    ) -> None: ...


class QueryEmbedder(Protocol):
    def embed_query(self, text: str) -> list[float]: ...


class TaggingTools:
    def __init__(self, store: ToolStore, embedder: QueryEmbedder, day: date):
        self.store = store
        self.embedder = embedder
        self.day = day
        self.run_name = f"tagging-{day.isoformat()}"

    def run(self, name: str, arguments: dict) -> str:
        """Runs one tool call and returns what the agent reads back."""
        tool = {"search": self._search, "lookup": self._lookup, "search_tags": self._search_tags}
        if name not in tool:
            return f"There is no tool named {name}; use search, lookup or search_tags."
        if REQUIRED_ARGUMENT[name] not in arguments:
            return f"Tool {name} needs the argument '{REQUIRED_ARGUMENT[name]}'."
        return json.dumps(tool[name](arguments), default=str)

    def _search(self, arguments: dict) -> list[dict]:
        embedding = self.embedder.embed_query(arguments["term"])
        hits = self.store.search_posts(embedding, window_start(self.day), self.day, SEARCH_RESULTS)
        self._count([hit["post_id"] for hit in hits], "search")
        return hits

    def _lookup(self, arguments: dict) -> dict | str:
        post_id = arguments["post_id"]
        try:
            post = self.store.lookup_post(post_id)
        except PostNotFound:
            return f"There is no post with id {post_id}; ids come from search results."
        self._count([post_id], "lookup")
        return post

    def _search_tags(self, arguments: dict) -> list[dict]:
        return self.store.search_topics(self.embedder.embed_query(arguments["term"]), TAG_RESULTS)

    def _count(self, post_ids: list[str], tool: str) -> None:
        if post_ids:
            self.store.record_retrievals(post_ids, self.run_name, "tagging", tool)
