"""Stand-ins shared across tests: the API routes' services, and topic data read by day."""

from datetime import date

from voices.api.main import ApiServices
from voices.explore.shapes import DayCount, Days, Map, MapPoint, TopicDay, TopicInfo, TopicInRange
from voices.report.launcher import RunStarted
from voices.report.runs import RunNotFound, RunState
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
            daily_before=[1, 1],
            direction="rising",
        )
        return [topic]

    def map(self, days):
        self.asked = days
        return Map(points=[map_point(n, days.start) for n in range(self.point_count)])


class RecordingTopicData:
    """Topics' daily engagement held in memory, remembering every span of days asked for."""

    def __init__(self, topic_days=(), topics=()):
        self._topic_days, self._topics, self.asked = list(topic_days), list(topics), []

    def topic_days(self, first_day, last_day):
        self.asked.append((first_day, last_day))
        return [d for d in self._topic_days if first_day <= d.day <= last_day]

    def topics(self, ids):
        return [t for t in self._topics if t.id in ids]


def topic_info(topic_id, first_seen=date(2026, 8, 1), label=None):
    return TopicInfo(
        id=topic_id, label=label or f"t{topic_id}", description="d", first_seen=first_seen
    )


def topic_day(topic_id, on, engagement):
    return TopicDay(topic_id=topic_id, day=on, engagement=engagement, posts=1)


class FakeRedis:
    """Keeps values in memory, recording each one's expiry."""

    def __init__(self):
        self.values, self.expiries = {}, {}

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value, ex):
        self.values[key], self.expiries[key] = value.encode(), ex


class FakeRuns:
    """Starts nothing; remembers the range asked for and answers one known run."""

    def __init__(self):
        self.started = None

    def start(self, days):
        self.started = days
        return RunStarted(run_id="0123456789ab", stream="run-0123456789ab")

    def state(self, run_id):
        if run_id != "0123456789ab":
            raise RunNotFound(run_id)
        return RunState(state="running")


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
        "runs": FakeRuns(),
    }
    return ApiServices(**(services | chosen))
