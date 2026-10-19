"""What the Topic detail page reads (atlas plate 31, screen 4): the API's response shape, and
the rows the store hands the service."""

from datetime import date

from pydantic import BaseModel


class TopicSummary(BaseModel):
    id: int
    label: str
    description: str
    keywords: list[str]
    first_seen: date
    last_seen: date


class EngagementDay(BaseModel):
    """One day the topic had any engagement."""

    day: date
    posts: int
    comments: int
    upvotes: int  # agreeing replies folded into the post they agree with
    people: int  # distinct authors who wrote in the topic that day


class PostCard(BaseModel):
    """A thread's opening post, as a typical post's card shows it. A thread whose post isn't
    stored is shown by its title, under an unknown author."""

    post_id: str
    thread_id: str
    kind: str  # post or comment, for building the link
    author: str
    day: date
    title: str
    excerpt: str


class TopicDecision(BaseModel):
    """One tagging decision that built the topic: minting it, or attaching threads to it."""

    day: date
    decision: str  # mint or attach
    threads: int  # threads that carry this decision now
    reason: str


class TopicDetail(TopicSummary):
    daily: list[EngagementDay]  # oldest first; days with no engagement are left out
    typical_posts: list[PostCard]  # closest to the topic's centre first
    decisions: list[TopicDecision]  # oldest first
