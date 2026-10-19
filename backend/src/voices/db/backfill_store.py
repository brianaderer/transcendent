"""Reads and writes for the backfill (atlas plate 07): which rows still lack their vector,
and saving the vectors rebuilt for them. Thread texts are read through the tagging store, so
a seeded thread is encoded exactly as tagging encodes it."""

from collections.abc import Sequence
from datetime import date

from sqlalchemy import ColumnElement, Engine, bindparam, func, select, update

from voices.backfill.backfill import PostText, Tally, UnencodedThread
from voices.db.models import Post, Thread, Topic
from voices.db.tagging_store import TaggingStore
from voices.tagging.threads import DueThread


class BackfillStore:
    def __init__(self, engine: Engine):
        self.engine = engine
        self.tagging = TaggingStore(engine)

    def posts_tally(self) -> Tally:
        return self._tally(Post.embedding)

    def threads_tally(self) -> Tally:
        return self._tally(Thread.embedding)

    def topics_tally(self) -> Tally:
        return self._tally(Topic.centroid)

    def posts_without_embeddings(self, limit: int) -> list[PostText]:
        query = (
            select(Post.source_id, Post.body)
            .where(Post.embedding.is_(None))
            .order_by(Post.source_id)
            .limit(limit)
        )
        with self.engine.connect() as connection:
            return [PostText(row.source_id, row.body) for row in connection.execute(query)]

    def save_post_embeddings(self, embeddings: dict[str, list[float]]) -> None:
        statement = (
            update(Post)
            .where(Post.source_id == bindparam("post_id"))
            .values(embedding=bindparam("encoding"))
        )
        rows = [{"post_id": i, "encoding": list(v)} for i, v in embeddings.items()]
        with self.engine.begin() as connection:
            connection.execute(statement, rows)

    def threads_without_embeddings(self, limit: int) -> list[UnencodedThread]:
        query = (
            select(Thread.source_id, Thread.first_seen_on, Thread.stage)
            .where(Thread.embedding.is_(None))
            .order_by(Thread.source_id)
            .limit(limit)
        )
        with self.engine.connect() as connection:
            return [UnencodedThread(*row) for row in connection.execute(query)]

    def threads_as_of(self, day: date, ids: Sequence[str]) -> list[DueThread]:
        return self.tagging.threads_as_of(day, ids)

    def save_thread_embeddings(self, embeddings: dict[str, list[float]]) -> None:
        self.tagging.save_thread_embeddings(embeddings)

    def rebuild_missing_centres(self) -> None:
        """Each topic with no centre gets the average of its threads' embeddings, which is
        what tagging keeps it at; a topic whose centre is there is left alone."""
        average = (
            select(func.avg(Thread.embedding)).where(Thread.topic_id == Topic.id).scalar_subquery()
        )
        statement = update(Topic).where(Topic.centroid.is_(None)).values(centroid=average)
        with self.engine.begin() as connection:
            connection.execute(statement)

    def _tally(self, vector: ColumnElement) -> Tally:
        query = select(func.count(vector), func.count())
        with self.engine.connect() as connection:
            done, total = connection.execute(query.select_from(vector.table)).one()
        return Tally(done=done, total=total)
