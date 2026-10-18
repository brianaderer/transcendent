"""Reads and writes for ingestion: the day's posts, threads and upvotes, and the ledger of
which days are done (atlas plates 21 and 40)."""

from collections.abc import Sequence
from datetime import UTC, date, datetime

from sqlalchemy import Engine, create_engine, func, select, update
from sqlalchemy.dialects.postgresql import insert

from voices.db.address import sqlalchemy_url
from voices.db.models import IngestedDay, Post, PostUpvotesDaily, Thread
from voices.ingestion.day import DayBatch, EmbeddedItem, NewThread


class Store:
    def __init__(self, engine: Engine):
        self.engine = engine

    def known_post_ids(self, ids: Sequence[str]) -> set[str]:
        return self._existing(Post.source_id, ids)

    def known_thread_ids(self, ids: Sequence[str]) -> set[str]:
        return self._existing(Thread.source_id, ids)

    def save_day(self, batch: DayBatch) -> None:
        """Everything the day adds, in one transaction. Saving the same day again changes
        nothing: posts and threads already there are skipped, and the day's upvote count is
        replaced, not added to, before each post's total is recounted from its days."""
        with self.engine.begin() as connection:
            if batch.threads:
                connection.execute(_insert_new(Thread, [_thread_row(t) for t in batch.threads]))
            if batch.posts:
                connection.execute(_insert_new(Post, [_post_row(p) for p in batch.posts]))
            for post_id, count in batch.upvotes.items():
                connection.execute(_set_daily_upvotes(post_id, batch.day, count))
                connection.execute(_recount_upvotes(post_id))

    def done_days(self) -> set[date]:
        with self.engine.connect() as connection:
            return set(
                connection.scalars(select(IngestedDay.day).where(IngestedDay.status == "done"))
            )

    def mark_running(self, day: date) -> None:
        self._record_day(day, status="running", started_at=_now(), finished_at=None, error=None)

    def mark_done(self, day: date, counts: dict[str, int]) -> None:
        self._record_day(day, status="done", counts=counts, finished_at=_now())

    def mark_failed(self, day: date, error: str) -> None:
        self._record_day(day, status="failed", error=error, finished_at=_now())

    def ingestion_status(self) -> dict:
        """Days done, posts stored (comments included), and the latest day in each state."""
        with self.engine.connect() as connection:
            return {
                "days_done": connection.scalar(_count_days("done")),
                "posts": connection.scalar(select(func.count()).select_from(Post)),
                "latest_day": _iso(connection.scalar(_latest_day("done"))),
                "running_day": _iso(connection.scalar(_latest_day("running"))),
                "failed_day": _iso(connection.scalar(_latest_day("failed"))),
            }

    def _existing(self, column, ids: Sequence[str]) -> set[str]:
        if not ids:
            return set()
        with self.engine.connect() as connection:
            return set(connection.scalars(select(column).where(column.in_(ids))))

    def _record_day(self, day: date, **fields) -> None:
        statement = insert(IngestedDay).values(day=day, **fields)
        with self.engine.begin() as connection:
            connection.execute(statement.on_conflict_do_update(index_elements=["day"], set_=fields))


def connect_store(database_url: str) -> Store:
    return Store(create_engine(sqlalchemy_url(database_url), pool_pre_ping=True))


def _insert_new(table, rows: list[dict]):
    return insert(table).values(rows).on_conflict_do_nothing()


def _thread_row(thread: NewThread) -> dict:
    return {"source_id": thread.source_id, "title": thread.title, "created_at": thread.created_at}


def _post_row(embedded: EmbeddedItem) -> dict:
    item = embedded.item
    return {
        "source_id": item.source_id,
        "thread_source_id": item.thread_source_id,
        "kind": item.kind,
        "author": item.author,
        "created_at": item.created_at,
        "body": item.body,
        "reddit_score": item.reddit_score,
        "parent_source_id": item.parent_source_id,
        "embedding": embedded.embedding,
    }


def _set_daily_upvotes(post_id: str, day: date, count: int):
    statement = insert(PostUpvotesDaily).values(post_source_id=post_id, day=day, count=count)
    return statement.on_conflict_do_update(
        index_elements=["post_source_id", "day"], set_={"count": statement.excluded.count}
    )


def _recount_upvotes(post_id: str):
    total = (
        select(func.coalesce(func.sum(PostUpvotesDaily.count), 0))
        .where(PostUpvotesDaily.post_source_id == post_id)
        .scalar_subquery()
    )
    return update(Post).where(Post.source_id == post_id).values(upvotes=total)


def _count_days(status: str):
    return select(func.count()).select_from(IngestedDay).where(IngestedDay.status == status)


def _latest_day(status: str):
    return select(func.max(IngestedDay.day)).where(IngestedDay.status == status)


def _iso(day: date | None) -> str | None:
    return day.isoformat() if day else None


def _now() -> datetime:
    return datetime.now(UTC)
