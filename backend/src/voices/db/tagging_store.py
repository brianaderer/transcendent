"""Reads and writes for tagging (atlas plate 21): the three-day window, the agent's searches,
applying its decisions, deleting what never clustered, and the daily engagement table."""

from collections.abc import Sequence
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import (
    Connection,
    Engine,
    Insert,
    Update,
    delete,
    func,
    insert,
    select,
    text,
    update,
)

from voices.db.models import ClusterDecision, Post, RetrievalEvent, Thread, Topic
from voices.tagging.clustering import WindowPost
from voices.tagging.decisions import CandidateTopic, DecidedCluster, TypicalPost

EXCERPT_CHARACTERS = 300
TYPICAL_POST_CHARACTERS = 600
RECENT_DAYS = 7  # "recent engagement" shown to the agent for each candidate topic


class TaggingStore:
    def __init__(self, engine: Engine):
        self.engine = engine

    # --- reading -------------------------------------------------------------------------

    def window_posts(self, first_day: date, last_day: date) -> list[WindowPost]:
        query = select(Post.source_id, Post.embedding, Post.topic_id).where(
            *_created_between(first_day, last_day), Post.embedding.is_not(None)
        )
        with self.engine.connect() as connection:
            rows = connection.execute(query).all()
        return [WindowPost(row.source_id, list(row.embedding), row.topic_id) for row in rows]

    def typical_posts(
        self, ids: Sequence[str], centroid: Sequence[float], limit: int
    ) -> list[TypicalPost]:
        query = (
            select(Post.source_id, Post.author, Post.body)
            .where(Post.source_id.in_(ids))
            .order_by(Post.embedding.cosine_distance(centroid))
            .limit(limit)
        )
        with self.engine.connect() as connection:
            rows = connection.execute(query).all()
        return [TypicalPost(r.source_id, r.author, r.body[:TYPICAL_POST_CHARACTERS]) for r in rows]

    def nearest_topics(self, centroid: Sequence[float], limit: int) -> list[CandidateTopic]:
        similarity = (1 - Topic.centroid.cosine_distance(centroid)).label("similarity")
        query = (
            select(Topic.id, Topic.label, Topic.description, similarity, _recent_posts())
            .order_by(similarity.desc())
            .limit(limit)
        )
        with self.engine.connect() as connection:
            rows = connection.execute(query).all()
        return [
            CandidateTopic(r.id, r.label, r.description, round(r.similarity, 3), r.recent)
            for r in rows
        ]

    def texts(self, ids: Sequence[str]) -> list[str]:
        with self.engine.connect() as connection:
            return list(connection.scalars(select(Post.body).where(Post.source_id.in_(ids))))

    def search_posts(
        self, embedding: Sequence[float], first_day: date, last_day: date, limit: int
    ) -> list[dict]:
        closeness = (1 - Post.embedding.cosine_distance(embedding)).label("closeness")
        query = (
            select(Post.source_id, Post.author, Post.created_at, Thread.title, Post.body, closeness)
            .join(Thread, Thread.source_id == Post.thread_source_id)
            .where(*_created_between(first_day, last_day))
            .order_by(closeness.desc())
            .limit(limit)
        )
        with self.engine.connect() as connection:
            return [_hit(row) for row in connection.execute(query).all()]

    def lookup_post(self, post_id: str) -> dict:
        """One post in full. Raises PostNotFound for an id that isn't stored."""
        query = (
            select(
                Post.source_id,
                Post.author,
                Post.created_at,
                Thread.title,
                Post.body,
                Post.parent_source_id,
            )
            .join(Thread, Thread.source_id == Post.thread_source_id)
            .where(Post.source_id == post_id)
        )
        with self.engine.connect() as connection:
            row = connection.execute(query).first()
        if row is None:
            raise PostNotFound(post_id)
        return {
            "post_id": row.source_id,
            "author": row.author,
            "date": row.created_at.date(),
            "thread": row.title,
            "text": row.body,
            "replies_to": row.parent_source_id,
        }

    def search_topics(self, embedding: Sequence[float], limit: int) -> list[dict]:
        return [vars(topic) for topic in self.nearest_topics(embedding, limit)]

    # --- writing -------------------------------------------------------------------------

    def record_retrievals(self, post_ids: Sequence[str], run: str, agent: str, tool: str) -> None:
        rows = [{"post_source_id": i, "run": run, "agent": agent, "tool": tool} for i in post_ids]
        with self.engine.begin() as connection:
            connection.execute(insert(RetrievalEvent), rows)

    def apply_decisions(
        self, day: date, settled: list[DecidedCluster], keywords: dict[str, list[str]]
    ) -> dict[str, int]:
        """All of a day's decisions in one transaction. Only posts still waiting for a tag are
        changed; posts already tagged in the window were there as anchors."""
        with self.engine.begin() as connection:
            applier = _DecisionApplier(connection, day, keywords)
            for item in settled:
                applier.apply(item)
        return applier.counts

    def delete_expired_pending(self, before: date) -> int:
        """Posts that joined no cluster in their three days are noise (atlas OPEN-14)."""
        statement = delete(Post).where(
            Post.status == "pending", Post.created_at < _start_of(before)
        )
        with self.engine.begin() as connection:
            return connection.execute(statement).rowcount

    def rebuild_engagement(self, first_day: date, last_day: date) -> None:
        """Recomputes each topic's daily engagement for these days from the posts."""
        days = {"first": first_day, "last": last_day}
        with self.engine.begin() as connection:
            connection.execute(text(CLEAR_ENGAGEMENT), days)
            connection.execute(text(COUNT_ENGAGEMENT), days)


class _DecisionApplier:
    """Applies one day's decisions inside one transaction, remembering the topics it mints so
    a merged mint can join them."""

    def __init__(self, connection: Connection, day: date, keywords: dict[str, list[str]]):
        self.connection = connection
        self.day = day
        self.keywords = keywords
        self.minted_topic_ids: dict[str, int] = {}  # cluster name -> its new topic
        self.counts = {"attached": 0, "minted": 0, "noise_deleted": 0, "left_waiting": 0}

    def apply(self, item: DecidedCluster) -> None:
        """Relies on settle_mints' order: a merged mint comes after the mint it joins."""
        action = item.decision.action
        if action == "noise":
            self.discard_as_noise(item)
        elif action == "attach":
            self.attach(item, self._existing_topic(item.decision.topic_id))
        elif item.merged_into:
            self.attach(item, self._twin_topic(item))
        else:
            self.attach(item, self.mint_topic(item))

    def discard_as_noise(self, item: DecidedCluster) -> None:
        self._record(item, topic_id=None)
        deleted = self.connection.execute(delete(Post).where(*_waiting(item))).rowcount
        self.counts["noise_deleted"] += deleted

    def attach(self, item: DecidedCluster, topic_id: int | None) -> None:
        """Tags the cluster's waiting posts with the topic. With no topic (the agent named one
        that doesn't exist) the posts keep waiting for another day's decision."""
        decision_id = self._record(item, topic_id)
        if topic_id is None:
            still_waiting = select(func.count()).select_from(Post).where(*_waiting(item))
            self.counts["left_waiting"] += self.connection.scalar(still_waiting)
            return
        statement = _tag_posts(_waiting(item), topic_id, decision_id, item)
        self.counts["attached"] += self.connection.execute(statement).rowcount
        self.connection.execute(_refresh_topic(topic_id, self.day))

    def mint_topic(self, item: DecidedCluster) -> int:
        """Creates the new topic and remembers it for any later cluster merged into it."""
        topic_id = self.connection.scalar(_new_topic(self.day, item, self.keywords))
        self.minted_topic_ids[item.brief.name] = topic_id
        self.counts["minted"] += 1
        return topic_id

    def _twin_topic(self, item: DecidedCluster) -> int:
        if item.merged_into not in self.minted_topic_ids:
            raise RuntimeError(f"{item.brief.name} merges into {item.merged_into}, not minted yet")
        return self.minted_topic_ids[item.merged_into]

    def _existing_topic(self, topic_id: int | None) -> int | None:
        return self.connection.scalar(select(Topic.id).where(Topic.id == topic_id))

    def _record(self, item: DecidedCluster, topic_id: int | None) -> int:
        return self.connection.scalar(_new_decision(self.day, item, topic_id))


class PostNotFound(Exception):
    pass


def _waiting(item: DecidedCluster) -> list:
    """The cluster's posts still waiting for a tag; posts already tagged were only anchors."""
    return [Post.source_id.in_(item.brief.member_ids), Post.status == "pending"]


def _new_topic(day: date, item: DecidedCluster, keywords: dict[str, list[str]]) -> Insert:
    return (
        insert(Topic)
        .values(
            label=item.decision.label or "Untitled",
            description=item.decision.description or "",
            keywords=keywords.get(item.brief.name, []),
            centroid=list(item.brief.centroid),
            first_seen=day,
            last_seen=day,
        )
        .returning(Topic.id)
    )


def _new_decision(day: date, item: DecidedCluster, topic_id: int | None) -> Insert:
    return (
        insert(ClusterDecision)
        .values(
            day=day,
            decision=item.decision.action,
            topic_id=topic_id,
            reason=item.decision.reason,
            candidate_tags=[vars(candidate) for candidate in item.brief.candidates],
            prompt=item.prompt,
            model=item.model,
        )
        .returning(ClusterDecision.id)
    )


def _tag_posts(waiting: list, topic_id: int, decision_id: int, item: DecidedCluster) -> Update:
    closeness = 1 - Post.embedding.cosine_distance(list(item.brief.centroid))
    return (
        update(Post)
        .where(*waiting)
        .values(
            status="tagged",
            topic_id=topic_id,
            cluster_decision_id=decision_id,
            topic_similarity=closeness,
        )
    )


def _refresh_topic(topic_id: int, day: date) -> Update:
    """The topic's centre moves to the average of its posts; it was last seen today."""
    average = select(func.avg(Post.embedding)).where(Post.topic_id == topic_id).scalar_subquery()
    return (
        update(Topic)
        .where(Topic.id == topic_id)
        .values(centroid=average, last_seen=func.greatest(Topic.last_seen, day))
    )


def _recent_posts():
    window_start = Topic.last_seen - RECENT_DAYS
    return (
        select(func.count())
        .where(Post.topic_id == Topic.id, func.date(Post.created_at) > window_start)
        .scalar_subquery()
        .label("recent")
    )


def _created_between(first_day: date, last_day: date) -> list:
    return [
        Post.created_at >= _start_of(first_day),
        Post.created_at < _start_of(last_day + timedelta(days=1)),
    ]


def _start_of(day: date) -> datetime:
    return datetime.combine(day, time(), UTC)


def _hit(row) -> dict:
    return {
        "post_id": row.source_id,
        "author": row.author,
        "date": row.created_at.date(),
        "thread": row.title,
        "excerpt": row.body[:EXCERPT_CHARACTERS],
        "closeness": round(row.closeness, 3),
    }


CLEAR_ENGAGEMENT = "DELETE FROM topic_daily_engagement WHERE day BETWEEN :first AND :last"

# One row per topic per day: posts and comments written that day, agreeing replies that day
# (even to older posts, so a day can have upvotes and no new posts), distinct people,
# threads started that day, and questions started that day that nobody has answered.
COUNT_ENGAGEMENT = """
WITH items AS (
    SELECT p.topic_id, (p.created_at AT TIME ZONE 'UTC')::date AS day, p.kind, p.author,
           p.kind = 'post' AND strpos(p.body, '?') > 0
             AND NOT EXISTS (SELECT 1 FROM posts r WHERE r.parent_source_id = p.source_id)
             AS unanswered
    FROM posts p
    WHERE p.status = 'tagged'
      AND (p.created_at AT TIME ZONE 'UTC')::date BETWEEN :first AND :last
), counted AS (
    SELECT topic_id, day,
           count(*) FILTER (WHERE kind = 'post') AS posts,
           count(*) FILTER (WHERE kind = 'comment') AS comments,
           count(DISTINCT author) AS unique_authors,
           count(*) FILTER (WHERE unanswered) AS unanswered_questions
    FROM items GROUP BY topic_id, day
), votes AS (
    SELECT q.topic_id, u.day, sum(u.count) AS upvotes
    FROM post_upvotes_daily u JOIN posts q ON q.source_id = u.post_source_id
    WHERE q.status = 'tagged' AND u.day BETWEEN :first AND :last
    GROUP BY q.topic_id, u.day
)
INSERT INTO topic_daily_engagement
    (topic_id, day, posts, comments, upvotes, unique_authors, new_threads, unanswered_questions)
SELECT coalesce(c.topic_id, v.topic_id), coalesce(c.day, v.day),
       coalesce(c.posts, 0), coalesce(c.comments, 0), coalesce(v.upvotes, 0),
       coalesce(c.unique_authors, 0), coalesce(c.posts, 0), coalesce(c.unanswered_questions, 0)
FROM counted c FULL OUTER JOIN votes v ON v.topic_id = c.topic_id AND v.day = c.day
"""
