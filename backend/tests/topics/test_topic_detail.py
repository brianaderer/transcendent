from datetime import date

import pytest

from voices.topics.shapes import EngagementDay, PostCard, TopicDecision, TopicSummary
from voices.topics.topic_detail import TYPICAL_POSTS_SHOWN, TopicDetails, TopicNotFound

DAY = date(2026, 10, 12)
SUMMARY = TopicSummary(
    id=7,
    label="Impellers",
    description="Raw-water pump failures.",
    keywords=["impeller", "pump"],
    first_seen=DAY,
    last_seen=DAY,
)


class FakeTopicData:
    def __init__(self, known=(7,)):
        self.known, self.typical_limit = known, None

    def summary(self, topic_id):
        if topic_id not in self.known:
            raise TopicNotFound(topic_id)
        return SUMMARY

    def engagement(self, topic_id):
        return [EngagementDay(day=DAY, posts=1, comments=2, upvotes=3, people=2)]

    def typical_posts(self, topic_id, limit):
        self.typical_limit = limit
        card = PostCard(
            post_id="p1",
            thread_id="p1",
            kind="post",
            author="salty",
            day=DAY,
            title="Impellers",
            excerpt="Third one this season.",
        )
        return [card]

    def decisions(self, topic_id):
        return [TopicDecision(day=DAY, decision="mint", threads=4, reason="A new conversation.")]


def test_a_topics_detail_is_its_summary_engagement_typical_posts_and_decisions():
    detail = TopicDetails(FakeTopicData()).detail(7)

    assert (detail.label, detail.keywords) == ("Impellers", ["impeller", "pump"])
    assert detail.daily[0].people == 2
    assert detail.typical_posts[0].post_id == "p1"
    assert detail.decisions[0].decision == "mint"


def test_three_typical_posts_are_asked_for():
    data = FakeTopicData()

    TopicDetails(data).detail(7)

    assert data.typical_limit == TYPICAL_POSTS_SHOWN == 3


def test_an_unknown_topic_is_not_found():
    with pytest.raises(TopicNotFound):
        TopicDetails(FakeTopicData(known=())).detail(8)
