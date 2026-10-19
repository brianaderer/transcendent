"""What the Retrieval stats page reads (atlas plate 31, screen 5): the API's response shape,
the filter it is asked with, and the rows the store hands the service."""

from dataclasses import dataclass
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

from voices.explore.day_range import DayRange

Agent = Literal["report", "tagging"]


@dataclass(frozen=True)
class RetrievalFilter:
    """Which retrievals count: one agent's, of posts written in the range, from one run or
    (with no run named) from every run."""

    agent: Agent
    days: DayRange
    run: str | None = None


class RetrievedPost(BaseModel):
    post_id: str
    thread_id: str
    kind: str  # post or comment
    author: str
    day: date  # the day it was written
    excerpt: str
    topic_id: int | None  # its thread's topic; none while the thread waits for a decision
    topic_label: str | None
    times_retrieved: int
    last_retrieved: datetime


class RankedPost(RetrievedPost):
    rank: int  # 1 for the most retrieved


class TopicRetrievals(BaseModel):
    topic_id: int | None  # none: posts whose thread has no topic yet
    label: str | None
    times_retrieved: int


class RetrievalStats(BaseModel):
    agent: Agent
    runs: list[str]  # the runs that retrieved any of the range's posts, newest first
    total: int  # every counted retrieval
    posts: list[RankedPost]  # the most retrieved first
    topics: list[TopicRetrievals]  # the most retrieved first
