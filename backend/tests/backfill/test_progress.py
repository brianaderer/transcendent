from voices.backfill.progress import PROGRESS_KEY, RedisBackfillProgress


class FakeRedis:
    def __init__(self):
        self.values = {}

    def set(self, key, value):
        self.values[key] = value.encode()

    def get(self, key):
        return self.values.get(key)

    def exists(self, key):
        return int(key in self.values)

    def delete(self, key):
        self.values.pop(key, None)


def test_recorded_progress_reads_back_as_what_how_many_done_and_of_how_many():
    progress = RedisBackfillProgress(FakeRedis())

    progress.record("posts", 4120, 12682)

    assert progress.read() == {"what": "posts", "done": 4120, "total": 12682}
    assert progress.recorded()


def test_no_progress_is_read_when_no_backfill_is_under_way():
    progress = RedisBackfillProgress(FakeRedis())

    assert progress.read() is None
    assert not progress.recorded()


def test_cleared_progress_is_gone():
    redis = FakeRedis()
    progress = RedisBackfillProgress(redis)
    progress.record("threads", 1, 2)

    progress.clear()

    assert progress.read() is None
    assert PROGRESS_KEY not in redis.values
