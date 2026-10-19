from datetime import UTC, date, datetime

from voices.explore.day_range import DayRange
from voices.retrievals.retrieval_stats import MOST_RETRIEVED_SHOWN, RetrievalStatistics
from voices.retrievals.shapes import RetrievalFilter, RetrievedPost, TopicRetrievals

DAYS = DayRange(date(2026, 10, 12), date(2026, 10, 18))
TAGGING = RetrievalFilter(agent="tagging", days=DAYS)


def retrieved(post_id, times):
    return RetrievedPost(
        post_id=post_id,
        thread_id="t1",
        kind="comment",
        author="salty",
        day=DAYS.start,
        excerpt="Carry a spare.",
        topic_id=1,
        topic_label="Impellers",
        times_retrieved=times,
        last_retrieved=datetime(2026, 10, 19, tzinfo=UTC),
    )


class FakeRetrievalData:
    def __init__(self, posts=(), topics=()):
        self.posts, self.topics, self.asked = list(posts), list(topics), []

    def most_retrieved(self, which, limit):
        self.asked.append(("posts", which, limit))
        return self.posts

    def per_topic(self, which):
        self.asked.append(("topics", which))
        return self.topics

    def runs(self, agent, days):
        self.asked.append(("runs", agent, days))
        return ["tagging-2026-10-18"]


def test_posts_are_ranked_in_the_order_the_store_gives_them_starting_at_one():
    data = FakeRetrievalData(posts=[retrieved("a", 9), retrieved("b", 4)])

    stats = RetrievalStatistics(data).stats(TAGGING)

    assert [(p.rank, p.post_id) for p in stats.posts] == [(1, "a"), (2, "b")]


def test_the_total_counts_every_retrieval_across_the_topics():
    topics = [
        TopicRetrievals(topic_id=1, label="Impellers", times_retrieved=12),
        TopicRetrievals(topic_id=None, label=None, times_retrieved=3),
    ]

    stats = RetrievalStatistics(FakeRetrievalData(topics=topics)).stats(TAGGING)

    assert stats.total == 15


def test_every_read_is_asked_with_the_filter_and_the_table_is_limited():
    data = FakeRetrievalData()

    stats = RetrievalStatistics(data).stats(TAGGING)

    assert ("posts", TAGGING, MOST_RETRIEVED_SHOWN) in data.asked
    assert ("topics", TAGGING) in data.asked
    assert ("runs", "tagging", DAYS) in data.asked
    assert (stats.agent, stats.runs) == ("tagging", ["tagging-2026-10-18"])


def test_no_retrievals_is_an_empty_page_not_an_error():
    stats = RetrievalStatistics(FakeRetrievalData()).stats(TAGGING)

    assert (stats.total, stats.posts, stats.topics) == (0, [], [])
