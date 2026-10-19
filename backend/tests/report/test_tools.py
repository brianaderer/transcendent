import json
from datetime import date

from voices.db.tagging_store import PostNotFound
from voices.explore.day_range import DayRange
from voices.report.tools import ReportTools

WINDOW = DayRange(date(2026, 10, 12), date(2026, 10, 18))


class FakeStore:
    def __init__(self):
        self.searched, self.recorded = [], []

    def search_posts(self, embedding, first_day, last_day, limit):
        self.searched.append((embedding, first_day, last_day, limit))
        return [{"post_id": "p1", "text": "Impellers"}, {"post_id": "p2", "text": "Spares"}]

    def lookup_post(self, post_id):
        if post_id == "gone":
            raise PostNotFound(post_id)
        posted = date(2026, 10, 25) if post_id == "later" else date(2026, 10, 14)
        return {"post_id": post_id, "date": posted, "text": "Carry a spare."}

    def record_retrievals(self, post_ids, run, agent, tool):
        self.recorded.append((list(post_ids), run, agent, tool))


class FakeEmbedder:
    def embed_query(self, text):
        return [float(len(text))]


def tools(store, trends=lambda: [{"label": "Impellers", "expected": 12.0}]):
    return ReportTools(store, FakeEmbedder(), WINDOW, "run-1", trends)


def test_search_looks_only_inside_the_window_and_counts_each_hit_as_the_report_agents():
    store = FakeStore()

    result = tools(store).run("search", {"term": "impeller"})

    assert store.searched[0][1:3] == (WINDOW.start, WINDOW.end)
    assert result.post_ids == ["p1", "p2"]
    assert store.recorded == [(["p1", "p2"], "run-1", "report", "search")]
    assert json.loads(result.text)[0]["post_id"] == "p1"


def test_a_lookup_inside_the_window_is_read_in_full_and_counted():
    store = FakeStore()

    result = tools(store).run("lookup", {"post_id": "p7"})

    assert json.loads(result.text)["text"] == "Carry a spare."
    assert store.recorded == [(["p7"], "run-1", "report", "lookup")]


def test_a_post_written_after_the_window_is_refused_so_a_prediction_cannot_peek():
    store = FakeStore()

    result = tools(store).run("lookup", {"post_id": "later"})

    assert "after" in result.text and result.post_ids == []
    assert store.recorded == []


def test_an_unknown_post_is_answered_not_raised():
    assert "no post" in tools(FakeStore()).run("lookup", {"post_id": "gone"}).text


def test_topic_trends_are_what_the_run_hands_in():
    result = tools(FakeStore()).run("topic_trends", {})

    assert json.loads(result.text) == [{"label": "Impellers", "expected": 12.0}]


def test_upcoming_events_searches_the_window_for_dated_plans():
    store = FakeStore()

    result = tools(store).run("upcoming_events", {})

    assert store.searched[0][1:3] == (WINDOW.start, WINDOW.end)
    assert result.post_ids == ["p1", "p2"]


def test_a_missing_argument_or_unknown_tool_is_explained():
    assert "needs the argument 'term'" in tools(FakeStore()).run("search", {}).text
    assert "no tool named" in tools(FakeStore()).run("weather", {}).text
