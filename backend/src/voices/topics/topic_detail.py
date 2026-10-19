"""The Topic detail page's read (atlas plate 31, screen 4): one topic with its engagement
across the whole history, its most typical posts, and the decisions that built it."""

from typing import Protocol

from voices.topics.shapes import EngagementDay, PostCard, TopicDecision, TopicDetail, TopicSummary

TYPICAL_POSTS_SHOWN = 3


class TopicNotFound(Exception):
    pass


class TopicData(Protocol):
    def summary(self, topic_id: int) -> TopicSummary:
        """Raises TopicNotFound for an id with no topic."""
        ...

    def engagement(self, topic_id: int) -> list[EngagementDay]: ...
    def typical_posts(self, topic_id: int, limit: int) -> list[PostCard]: ...
    def decisions(self, topic_id: int) -> list[TopicDecision]: ...


class TopicDetails:
    def __init__(self, data: TopicData):
        self.data = data

    def detail(self, topic_id: int) -> TopicDetail:
        """Raises TopicNotFound for an id with no topic."""
        summary = self.data.summary(topic_id)
        return TopicDetail(
            **summary.model_dump(),
            daily=self.data.engagement(topic_id),
            typical_posts=self.data.typical_posts(topic_id, TYPICAL_POSTS_SHOWN),
            decisions=self.data.decisions(topic_id),
        )
