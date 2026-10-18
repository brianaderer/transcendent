"""The tagging agent as the catch-up uses it: one decision per cluster of a day."""

from collections.abc import Sequence
from datetime import date
from typing import Protocol

from voices.db.tagging_store import TaggingStore
from voices.tagging.decider import ToolLoopDecider
from voices.tagging.decisions import ClusterBrief, DecidedCluster
from voices.tagging.graph import decide_all
from voices.tagging.model import connect_model
from voices.tagging.tools import TaggingTools


class QueryEmbedder(Protocol):
    def embed_query(self, text: str) -> list[float]: ...


class TaggingAgent:
    def __init__(self, store: TaggingStore, embedder: QueryEmbedder, api_key: str, model_name: str):
        self.store = store
        self.embedder = embedder
        self.api_key = api_key
        self.model_name = model_name

    def decide(self, day: date, briefs: Sequence[ClusterBrief]) -> list[DecidedCluster]:
        """Decides every cluster of the day. Without a key this raises MissingModelKey, with a
        message saying where the key goes."""
        model = connect_model(self.api_key, self.model_name)
        tools = TaggingTools(self.store, self.embedder, day)
        return decide_all(ToolLoopDecider(model, self.model_name, tools), list(briefs))
