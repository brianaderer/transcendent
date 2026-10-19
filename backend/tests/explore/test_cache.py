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


class FakeRedisWithKeys(FakeRedis):
    def scan_iter(self, match):
        assert match == "map:*"
        return [key for key in list(self.values) if key.startswith("map:")]

    def delete(self, key):
        self.values.pop(key)


def test_forgetting_the_maps_drops_every_map_and_nothing_else():
    redis = FakeRedisWithKeys()
    cache = RedisMapCache(redis)
    cache.put("map:a", "{}")
    cache.put("map:b", "{}")
    redis.set("run:x", "kept", ex=1)

    cache.forget_all()

    assert set(redis.values) == {"run:x"}
