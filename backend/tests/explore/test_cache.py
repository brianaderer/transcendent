from voices.explore.cache import KEPT_SECONDS, RedisMapCache


class FakeRedis:
    def __init__(self):
        self.values, self.expiries = {}, {}

    def get(self, key):
        return self.values.get(key)

    def set(self, key, value, ex):
        self.values[key], self.expiries[key] = value.encode(), ex


def test_a_map_put_in_is_read_back_as_text_and_ages_out():
    redis = FakeRedis()
    cache = RedisMapCache(redis)

    cache.put("map:a", '{"points": []}')

    assert cache.get("map:a") == '{"points": []}'
    assert redis.expiries["map:a"] == KEPT_SECONDS


def test_a_map_never_put_in_is_missing():
    assert RedisMapCache(FakeRedis()).get("map:b") is None
