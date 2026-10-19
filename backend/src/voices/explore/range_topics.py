"""A range's topics with their numbers and badges (atlas plate 31), shared by the Explore
page and the comparison's answer key (plate 70), so both measure a topic the same way."""

from collections import defaultdict
from collections.abc import Sequence
from datetime import date
from typing import Protocol

from voices.explore.day_range import DayRange
from voices.explore.direction import is_new, trend
from voices.explore.shapes import TopicDay, TopicInfo, TopicInRange


class TopicData(Protocol):
    """Topics' daily engagement and their labels; `ExploreStore` satisfies it."""

    def topic_days(self, first_day: date, last_day: date) -> list[TopicDay]: ...
    def topics(self, ids: Sequence[int]) -> list[TopicInfo]: ...


def topics_in_range(data: TopicData, days: DayRange) -> list[TopicInRange]:
    """The topics with engagement in the range, busiest first (ties by id), each badged
    against the period of the same length just before the range."""
    rows = data.topic_days(days.period_before().start, days.end)
    by_topic = rows_by_topic(rows)
    info = {t.id: t for t in data.topics(sorted(by_topic))}
    topics = [_topic(info[i], topic_rows, days) for i, topic_rows in by_topic.items()]
    active = [t for t in topics if t.engagement > 0]
    return sorted(active, key=lambda t: (-t.engagement, t.id))


def rows_by_topic(rows: list[TopicDay]) -> dict[int, list[TopicDay]]:
    grouped: dict[int, list[TopicDay]] = defaultdict(list)
    for row in rows:
        grouped[row.topic_id].append(row)
    return grouped


def _topic(info: TopicInfo, rows: list[TopicDay], days: DayRange) -> TopicInRange:
    in_range = [r for r in rows if r.day in days]
    before = sum(r.engagement for r in rows if r.day < days.start)
    engagement = sum(r.engagement for r in in_range)
    return TopicInRange(
        **info.model_dump(),
        engagement=engagement,
        posts=sum(r.posts for r in in_range),
        daily=_daily(in_range, days),
        direction="new" if is_new(info.first_seen, days) else trend(engagement, before),
    )


def _daily(rows: list[TopicDay], days: DayRange) -> list[int]:
    by_day = {r.day: r.engagement for r in rows}
    return [by_day.get(day, 0) for day in days.days()]
