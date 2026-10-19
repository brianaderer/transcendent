"""The Explore page's three reads (atlas plate 31): posts per day, the range's topics with
their badges, and the range's map, kept in a cache until a new day is loaded."""

from collections import defaultdict
from collections.abc import Callable, Sequence
from datetime import date
from typing import Protocol

from voices.explore.day_range import DayRange
from voices.explore.direction import direction, is_new
from voices.explore.projection import Point
from voices.explore.shapes import (
    DayCount,
    Days,
    Map,
    MapPoint,
    MapPost,
    TopicDay,
    TopicInfo,
    TopicInRange,
)

Flatten = Callable[[Sequence[Sequence[float]]], list[Point]]


class ExploreData(Protocol):
    def posts_per_day(self) -> list[DayCount]: ...
    def latest_day(self) -> date | None: ...
    def topic_days(self, first_day: date, last_day: date) -> list[TopicDay]: ...
    def topics(self, ids: Sequence[int]) -> list[TopicInfo]: ...
    def posts_in(self, first_day: date, last_day: date) -> list[MapPost]: ...


class MapCache(Protocol):
    def get(self, key: str) -> str | None: ...
    def put(self, key: str, value: str) -> None: ...


class Explore:
    def __init__(self, data: ExploreData, cache: MapCache, flatten: Flatten):
        self.data = data
        self.cache = cache
        self.flatten = flatten

    def days(self) -> Days:
        return Days(days=self.data.posts_per_day(), latest_day=self.data.latest_day())

    def topics(self, days: DayRange) -> list[TopicInRange]:
        """The topics with engagement in the range, busiest first."""
        rows = self.data.topic_days(days.period_before().start, days.end)
        by_topic = _by_topic(rows)
        info = {t.id: t for t in self.data.topics(sorted(by_topic))}
        topics = [_topic(info[i], topic_rows, days) for i, topic_rows in by_topic.items()]
        active = [t for t in topics if t.engagement > 0]
        return sorted(active, key=lambda t: (-t.engagement, t.id))

    def map(self, days: DayRange) -> Map:
        """Every post and comment written in the range, placed on the range's own map."""
        key = _map_key(days, self.data.latest_day())
        cached = self.cache.get(key)
        if cached:
            return Map.model_validate_json(cached)
        drawn = self._draw(self.data.posts_in(days.start, days.end))
        self.cache.put(key, drawn.model_dump_json())
        return drawn

    def _draw(self, posts: list[MapPost]) -> Map:
        places = self.flatten([post.embedding for post in posts])
        return Map(points=[_point(post, place) for post, place in zip(posts, places, strict=True)])


def _map_key(days: DayRange, latest_day: date | None) -> str:
    """The latest loaded day is part of the key, so a new day starts a new map and the old
    ones simply age out of the cache."""
    return f"map:{days.start}:{days.end}:{latest_day or 'nothing-loaded'}"


def _by_topic(rows: list[TopicDay]) -> dict[int, list[TopicDay]]:
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
        direction=direction(is_new(info.first_seen, days), engagement, before),
    )


def _daily(rows: list[TopicDay], days: DayRange) -> list[int]:
    by_day = {r.day: r.engagement for r in rows}
    return [by_day.get(day, 0) for day in days.days()]


def _point(post: MapPost, place: Point) -> MapPoint:
    x, y = place
    return MapPoint(**post.model_dump(exclude={"embedding"}), x=x, y=y)
