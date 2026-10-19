"""Reads and writes for tagging (atlas plate 21): the threads due a decision, their
encodings, the agent's searches, applying its decisions, and the daily engagement table."""

from collections.abc import Sequence
from datetime import UTC, date, datetime, time, timedelta

from sqlalchemy import (
    ColumnElement,
    Connection,
    Engine,
    Insert,
    Select,
    Update,
    and_,
    bindparam,
    case,
    delete,
    func,
    insert,
    not_,
    or_,
    select,
    text,
    update,
)

from voices.db.models import ClusterDecision, Post, RetrievalEvent, Thread, Topic
from voices.tagging.decisions import CandidateTopic, DecidedCluster, TypicalPost
from voices.tagging.threads import DueThread, Reply
from voices.tagging.window import window_start

EXCERPT_CHARACTERS = 300
TYPICAL_POST_CHARACTERS = 600
RECENT_DAYS = 7  # "recent engagement" shown to the agent for each candidate topic
REVIVAL_DAYS = 7  # a thread older than this that gets new comments has come back to life


class TaggingStore:
    def __init__(self, engine: Engine):
        self.engine = engine

    # --- reading -------------------------------------------------------------------------

    def threads_due(self, day: date) -> list[DueThread]:
        """Threads on their first day not yet decided, and threads on their third day not yet
        settled, each with its post and the replies it has by the end of the day."""
        query = _thread_with_its_post(Thread.source_id, Post.body).where(_due_on(day))
        with self.engine.connect() as connection:
            threads = connection.execute(query).all()
            replies = self._replies(connection, [t.source_id for t in threads], day)
        return [DueThread(t.source_id, t.body, replies.get(t.source_id, [])) for t in threads]

    def _replies(
        self, connection: Connection, thread_ids: list[str], day: date
    ) -> dict[str, list[Reply]]:
        """Best-scored first."""
        query = (
            select(Post.thread_source_id, Post.body, Post.reddit_score)
            .where(
                Post.thread_source_id.in_(thread_ids),
                Post.kind == "comment",
                Post.created_at < _start_of(day + timedelta(days=1)),
            )
            .order_by(Post.reddit_score.desc())
        )
        replies: dict[str, list[Reply]] = {}
        for row in connection.execute(query):
            replies.setdefault(row.thread_source_id, []).append(Reply(row.body, row.reddit_score))
        return replies

    def typical_threads(
        self, ids: Sequence[str], centroid: Sequence[float], limit: int
    ) -> list[TypicalPost]:
        query = (
            _thread_with_its_post(Thread.source_id, Post.author, Post.body)
            .where(Thread.source_id.in_(ids))
            .order_by(Thread.embedding.cosine_distance(centroid))
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

    def save_thread_embeddings(self, embeddings: dict[str, list[float]]) -> None:
        if not embeddings:
            return
        statement = (
            update(Thread)
            .where(Thread.source_id == bindparam("thread_id"))
            .values(embedding=bindparam("encoding"))
        )
        rows = [{"thread_id": i, "encoding": list(v)} for i, v in embeddings.items()]
        with self.engine.begin() as connection:
            connection.execute(statement, rows)

    def record_retrievals(self, post_ids: Sequence[str], run: str, agent: str, tool: str) -> None:
        rows = [{"post_source_id": i, "run": run, "agent": agent, "tool": tool} for i in post_ids]
        with self.engine.begin() as connection:
            connection.execute(insert(RetrievalEvent), rows)

    def apply_decisions(
        self, day: date, settled: list[DecidedCluster], keywords: dict[str, list[str]]
    ) -> dict[str, int]:
        """All of a day's decisions in one transaction."""
        with self.engine.begin() as connection:
            applier = _DecisionApplier(connection, day, keywords)
            for item in settled:
                applier.apply(item)
        return applier.counts

    def rebuild_engagement(self, first_day: date, last_day: date) -> None:
        """Recomputes each topic's daily engagement for these days from the posts, each post
        counting for its thread's topic."""
        days = {"first": first_day, "last": last_day, "revival": REVIVAL_DAYS}
        with self.engine.begin() as connection:
            connection.execute(text(CLEAR_ENGAGEMENT), days)
            connection.execute(text(COUNT_ENGAGEMENT), days)


class _DecisionApplier:
    """Applies one day's decisions inside one transaction, remembering the topics it mints so
    a merged mint can join them. A thread decided on its first day is decided again on its
    third; the third day's decision is final."""

    def __init__(self, connection: Connection, day: date, keywords: dict[str, list[str]]):
        self.connection = connection
        self.day = day
        self.keywords = keywords
        self.minted_topic_ids: dict[str, int] = {}  # group name -> its new topic
        self.counts = {
            "attached": 0,
            "minted": 0,
            "noise_waiting": 0,
            "noise_deleted": 0,
            "left_waiting": 0,
        }

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
        """Noise on a thread's third day deletes it with its posts; on its first day the
        thread waits for its third."""
        decision_id = self._record(item, topic_id=None)
        self._delete_on_third_day(item)
        self._wait_for_third_day(item, decision_id)

    def attach(self, item: DecidedCluster, topic_id: int | None) -> None:
        """Tags the group's threads with the topic. With no topic (the agent named one that
        doesn't exist) the threads are left as they were."""
        decision_id = self._record(item, topic_id)
        if topic_id is None:
            self._leave_as_they_were(item)
            return
        topics_left = self._current_topics(_members(item)) - {topic_id}
        statement = _tag_threads(_members(item), topic_id, decision_id, self.day)
        self.counts["attached"] += self.connection.execute(statement).rowcount
        self._refresh_topics(left=topics_left, joined=topic_id)

    def mint_topic(self, item: DecidedCluster) -> int:
        """Creates the new topic and remembers it for any later group merged into it."""
        topic_id = self.connection.scalar(_new_topic(self.day, item, self.keywords))
        self.minted_topic_ids[item.brief.name] = topic_id
        self.counts["minted"] += 1
        return topic_id

    def _delete_on_third_day(self, item: DecidedCluster) -> None:
        on_third_day = and_(_members(item), _on_or_after_third_day(self.day))
        topics_left = self._current_topics(on_third_day)
        doomed = select(Thread.source_id).where(on_third_day)
        self.connection.execute(delete(Post).where(Post.thread_source_id.in_(doomed)))
        deleted = self.connection.execute(delete(Thread).where(on_third_day)).rowcount
        self.counts["noise_deleted"] += deleted
        self._refresh_topics(left=topics_left)

    def _wait_for_third_day(self, item: DecidedCluster, decision_id: int) -> None:
        on_first_day = and_(_members(item), not_(_on_or_after_third_day(self.day)))
        waiting = update(Thread).where(on_first_day)
        statement = waiting.values(stage="decided_once", cluster_decision_id=decision_id)
        self.counts["noise_waiting"] += self.connection.execute(statement).rowcount

    def _leave_as_they_were(self, item: DecidedCluster) -> None:
        """A first-day thread is decided again on its third day; a third-day thread keeps the
        topic its first day gave it, if any, and is settled."""
        members = select(func.count()).select_from(Thread).where(_members(item))
        self.counts["left_waiting"] += self.connection.scalar(members)
        on_third_day = and_(_members(item), _on_or_after_third_day(self.day))
        self.connection.execute(update(Thread).where(on_third_day).values(stage="settled"))

    def _refresh_topics(self, left: set[int], joined: int | None = None) -> None:
        """A topic's centre follows its threads; the topic joined today was also seen today."""
        if joined is not None:
            seen_today = func.greatest(Topic.last_seen, self.day)
            self.connection.execute(_refresh_topic(joined).values(last_seen=seen_today))
        for topic_id in left:
            self.connection.execute(_refresh_topic(topic_id))

    def _current_topics(self, threads: ColumnElement[bool]) -> set[int]:
        query = select(Thread.topic_id).where(threads, Thread.topic_id.is_not(None))
        return set(self.connection.scalars(query))

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


def _thread_with_its_post(*columns) -> Select:
    """A thread's post shares the thread's id."""
    return select(*columns).join(Post, Post.source_id == Thread.source_id)


def _due_on(day: date) -> ColumnElement[bool]:
    return or_(
        and_(_started_on(day), Thread.stage == "new"),
        and_(_started_on(window_start(day)), Thread.stage.in_(["new", "decided_once"])),
    )


def _started_on(day: date) -> ColumnElement[bool]:
    return and_(
        Thread.created_at >= _start_of(day), Thread.created_at < _start_of(day + timedelta(days=1))
    )


def _on_or_after_third_day(day: date) -> ColumnElement[bool]:
    """Threads started on or before the first of the three days ending today."""
    return Thread.created_at < _start_of(window_start(day) + timedelta(days=1))


def _members(item: DecidedCluster) -> ColumnElement[bool]:
    return Thread.source_id.in_(item.brief.member_ids)


def _tag_threads(
    members: ColumnElement[bool], topic_id: int, decision_id: int, day: date
) -> Update:
    stage = case((_on_or_after_third_day(day), "settled"), else_="decided_once")
    return (
        update(Thread)
        .where(members)
        .values(topic_id=topic_id, cluster_decision_id=decision_id, stage=stage)
    )


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


def _refresh_topic(topic_id: int) -> Update:
    """The topic's centre moves to the average of its threads; a topic left with no threads
    keeps the centre it had."""
    average = (
        select(func.avg(Thread.embedding)).where(Thread.topic_id == topic_id).scalar_subquery()
    )
    return (
        update(Topic)
        .where(Topic.id == topic_id)
        .values(centroid=func.coalesce(average, Topic.centroid))
    )


def _recent_posts():
    recent_start = Topic.last_seen - RECENT_DAYS
    return (
        select(func.count())
        .select_from(Post)
        .join(Thread, Thread.source_id == Post.thread_source_id)
        .where(Thread.topic_id == Topic.id, func.date(Post.created_at) > recent_start)
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

# One row per topic per day, each post counting for its thread's topic: posts and comments
# written that day, agreeing replies that day (even to older posts, so a day can have upvotes
# and no new posts), distinct people, threads started that day, threads older than :revival
# days that got comments that day, and questions started that day that nobody has answered.
COUNT_ENGAGEMENT = """
WITH items AS (
    SELECT t.topic_id, (p.created_at AT TIME ZONE 'UTC')::date AS day, p.kind, p.author,
           p.thread_source_id, (t.created_at AT TIME ZONE 'UTC')::date AS thread_day,
           p.kind = 'post' AND strpos(p.body, '?') > 0
             AND NOT EXISTS (SELECT 1 FROM posts r WHERE r.parent_source_id = p.source_id)
             AS unanswered
    FROM posts p JOIN threads t ON t.source_id = p.thread_source_id
    WHERE t.topic_id IS NOT NULL
      AND (p.created_at AT TIME ZONE 'UTC')::date BETWEEN :first AND :last
), counted AS (
    SELECT topic_id, day,
           count(*) FILTER (WHERE kind = 'post') AS posts,
           count(*) FILTER (WHERE kind = 'comment') AS comments,
           count(DISTINCT author) AS unique_authors,
           count(DISTINCT thread_source_id)
             FILTER (WHERE kind = 'comment' AND day - thread_day > :revival) AS revived_threads,
           count(*) FILTER (WHERE unanswered) AS unanswered_questions
    FROM items GROUP BY topic_id, day
), votes AS (
    SELECT t.topic_id, u.day, sum(u.count) AS upvotes
    FROM post_upvotes_daily u
    JOIN posts q ON q.source_id = u.post_source_id
    JOIN threads t ON t.source_id = q.thread_source_id
    WHERE t.topic_id IS NOT NULL AND u.day BETWEEN :first AND :last
    GROUP BY t.topic_id, u.day
)
INSERT INTO topic_daily_engagement
    (topic_id, day, posts, comments, upvotes, unique_authors, new_threads, revived_threads,
     unanswered_questions)
SELECT coalesce(c.topic_id, v.topic_id), coalesce(c.day, v.day),
       coalesce(c.posts, 0), coalesce(c.comments, 0), coalesce(v.upvotes, 0),
       coalesce(c.unique_authors, 0), coalesce(c.posts, 0), coalesce(c.revived_threads, 0),
       coalesce(c.unanswered_questions, 0)
FROM counted c FULL OUTER JOIN votes v ON v.topic_id = c.topic_id AND v.day = c.day
"""
