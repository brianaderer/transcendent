"""Stand-ins shared by the API route tests."""

from datetime import date

from voices.explore.shapes import DayCount, Days, Map, MapPoint, TopicInRange


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

    def __init__(self, points=1):
        self.asked, self.points = None, points

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
        return Map(points=[map_point(n, days.start) for n in range(self.points)])
