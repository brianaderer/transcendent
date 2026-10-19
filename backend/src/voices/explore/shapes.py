"""What the Explore page reads (atlas plate 31): the API's response shapes, and the rows the
store hands the service."""

from datetime import date

from pydantic import BaseModel

from voices.explore.direction import Direction


class DayCount(BaseModel):
    day: date
    posts: int  # posts and comments written that day


class Days(BaseModel):
    days: list[DayCount]
    latest_day: date | None  # the latest fully loaded day


class TopicInfo(BaseModel):
    id: int
    label: str
    description: str
    first_seen: date


class TopicInRange(TopicInfo):
    engagement: int  # posts, comments and upvotes in the range
    posts: int  # posts and comments in the range
    daily: list[int]  # engagement on each day of the range, in order
    direction: Direction


class TopicDay(BaseModel):
    topic_id: int
    day: date
    engagement: int
    posts: int


class PostSummary(BaseModel):
    """A post or comment as the dot plot's hover card shows it."""

    id: str
    thread_id: str
    kind: str  # post or comment
    author: str
    day: date
    thread_title: str
    excerpt: str
    thread_topic_id: int | None  # none while the thread waits for a decision


class MapPost(PostSummary):
    embedding: list[float]


class MapPoint(PostSummary):
    x: float
    y: float


class Map(BaseModel):
    points: list[MapPoint]
