"""The comparison's answer key (atlas plate 70, OPEN-21): what the topic and engagement data
say about a range — which topics were biggest, in what order, and which way each moved —
measured exactly as the Explore page's badges are."""

from pydantic import BaseModel

from voices.explore.day_range import DayRange
from voices.explore.direction import Direction
from voices.explore.range_topics import TopicData, topics_in_range
from voices.explore.shapes import TopicInRange

MAIN_TOPICS = 10  # the range's biggest topics by engagement are the ones a report should find


class KeyTopic(BaseModel):
    topic_id: int
    label: str
    description: str
    rank: int  # 1 is the biggest; topics with equal engagement share a rank
    engagement: int  # posts, comments and upvotes in the range
    direction: Direction  # the Explore badge: new, rising, steady or fading

    @property
    def id(self) -> int:
        """The topic's id under the name the matching reads (`TopicInfo` uses `id`)."""
        return self.topic_id


def answer_key(data: TopicData, days: DayRange) -> list[KeyTopic]:
    """The range's main topics: every active topic ranked MAIN_TOPICS or better, biggest
    first (so a tie at the cut keeps every tied topic)."""
    return main_topics(active_topics(data, days))


def active_topics(data: TopicData, days: DayRange) -> list[KeyTopic]:
    """Every topic with engagement in the range, ranked, biggest first. A named topic that
    matches none of these was invented."""
    return ranked(topics_in_range(data, days))


def main_topics(active: list[KeyTopic]) -> list[KeyTopic]:
    return [t for t in active if t.rank <= MAIN_TOPICS]


def ranked(busiest_first: list[TopicInRange]) -> list[KeyTopic]:
    """Ranks by engagement: equal engagement shares a rank, and the next rank skips past
    them (1, 2, 2, 4)."""
    keys, rank = [], 0
    for position, topic in enumerate(busiest_first, start=1):
        if not keys or topic.engagement != keys[-1].engagement:
            rank = position
        keys.append(_key_topic(topic, rank))
    return keys


def _key_topic(topic: TopicInRange, rank: int) -> KeyTopic:
    return KeyTopic(
        topic_id=topic.id,
        label=topic.label,
        description=topic.description,
        rank=rank,
        engagement=topic.engagement,
        direction=topic.direction,
    )
