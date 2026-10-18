"""The tagging agent's tools: search, lookup and search_tags (atlas plate 60).

Search and lookup are counted in the retrieval statistics, as the tagging agent's, so the
report agent's retrievals can be shown apart (atlas OPEN-12).
"""

import json
from collections.abc import Sequence
from datetime import date, timedelta
from typing import Protocol

from voices.tagging.day_tagging import LOOKAHEAD_DAYS

SEARCH_RESULTS = 20
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
        return json.dumps(tool[name](arguments), default=str)

    def _search(self, arguments: dict) -> list[dict]:
        first_day = self.day - timedelta(days=LOOKAHEAD_DAYS - 1)
        embedding = self.embedder.embed_query(arguments["term"])
        hits = self.store.search_posts(embedding, first_day, self.day, SEARCH_RESULTS)
        self._count([hit["post_id"] for hit in hits], "search")
        return hits

    def _lookup(self, arguments: dict) -> dict:
        post = self.store.lookup_post(arguments["post_id"])
        self._count([arguments["post_id"]], "lookup")
        return post

    def _search_tags(self, arguments: dict) -> list[dict]:
        return self.store.search_topics(self.embedder.embed_query(arguments["term"]), TAG_RESULTS)

    def _count(self, post_ids: list[str], tool: str) -> None:
        if post_ids:
            self.store.record_retrievals(post_ids, self.run_name, "tagging", tool)
