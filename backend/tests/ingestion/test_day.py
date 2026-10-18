from datetime import UTC, date, datetime

from voices.ingestion.day import DayIngestion
from voices.ingestion.items import Item

DAY = date(2026, 10, 15)
AT = datetime(2026, 10, 15, 12, tzinfo=UTC)


def post(source_id, body="Which anchor for a 32ft sloop?"):
    return Item(source_id, source_id, "post", "salty", AT, body, 5, None, title=body)


def comment(source_id, body, parent, thread="p1", author="deckhand"):
    return Item(source_id, thread, "comment", author, AT, body, 1, parent)


class FakeArchive:
    def __init__(self, posts=(), comments=(), old_threads=()):
        self.posts, self.comments, self.old_threads = list(posts), list(comments), list(old_threads)

    def posts_created_between(self, start, end):
        return self.posts

    def comments_created_between(self, start, end):
        return self.comments

    def posts_by_id(self, ids):
        return [t for t in self.old_threads if t.source_id in ids]


class FakeEmbedder:
    def embed_documents(self, texts):
        return [[float(len(text))] for text in texts]


class AgreesWithPlusOne:
    def agreeing(self, texts):
        return [text == "+1" for text in texts]


class FakeStore:
    def __init__(self, posts=(), threads=()):
        self.posts, self.threads, self.saved = set(posts), set(threads), None

    def known_post_ids(self, ids):
        return self.posts & set(ids)

    def known_thread_ids(self, ids):
        return self.threads & set(ids)

    def save_day(self, batch):
        self.saved = batch


def run(archive, store):
    return DayIngestion(archive, FakeEmbedder(), AgreesWithPlusOne(), store).process(DAY)


def test_posts_and_comments_are_stored_with_their_embeddings():
    store = FakeStore()
    run(FakeArchive([post("p1")], [comment("c1", "Rocna, every time.", parent="p1")]), store)

    assert [p.item.source_id for p in store.saved.posts] == ["p1", "c1"]
    assert store.saved.posts[1].embedding == [float(len("Rocna, every time."))]
    assert [t.source_id for t in store.saved.threads] == ["p1"]


def test_unwanted_posts_are_dropped_and_counted():
    store = FakeStore()
    counts = run(
        FakeArchive(
            [post("p1")],
            [
                comment("c1", "[removed]", parent="p1"),
                comment("c2", "hi", parent="p1", author="AutoModerator"),
            ],
        ),
        store,
    )

    assert [p.item.source_id for p in store.saved.posts] == ["p1"]
    assert counts["dropped_unwanted"] == 2


def test_an_agreeing_reply_becomes_an_upvote_on_its_parent_and_is_not_stored():
    store = FakeStore(posts={"p0"}, threads={"p0"})
    counts = run(
        FakeArchive(
            [],
            [
                comment("c1", "+1", parent="p0", thread="p0"),
                comment("c2", "+1", parent="p0", thread="p0"),
            ],
        ),
        store,
    )

    assert store.saved.posts == []
    assert store.saved.upvotes == {"p0": 2}
    assert counts["upvotes"] == 2


def test_an_agreeing_reply_to_a_post_we_do_not_have_is_dropped():
    store = FakeStore(threads={"p0"})
    counts = run(FakeArchive([], [comment("c1", "+1", parent="gone", thread="p0")]), store)

    assert store.saved.upvotes == {}
    assert counts["dropped_orphan_upvotes"] == 1


def test_a_comment_on_a_thread_older_than_the_history_brings_the_thread_title_with_it():
    old = post("p0", body="Winter cover ideas")
    store = FakeStore()
    run(
        FakeArchive(
            [], [comment("c1", "Shrink wrap.", parent="p0", thread="p0")], old_threads=[old]
        ),
        store,
    )

    assert [(t.source_id, t.title) for t in store.saved.threads] == [("p0", "Winter cover ideas")]
    assert [p.item.source_id for p in store.saved.posts] == ["c1"]


def test_a_comment_whose_thread_cannot_be_found_is_dropped():
    store = FakeStore()
    counts = run(FakeArchive([], [comment("c1", "Shrink wrap.", parent="p0", thread="p0")]), store)

    assert store.saved.posts == []
    assert counts["dropped_without_thread"] == 1


def test_an_agreeing_reply_to_a_post_from_the_same_day_upvotes_it():
    store = FakeStore()
    run(FakeArchive([post("p1")], [comment("c1", "+1", parent="p1")]), store)

    assert store.saved.upvotes == {"p1": 1}
    assert [p.item.source_id for p in store.saved.posts] == ["p1"]
