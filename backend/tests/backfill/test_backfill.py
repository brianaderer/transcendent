from datetime import date

import pytest

from voices.backfill.backfill import Backfill, PostText, Tally, ThreadsNotFound, UnencodedThread
from voices.tagging.threads import DueThread, Reply, thread_text

FIRST_SEEN = date(1999, 1, 2)
THIRD_DAY = date(1999, 1, 4)


class FakeStore:
    """Posts, threads and topic centres held in memory; a vector is None until filled."""

    def __init__(self, posts=None, threads=None, centres=None, replies_by_day=None):
        self.posts = posts or {}  # id -> [body, vector]
        self.threads = threads or {}  # id -> [first_seen_on, stage, vector]
        self.centres = centres or {}  # topic id -> vector or None
        self.replies_by_day = replies_by_day or {}  # (thread id, day) -> replies
        self.calls = []

    def posts_tally(self):
        return _tally(v for _, v in self.posts.values())

    def threads_tally(self):
        return _tally(v for _, _, v in self.threads.values())

    def topics_tally(self):
        return _tally(self.centres.values())

    def posts_without_embeddings(self, limit):
        missing = sorted(i for i, (_, v) in self.posts.items() if v is None)[:limit]
        return [PostText(i, self.posts[i][0]) for i in missing]

    def save_post_embeddings(self, embeddings):
        self.calls.append(("posts", sorted(embeddings)))
        for i, vector in embeddings.items():
            self.posts[i][1] = vector

    def threads_without_embeddings(self, limit):
        missing = sorted(i for i, (_, _, v) in self.threads.items() if v is None)[:limit]
        return [UnencodedThread(i, self.threads[i][0], self.threads[i][1]) for i in missing]

    def threads_as_of(self, day, ids):
        self.calls.append(("threads_as_of", day, sorted(ids)))
        return [DueThread(i, f"post {i}", self.replies_by_day.get((i, day), [])) for i in ids]

    def save_thread_embeddings(self, embeddings):
        self.calls.append(("threads", sorted(embeddings)))
        for i, vector in embeddings.items():
            self.threads[i][2] = vector

    def rebuild_missing_centres(self):
        self.calls.append(("centres",))
        for topic_id, centre in self.centres.items():
            self.centres[topic_id] = centre or [1.0]


def _tally(vectors):
    vectors = list(vectors)
    return Tally(done=sum(v is not None for v in vectors), total=len(vectors))


class EchoEmbedder:
    def __init__(self):
        self.texts = []

    def embed_documents(self, texts):
        self.texts += texts
        return [[float(len(text))] for text in texts]


class FakeProgress:
    def __init__(self, recorded=False):
        self.records, self.is_recorded, self.cleared = [], recorded, False

    def record(self, what, done, total):
        self.records.append((what, done, total))
        self.is_recorded = True

    def recorded(self):
        return self.is_recorded

    def clear(self):
        self.cleared, self.is_recorded = True, False


class Harness:
    def __init__(self, store, progress=None):
        self.store, self.embedder = store, EchoEmbedder()
        self.progress, self.events, self.maps_forgotten = progress or FakeProgress(), [], 0

    def run(self, batch_size=2):
        backfill = Backfill(
            self.store, self.embedder, self.progress, self.emit, self.forget_maps, batch_size
        )
        backfill.run()

    def emit(self, event_type, **body):
        self.events.append((event_type, body))

    def forget_maps(self):
        self.maps_forgotten += 1


def seeded_store():
    return FakeStore(
        posts={"p1": ["one", None], "p2": ["two", None], "p3": ["three", None]},
        threads={"t1": [FIRST_SEEN, "settled", None]},
        centres={7: None},
    )


def test_nothing_happens_when_no_vector_is_missing():
    store = FakeStore(posts={"p1": ["one", [1.0]]}, threads={"t1": [FIRST_SEEN, "settled", [1.0]]})
    harness = Harness(store)

    harness.run()

    assert harness.events == []
    assert harness.embedder.texts == []
    assert harness.maps_forgotten == 0


def test_posts_are_embedded_whole_in_batches_each_saved_as_it_goes():
    harness = Harness(seeded_store())

    harness.run(batch_size=2)

    assert [call for call in harness.store.calls if call[0] == "posts"] == [
        ("posts", ["p1", "p2"]),
        ("posts", ["p3"]),
    ]
    assert harness.embedder.texts[:3] == ["one", "two", "three"]


def test_progress_counts_up_through_posts_then_threads_then_topics():
    harness = Harness(seeded_store())

    harness.run(batch_size=2)

    assert harness.progress.records == [
        ("posts", 0, 3),
        ("posts", 2, 3),
        ("posts", 3, 3),
        ("threads", 0, 1),
        ("threads", 1, 1),
        ("topics", 0, 1),
        ("topics", 1, 1),
    ]
    progress_events = [body for kind, body in harness.events if kind == "backfill.progress"]
    assert progress_events[0] == {"what": "posts", "done": 0, "total": 3}
    assert len(progress_events) == len(harness.progress.records)


def test_a_restart_counts_on_from_what_was_already_filled():
    store = seeded_store()
    store.posts["p1"][1] = [1.0]
    harness = Harness(store)

    harness.run(batch_size=5)

    assert harness.progress.records[:2] == [("posts", 1, 3), ("posts", 3, 3)]
    assert ("posts", ["p2", "p3"]) in store.calls


def test_a_settled_thread_is_encoded_as_it_stood_on_its_third_day():
    replies = {("t1", THIRD_DAY): [Reply("late and good", 9)]}
    store = FakeStore(threads={"t1": [FIRST_SEEN, "settled", None]}, replies_by_day=replies)
    harness = Harness(store)

    harness.run()

    assert ("threads_as_of", THIRD_DAY, ["t1"]) in store.calls
    assert harness.embedder.texts == [thread_text("post t1", [Reply("late and good", 9)])]


def test_a_thread_still_waiting_for_its_third_day_is_encoded_as_it_stood_on_its_first():
    store = FakeStore(threads={"t2": [FIRST_SEEN, "decided_once", None]})

    Harness(store).run()

    assert ("threads_as_of", FIRST_SEEN, ["t2"]) in store.calls


class LosingStore(FakeStore):
    """Can't find one of the threads it is asked for, as a thread deleted mid-run would be."""

    def threads_as_of(self, day, ids):
        return super().threads_as_of(day, ids)[1:]


def test_a_thread_the_store_cannot_find_stops_the_backfill_instead_of_looping():
    threads = {"t1": [FIRST_SEEN, "settled", None], "t2": [FIRST_SEEN, "settled", None]}
    store = LosingStore(threads=threads)

    with pytest.raises(ThreadsNotFound, match="t1"):
        Harness(store).run()


def test_topic_centres_are_rebuilt_after_every_thread_has_its_embedding():
    store = seeded_store()

    Harness(store).run()

    kinds = [call[0] for call in store.calls if call[0] in ("threads", "centres")]
    assert kinds == ["threads", "centres"]
    assert store.centres[7] == [1.0]


def test_when_done_the_cached_maps_are_forgotten_and_the_progress_cleared():
    harness = Harness(seeded_store())

    harness.run()

    assert harness.maps_forgotten == 1
    assert harness.progress.cleared
    assert harness.events[-1] == ("backfill.finished", {})


def test_a_backfill_stopped_just_before_finishing_finishes_on_the_next_run():
    store = FakeStore(posts={"p1": ["one", [1.0]]})
    harness = Harness(store, FakeProgress(recorded=True))

    harness.run()

    assert harness.maps_forgotten == 1
    assert harness.progress.cleared
