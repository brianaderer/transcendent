"""The Explore page's three reads (atlas plate 31): posts per day, the range's topics with
their badges, and the range's map, kept in a cache until a new day is loaded."""

from collections import defaultdict
from collections.abc import Callable, Sequence
from datetime import date, timedelta
from typing import Protocol

from voices.explore.direction import direction
from voices.explore.projection import Point
from voices.explore.shapes import (
    DayCount,
    Days,
    Map,
    MapPoint,
    MapPost,
    Topic,
    TopicDay,
    TopicInfo,
)

Flatten = Callable[[Sequence[Sequence[float]]], list[Point]]


class ExploreStore(Protocol):
    def posts_per_day(self) -> list[DayCount]: ...
    def latest_day(self) -> date | None: ...
    def topic_days(self, first_day: date, last_day: date) -> list[TopicDay]: ...
    def topics(self, ids: Sequence[int]) -> list[TopicInfo]: ...
    def posts_in(self, first_day: date, last_day: date) -> list[MapPost]: ...


class MapCache(Protocol):
    def get(self, key: str) -> str | None: ...
    def put(self, key: str, value: str) -> None: ...


class InvalidRange(Exception):
    pass


class Explore:
    def __init__(self, store: ExploreStore, cache: MapCache, flatten: Flatten):
        self.store = store
        self.cache = cache
        self.flatten = flatten

    def days(self) -> Days:
        return Days(days=self.store.posts_per_day(), latest_day=self.store.latest_day())

    def topics(self, start: date, end: date) -> list[Topic]:
        """The topics with engagement in the range, busiest first."""
        _check(start, end)
        length = (end - start).days + 1
        rows = self.store.topic_days(start - timedelta(days=length), end)
        by_topic = _by_topic(rows)
        info = {t.id: t for t in self.store.topics(sorted(by_topic))}
        topics = [_topic(info[i], days, start, end) for i, days in by_topic.items()]
        active = [t for t in topics if t.engagement > 0]
        return sorted(active, key=lambda t: (-t.engagement, t.id))

    def map(self, start: date, end: date) -> Map:
        """Every post and comment written in the range, placed on the range's own map."""
        _check(start, end)
        key = f"map:{start}:{end}:{self.store.latest_day()}"
        cached = self.cache.get(key)
        if cached:
            return Map.model_validate_json(cached)
        drawn = self._draw(self.store.posts_in(start, end))
        self.cache.put(key, drawn.model_dump_json())
        return drawn

    def _draw(self, posts: list[MapPost]) -> Map:
        places = self.flatten([post.embedding for post in posts])
        return Map(points=[_point(post, place) for post, place in zip(posts, places, strict=True)])


def _check(start: date, end: date) -> None:
    if end < start:
        raise InvalidRange(f"the range ends before it starts ({start} to {end})")


def _by_topic(rows: list[TopicDay]) -> dict[int, list[TopicDay]]:
    grouped: dict[int, list[TopicDay]] = defaultdict(list)
    for row in rows:
        grouped[row.topic_id].append(row)
    return grouped


def _topic(info: TopicInfo, rows: list[TopicDay], start: date, end: date) -> Topic:
    in_range = [r for r in rows if r.day >= start]
    before = sum(r.engagement for r in rows if r.day < start)
    engagement = sum(r.engagement for r in in_range)
    return Topic(
        **info.model_dump(),
        engagement=engagement,
        posts=sum(r.posts for r in in_range),
        daily=_daily(in_range, start, end),
        direction=direction(info.first_seen, start, engagement, before),
    )


def _daily(rows: list[TopicDay], start: date, end: date) -> list[int]:
    by_day = {r.day: r.engagement for r in rows}
    days = (end - start).days + 1
    return [by_day.get(start + timedelta(days=n), 0) for n in range(days)]


def _point(post: MapPost, place: Point) -> MapPoint:
    x, y = place
    return MapPoint(**post.model_dump(exclude={"embedding"}), x=x, y=y)
