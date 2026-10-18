import json
from datetime import date

from voices.db.tagging_store import PostNotFound
from voices.tagging.tools import TaggingTools

DAY = date(2026, 10, 15)


class FakeEmbedder:
    def embed_query(self, text):
        return [float(len(text))]


class FakeStore:
    def __init__(self):
        self.recorded = []
        self.searched = None

    def search_posts(self, embedding, first_day, last_day, limit):
        self.searched = (embedding, first_day, last_day, limit)
        return [{"post_id": "p1", "excerpt": "Impeller died"}]

    def lookup_post(self, post_id):
        if post_id == "invented":
            raise PostNotFound(post_id)
        return {"post_id": post_id, "text": "full text"}

    def search_topics(self, embedding, limit):
        return [{"topic_id": 3, "label": "Engines"}]

    def record_retrievals(self, post_ids, run, agent, tool):
        self.recorded.append((post_ids, run, agent, tool))


def test_search_looks_within_the_three_day_window_and_counts_what_it_returns():
    store = FakeStore()

    result = TaggingTools(store, FakeEmbedder(), DAY).run("search", {"term": "impeller"})

    assert json.loads(result) == [{"post_id": "p1", "excerpt": "Impeller died"}]
    assert store.searched == ([8.0], date(2026, 10, 13), DAY, 20)
    assert store.recorded == [(["p1"], "tagging-2026-10-15", "tagging", "search")]


def test_lookup_reads_one_post_and_counts_it():
    store = FakeStore()

    result = TaggingTools(store, FakeEmbedder(), DAY).run("lookup", {"post_id": "p9"})

    assert json.loads(result)["text"] == "full text"
    assert store.recorded == [(["p9"], "tagging-2026-10-15", "tagging", "lookup")]


def test_search_tags_finds_topics_by_meaning():
    result = TaggingTools(FakeStore(), FakeEmbedder(), DAY).run("search_tags", {"term": "engine"})

    assert json.loads(result) == [{"topic_id": 3, "label": "Engines"}]


def test_an_unknown_tool_is_answered_with_an_explanation_not_an_error():
    result = TaggingTools(FakeStore(), FakeEmbedder(), DAY).run("delete_everything", {})

    assert "no tool named delete_everything" in result


def test_looking_up_an_unknown_post_answers_the_agent_and_counts_nothing():
    store = FakeStore()

    result = TaggingTools(store, FakeEmbedder(), DAY).run("lookup", {"post_id": "invented"})

    assert "no post with id invented" in result
    assert store.recorded == []


def test_a_missing_argument_is_answered_not_raised():
    result = TaggingTools(FakeStore(), FakeEmbedder(), DAY).run("search", {})

    assert "needs the argument 'term'" in result
