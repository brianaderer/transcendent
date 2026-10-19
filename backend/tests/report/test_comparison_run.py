from datetime import date

from langchain_core.messages import AIMessage

from voices.explore.day_range import DayRange
from voices.explore.shapes import TopicDay, TopicInfo
from voices.report.comparison_run import ComparisonRun, RunParts

DAYS = DayRange(date(2026, 10, 12), date(2026, 10, 18))
REPORT = {
    "document": "## The period in brief\\nWinter work.",
    "topics": [
        {"name": "Winterizing boats", "rank": 1, "direction": "rising"},
        {"name": "Space sailing", "rank": 2, "direction": "new"},
    ],
}
PREDICTION = {
    "predicted": [{"name": "Winterizing boats", "direction": "rising"}],
    "reasoning": "Haul-out season.",
}


class AnsweringModel:
    """Answers each task at once; offered tools, it searches (or reads) once first. Records
    what it saw."""

    def __init__(self):
        self.tasks = []
        self.offered_tools = []
        self._tools = []

    def bind_tools(self, tools):
        self._tools = [getattr(t, "__name__", None) or t["function"]["name"] for t in tools]
        return self

    def invoke(self, messages):
        first = messages[0].content
        if len(messages) == 1:
            self.tasks.append(first)
            self.offered_tools.append(self._tools)
        answer = "Report" if "Report" in self._tools else "Prediction"
        used_a_tool = any(getattr(m, "tool_call_id", None) for m in messages)
        if "search" in self._tools and not used_a_tool:
            return _call("search", {"term": "winter"})
        if "read_posts" in self._tools and not used_a_tool:
            return _call("read_posts", {})
        return _call(answer, REPORT if answer == "Report" else PREDICTION)


def _call(name, arguments):
    return AIMessage(
        content="",
        tool_calls=[{"name": name, "args": arguments, "id": name}],
        usage_metadata={"input_tokens": 10, "output_tokens": 5, "total_tokens": 15},
    )


class FakeData:
    """Two topics: winterizing, busy in the range; anchoring, quiet."""

    def __init__(self):
        self.searched_windows, self.read_windows, self.retrieval_tools = [], [], []

    def topic_days(self, first_day, last_day):
        rows = [TopicDay(topic_id=1, day=date(2026, 10, 14), engagement=30, posts=10)]
        rows.append(TopicDay(topic_id=2, day=date(2026, 9, 20), engagement=4, posts=2))
        return [r for r in rows if first_day <= r.day <= last_day]

    def topics(self, ids):
        everything = {
            1: TopicInfo(
                id=1, label="Winterizing", description="Haul-out", first_seen=date(2026, 9, 1)
            ),
            2: TopicInfo(
                id=2, label="Anchoring", description="Anchors", first_seen=date(2026, 9, 1)
            ),
        }
        return [everything[i] for i in ids if i in everything]

    def search_posts(self, embedding, first_day, last_day, limit):
        self.searched_windows.append((first_day, last_day))
        return [{"post_id": "p1", "text": "Shrink wrap time."}]

    def lookup_post(self, post_id):
        return {"post_id": post_id, "date": date(2026, 10, 14)}

    def sample_posts(self, days, limit, seed, exclude_ids):
        self.read_windows.append((days.start, days.end))
        return [{"post_id": "p9", "text": "Hauled out today."}]

    def record_retrievals(self, post_ids, run, agent, tool):
        self.retrieval_tools.append(tool)


class MeaningEmbedder:
    """Names about winter land on the winterizing topic; anything else lands nowhere."""

    def embed_query(self, text):
        return [1.0, 0.0]

    def embed_for_comparison(self, texts):
        return [
            [1.0, 0.0] if "inter" in t else [0.0, 1.0] if "Anchor" in t else [0.6, -0.8]
            for t in texts
        ]


def run(model=None, data=None, events=None):
    parts = RunParts(model or AnsweringModel(), "test-model", data or FakeData(), MeaningEmbedder())
    emit = (
        (lambda kind, **body: events.append((kind, body)))
        if events is not None
        else (lambda *a, **k: None)
    )
    return ComparisonRun(parts, emit).run("abc123", DAYS)


def test_both_versions_get_the_same_words_and_only_b_gets_retrieval():
    model = AnsweringModel()

    run(model)

    # Both versions run at once, so tell them apart by their tools, not by the order of calls.
    calls = list(zip(model.tasks, model.offered_tools, strict=True))
    by_a = [(task, tools) for task, tools in calls if "read_posts" in tools]
    by_b = [(task, tools) for task, tools in calls if "search" in tools]
    assert len(by_a) == len(by_b) == 2
    assert sorted(task for task, _ in by_a) == sorted(task for task, _ in by_b)
    assert sorted(tools for _, tools in by_a) == [
        ["read_posts", "Prediction"],
        ["read_posts", "Report"],
    ]
    assert all("read_posts" not in tools for _, tools in by_b)


def test_version_a_reads_only_before_the_range_when_predicting_as_b_searches():
    data = FakeData()

    run(data=data)

    assert data.read_windows == data.searched_windows
    assert data.read_windows[1][1] == date(2026, 10, 11)


def test_version_a_reads_are_not_counted_as_retrievals():
    data = FakeData()

    run(data=data)

    assert data.retrieval_tools == ["search", "search"]  # B's two searches, nothing of A's


def test_the_prediction_searches_only_before_the_range():
    data = FakeData()

    run(data=data)

    report_window, prediction_window = data.searched_windows
    assert report_window == (DAYS.start, DAYS.end)
    assert prediction_window[1] == date(2026, 10, 11)


def test_both_versions_are_scored_against_the_same_answer_key():
    result = run()

    a, b = result.versions
    assert [t.label for t in result.main_topics] == ["Winterizing"]
    assert a.scores.topics_found == 1 and a.scores.topics_invented == 1
    assert a.report_matches == {"Winterizing boats": 1, "Space sailing": None}
    assert (b.tool_calls, a.tool_calls) == (2, 2)


def test_the_run_is_announced_live_from_start_to_scores():
    events = []

    run(events=events)

    kinds = [kind for kind, _ in events]
    assert kinds[0] == "run.started" and kinds[-1] == "measurement.done"
    assert "run.finished" not in kinds  # announced once the result is kept (report_task)
    tool_calls = [body for kind, body in events if kind == "tool.called"]
    assert {body["version"] for body in tool_calls} == {"A", "B"}
    assert {body["tool"] for body in tool_calls if body["version"] == "A"} == {"read_posts"}
