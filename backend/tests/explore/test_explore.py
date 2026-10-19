import json
from datetime import date

from voices.explore.day_range import DayRange
from voices.explore.explore import Explore
from voices.explore.shapes import DayCount, MapPost, TopicDay, TopicInfo

START, END = date(2026, 10, 12), date(2026, 10, 14)
DAYS = DayRange(START, END)


def topic(topic_id, first_seen=date(2026, 9, 1)):
    return TopicInfo(id=topic_id, label=f"t{topic_id}", description="d", first_seen=first_seen)


def map_post(source_id, topic_id=1):
    return MapPost(
        id=source_id,
        thread_id="th",
        kind="comment",
        author="salty",
        day=START,
        thread_title="Impellers",
        excerpt="Carry a spare.",
        thread_topic_id=topic_id,
        embedding=[1.0, 0.0],
    )


class FakeData:
    def __init__(self, topic_days=(), topics=(), posts=(), latest=date(2026, 10, 18)):
        self._topic_days, self._topics, self._posts = list(topic_days), list(topics), list(posts)
        self.latest, self.asked = latest, []

    def posts_per_day(self):
        return [DayCount(day=START, posts=4)]

    def latest_day(self):
        return self.latest

    def topic_days(self, first_day, last_day):
        self.asked.append((first_day, last_day))
        return [d for d in self._topic_days if first_day <= d.day <= last_day]

    def topics(self, ids):
        return [t for t in self._topics if t.id in ids]

    def posts_in(self, first_day, last_day):
        return self._posts


class FakeCache:
    def __init__(self):
        self.values = {}

    def get(self, key):
        return self.values.get(key)

    def put(self, key, value):
        self.values[key] = value


class CountingFlatten:
    def __init__(self):
        self.calls = 0

    def __call__(self, vectors):
        self.calls += 1
        return [(float(i), 0.0) for i, _ in enumerate(vectors)]


def explore(data, flatten=None, cache=None):
    return Explore(data, cache or FakeCache(), flatten or CountingFlatten())


def day(topic_id, on, engagement, posts=1):
    return TopicDay(topic_id=topic_id, day=on, engagement=engagement, posts=posts)


def test_days_are_the_posts_per_day_and_the_latest_loaded_day():
    days = explore(FakeData()).days()

    assert days.days == [DayCount(day=START, posts=4)]
    assert days.latest_day == date(2026, 10, 18)


def test_topics_read_the_range_and_the_period_of_the_same_length_before_it():
    data = FakeData()

    explore(data).topics(DAYS)

    assert data.asked == [(date(2026, 10, 9), END)]


def test_a_topic_has_one_number_a_day_with_zeros_on_quiet_days():
    data = FakeData([day(1, START, 5), day(1, END, 2)], [topic(1)])

    [only] = explore(data).topics(DAYS)

    assert only.daily == [5, 0, 2]
    assert (only.engagement, only.posts) == (7, 2)


def test_topics_come_busiest_first_and_quiet_ones_are_left_out():
    days = [day(1, START, 2), day(2, START, 9), day(3, date(2026, 10, 10), 4)]
    data = FakeData(days, [topic(1), topic(2), topic(3)])

    assert [t.id for t in explore(data).topics(DAYS)] == [2, 1]


def test_each_topic_is_badged_against_the_period_before():
    days = [day(1, date(2026, 10, 10), 10), day(1, START, 20), day(2, START, 3)]
    data = FakeData(days, [topic(1), topic(2, first_seen=END)])

    badges = {t.id: t.direction for t in explore(data).topics(DAYS)}

    assert badges == {1: "rising", 2: "new"}


def test_the_map_places_every_post_with_its_topic():
    data = FakeData(posts=[map_post("a"), map_post("b", topic_id=None)])

    points = explore(data).map(DAYS).points

    assert [(p.id, p.x, p.thread_topic_id) for p in points] == [("a", 0.0, 1), ("b", 1.0, None)]


def test_a_range_is_flattened_once_until_a_new_day_is_loaded():
    data, flatten, cache = FakeData(posts=[map_post("a")]), CountingFlatten(), FakeCache()
    service = explore(data, flatten, cache)

    service.map(DAYS)
    service.map(DAYS)
    data.latest = date(2026, 10, 19)
    service.map(DAYS)

    assert flatten.calls == 2


def test_the_cached_map_is_the_map_as_sent():
    cache = FakeCache()
    sent = explore(FakeData(posts=[map_post("a")]), cache=cache).map(DAYS)

    [stored] = cache.values.values()

    assert json.loads(stored) == json.loads(sent.model_dump_json())


def test_a_topic_also_has_one_number_a_day_for_the_period_its_badge_compares_with():
    days = [day(1, date(2026, 10, 9), 4), day(1, date(2026, 10, 11), 6), day(1, START, 5)]
    data = FakeData(days, [topic(1)])

    [only] = explore(data).topics(DAYS)

    assert only.daily_before == [4, 0, 6]
