import json

from voices.events import RedisEvents, as_server_sent_event


class FakeRedis:
    def __init__(self):
        self.published = []

    def publish(self, channel, message):
        self.published.append((channel, json.loads(message)))


def test_an_event_is_published_on_its_streams_channel_with_its_type():
    redis = FakeRedis()

    RedisEvents(redis).emit("ingestion", "day.finished", day="2026-10-15")

    [(channel, event)] = redis.published
    assert channel == "events:ingestion"
    assert event["type"] == "day.finished"
    assert event["day"] == "2026-10-15"
    assert event["time"].endswith("Z")


def test_an_event_is_framed_for_the_browser_as_one_server_sent_event():
    assert as_server_sent_event('{"type": "x"}') == 'data: {"type": "x"}\n\n'
