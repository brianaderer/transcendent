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


class Topic(BaseModel):
    id: int
    label: str
    description: str
    first_seen: date
    engagement: int  # posts, comments and upvotes in the range
    posts: int  # posts and comments in the range
    daily: list[int]  # engagement on each day of the range, in order
    direction: Direction


class MapPoint(BaseModel):
    id: str
    thread_id: str
    kind: str  # post or comment
    author: str
    day: date
    title: str  # the thread's
    excerpt: str
    topic_id: int | None  # the thread's; none while it waits for a decision
    x: float
    y: float


class Map(BaseModel):
    points: list[MapPoint]


class TopicDay(BaseModel):
    topic_id: int
    day: date
    engagement: int
    posts: int


class TopicInfo(BaseModel):
    id: int
    label: str
    description: str
    first_seen: date


class MapPost(BaseModel):
    id: str
    thread_id: str
    kind: str
    author: str
    day: date
    title: str
    excerpt: str
    topic_id: int | None
    embedding: list[float]
