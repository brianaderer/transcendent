"""Stand-ins shared by the API route tests."""

from datetime import date

from voices.api.main import ApiServices
from voices.explore.shapes import DayCount, Days, Map, MapPoint, TopicInRange
from voices.retrievals.shapes import RetrievalStats
from voices.topics.shapes import EngagementDay, PostCard, TopicDecision, TopicDetail
from voices.topics.topic_detail import TopicNotFound


async def no_events(_stream):
    return
    yield  # never reached; its presence makes this an (empty) async generator


def map_point(n, day):
    return MapPoint(
        id=f"p{n}",
        thread_id="t1",
        kind="post",
        author="salty",
        day=day,
        thread_title="Impellers",
        excerpt="Why does my impeller keep failing?",
        thread_topic_id=1,
        x=0.5,
        y=-0.5,
    )


class FakeExplore:
    """Answers the Explore reads with fixed data, remembering the range it was asked for."""

    def __init__(self, point_count=1):
        self.asked, self.point_count = None, point_count

    def days(self):
        return Days(days=[DayCount(day=date(2026, 10, 12), posts=4)], latest_day=date(2026, 10, 12))

    def topics(self, days):
        self.asked = days
        topic = TopicInRange(
            id=1,
            label="Impellers",
            description="d",
            first_seen=date(2026, 9, 1),
            engagement=7,
            posts=2,
            daily=[5, 2],
            direction="rising",
        )
        return [topic]

    def map(self, days):
        self.asked = days
        return Map(points=[map_point(n, days.start) for n in range(self.point_count)])


class FakeTopics:
    """Answers the Topic detail read for one known topic, id 1."""

    def detail(self, topic_id):
        if topic_id != 1:
            raise TopicNotFound(topic_id)
        day = date(2026, 10, 12)
        return TopicDetail(
            id=1,
            label="Impellers",
            description="d",
            keywords=["impeller"],
            first_seen=date(2026, 9, 1),
            last_seen=day,
            daily=[EngagementDay(day=day, posts=1, comments=2, upvotes=3, people=2)],
            typical_posts=[
                PostCard(
                    post_id="p1",
                    thread_id="p1",
                    kind="post",
                    author="salty",
                    day=day,
                    title="Impellers",
                    excerpt="Third one this season.",
                )
            ],
            decisions=[TopicDecision(day=day, decision="mint", threads=3, reason="New.")],
        )


class FakeRetrievals:
    """Answers the Retrieval stats read with no retrievals, remembering the filter asked."""

    def __init__(self):
        self.asked = None

    def stats(self, which):
        self.asked = which
        return RetrievalStats(agent=which.agent, runs=[], total=0, posts=[], topics=[])


def stand_in_services(**chosen):
    """Every service a stand-in, except those chosen by name."""
    services = {
        "health_checks": {},
        "ingestion_status": dict,
        "event_stream": no_events,
        "explore": FakeExplore(),
        "topics": FakeTopics(),
        "retrievals": FakeRetrievals(),
    }
    return ApiServices(**(services | chosen))
