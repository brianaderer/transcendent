"""The Retrieval stats page's read (atlas plate 31, screen 5): which stored posts an agent
retrieved most, and how its retrievals spread over the topics (CLAUDE.md §7)."""

from typing import Protocol

from voices.explore.day_range import DayRange
from voices.retrievals.shapes import (
    Agent,
    RankedPost,
    RetrievalFilter,
    RetrievalStats,
    RetrievedPost,
    TopicRetrievals,
)

MOST_RETRIEVED_SHOWN = 100  # the table's rows; enough to sort through, small to send


class RetrievalData(Protocol):
    def most_retrieved(self, which: RetrievalFilter, limit: int) -> list[RetrievedPost]:
        """The most retrieved first."""
        ...

    def per_topic(self, which: RetrievalFilter) -> list[TopicRetrievals]:
        """The most retrieved first."""
        ...

    def runs(self, agent: Agent, days: DayRange) -> list[str]: ...


class RetrievalStatistics:
    def __init__(self, data: RetrievalData):
        self.data = data

    def stats(self, which: RetrievalFilter) -> RetrievalStats:
        topics = self.data.per_topic(which)
        posts = self.data.most_retrieved(which, MOST_RETRIEVED_SHOWN)
        return RetrievalStats(
            agent=which.agent,
            runs=self.data.runs(which.agent, which.days),
            total=sum(topic.times_retrieved for topic in topics),
            posts=_ranked(posts),
            topics=topics,
        )


def _ranked(posts: list[RetrievedPost]) -> list[RankedPost]:
    return [RankedPost(**post.model_dump(), rank=n) for n, post in enumerate(posts, start=1)]
