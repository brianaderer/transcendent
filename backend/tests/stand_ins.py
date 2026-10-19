"""Stand-ins shared across tests: the API routes' services, and topic data read by day."""

from datetime import date

from voices.explore.shapes import DayCount, Days, Map, MapPoint, TopicDay, TopicInfo, TopicInRange


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
