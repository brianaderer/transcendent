"""One day of r/sailing: fetch, filter, fold agreeing replies into upvotes, embed, store.

The unit of work for the catch-up (atlas plate 40). Everything is fetched and computed first,
then saved in one transaction, so a day that fails part-way leaves nothing behind.
"""

from collections import Counter
from collections.abc import Sequence
from dataclasses import dataclass, field
from datetime import UTC, date, datetime, time, timedelta
from typing import Protocol

from voices.ingestion.filters import is_unwanted
from voices.ingestion.items import Item


class Archive(Protocol):
    def posts_created_between(self, start: datetime, end: datetime) -> list[Item]: ...
    def comments_created_between(self, start: datetime, end: datetime) -> list[Item]: ...
    def posts_by_id(self, ids: Sequence[str]) -> list[Item]: ...


class DocumentEmbedder(Protocol):
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...


class Agreement(Protocol):
    def agreeing(self, texts: Sequence[str]) -> list[bool]: ...


@dataclass(frozen=True)
class Thread:
    source_id: str
    title: str
    created_at: datetime


@dataclass(frozen=True)
class EmbeddedItem:
    item: Item
    embedding: list[float]


@dataclass
class DayBatch:
    """Everything one day adds to the database, saved together."""

    day: date
    threads: list[Thread] = field(default_factory=list)
    posts: list[EmbeddedItem] = field(default_factory=list)
    upvotes: dict[str, int] = field(default_factory=dict)  # parent post id -> agreeing replies


class DayStore(Protocol):
    def known_post_ids(self, ids: Sequence[str]) -> set[str]: ...
    def known_thread_ids(self, ids: Sequence[str]) -> set[str]: ...
    def save_day(self, batch: DayBatch) -> None: ...


def process_day(
    day: date, archive: Archive, embedder: DocumentEmbedder, agreement: Agreement, store: DayStore
) -> dict[str, int]:
    counts: Counter[str] = Counter()
    items = _wanted_items(_fetch_day(day, archive), counts)
    threads, items = _attach_threads(items, archive, store, counts)
    upvotes, items = _fold_agreeing_replies(items, agreement, store, counts)
    embedded = _embed(items, embedder)
    store.save_day(DayBatch(day, threads, embedded, upvotes))
    counts.update(stored=len(embedded), threads_added=len(threads), upvotes=sum(upvotes.values()))
    return dict(counts)


def _fetch_day(day: date, archive: Archive) -> list[Item]:
    start = datetime.combine(day, time(), UTC)
    end = start + timedelta(days=1)
    return archive.posts_created_between(start, end) + archive.comments_created_between(start, end)


def _wanted_items(items: list[Item], counts: Counter[str]) -> list[Item]:
    wanted = [item for item in items if not is_unwanted(item)]
    counts.update(fetched=len(items), dropped_unwanted=len(items) - len(wanted))
    return wanted


def _attach_threads(
    items: list[Item], archive: Archive, store: DayStore, counts: Counter[str]
) -> tuple[list[Thread], list[Item]]:
    """New threads come from today's posts; a comment on an older thread brings that thread's
    title from the archive. Comments whose thread can't be found are dropped."""
    threads = {i.source_id: _thread_of(i) for i in items if i.kind == "post"}
    needed = {i.thread_source_id for i in items} - threads.keys()
    unknown = sorted(needed - store.known_thread_ids(sorted(needed)))
    threads.update((p.source_id, _thread_of(p)) for p in archive.posts_by_id(unknown))
    available = threads.keys() | (needed - set(unknown))
    kept = [i for i in items if i.thread_source_id in available]
    counts.update(dropped_without_thread=len(items) - len(kept))
    return list(threads.values()), kept


def _thread_of(post: Item) -> Thread:
    return Thread(post.source_id, post.title or "", post.created_at)


def _fold_agreeing_replies(
    items: list[Item], agreement: Agreement, store: DayStore, counts: Counter[str]
) -> tuple[dict[str, int], list[Item]]:
    comments = [i for i in items if i.kind == "comment"]
    agreeing = {
        c.source_id
        for c, a in zip(comments, agreement.agreeing([c.body for c in comments]), strict=True)
        if a
    }
    parents = [c.parent_source_id for c in comments if c.source_id in agreeing]
    reachable = store.known_post_ids(parents) | {
        i.source_id for i in items if i.source_id not in agreeing
    }
    upvotes = Counter(p for p in parents if p in reachable)
    counts.update(dropped_orphan_upvotes=len(parents) - sum(upvotes.values()))
    return dict(upvotes), [i for i in items if i.source_id not in agreeing]


def _embed(items: list[Item], embedder: DocumentEmbedder) -> list[EmbeddedItem]:
    if not items:
        return []
    vectors = embedder.embed_documents([item.body for item in items])
    return [EmbeddedItem(item, vector) for item, vector in zip(items, vectors, strict=True)]
