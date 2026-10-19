from datetime import date

import pytest
from langchain_core.messages import AIMessage

from voices.explore.day_range import DayRange
from voices.report.tasks import write_task
from voices.report.tools import ToolResult
from voices.report.writer import MAX_TOOL_CALLS, NoAnswer, ReportWriter

DAYS = DayRange(date(2026, 10, 12), date(2026, 10, 18))
REPORT = {
    "document": "## The period in brief\nSailors winterized.",
    "topics": [{"name": "Winterizing", "rank": 1, "direction": "rising"}],
}


class ScriptedModel:
    def __init__(self, replies):
        self.replies, self.offered = list(replies), []

    def bind_tools(self, tools):
        self.offered.append([getattr(t, "__name__", None) or t["function"]["name"] for t in tools])
        return self

    def invoke(self, messages):
        self.seen = list(messages)
        return self.replies.pop(0)


class FakeTools:
    def __init__(self):
        self.calls = []

    def run(self, name, arguments):
        self.calls.append(name)
        return ToolResult(f"result of {name}", ["p1", "p2"])


def call(name, arguments, call_id="1", tokens=(100, 20)):
    return AIMessage(
        content="",
        tool_calls=[{"name": name, "args": arguments, "id": call_id}],
        usage_metadata={
            "input_tokens": tokens[0],
            "output_tokens": tokens[1],
            "total_tokens": sum(tokens),
        },
    )


def said(text):
    return AIMessage(
        content=text, usage_metadata={"input_tokens": 5, "output_tokens": 5, "total_tokens": 10}
    )


class Events:
    def __init__(self):
        self.seen = []

    def __call__(self, event_type, **body):
        self.seen.append((event_type, body))


def test_without_tools_the_model_is_offered_only_the_answer():
    model = ScriptedModel([call("Report", REPORT)])

    written = ReportWriter(model, None, Events()).write(write_task(DAYS))

    assert model.offered == [["Report"]]
    assert written.answer.topics[0].name == "Winterizing"


def test_with_tools_the_model_may_search_first_and_each_call_is_streamed():
    tools, events = FakeTools(), Events()
    model = ScriptedModel([call("search", {"term": "winter"}), call("Report", REPORT, "2")])

    written = ReportWriter(model, tools, events).write(write_task(DAYS))

    assert tools.calls == ["search"]
    assert "search" in model.offered[0] and "Report" in model.offered[0]
    kinds = [kind for kind, _ in events.seen]
    assert kinds[:2] == ["tool.called", "tool.returned"]
    assert events.seen[1][1]["posts"] == 2
    assert written.tool_calls == 1


def test_tokens_and_time_are_counted_across_turns():
    model = ScriptedModel([call("search", {"term": "w"}), call("Report", REPORT, "2", (300, 400))])

    written = ReportWriter(model, FakeTools(), Events()).write(write_task(DAYS))

    assert (written.input_tokens, written.output_tokens) == (400, 420)
    assert written.seconds >= 0


def test_after_the_tool_call_cap_only_the_answer_is_offered():
    searches = [call("search", {"term": str(n)}, str(n)) for n in range(MAX_TOOL_CALLS)]
    model = ScriptedModel([*searches, call("Report", REPORT, "last")])

    ReportWriter(model, FakeTools(), Events()).write(write_task(DAYS))

    assert model.offered[-1] == ["Report"]


def test_a_malformed_answer_is_explained_and_asked_for_once_more():
    model = ScriptedModel([call("Report", {"document": "x"}), call("Report", REPORT, "2")])

    written = ReportWriter(model, None, Events()).write(write_task(DAYS))

    assert written.answer.document.startswith("## The period")
    assert "malformed" in model.seen[-1].content


def test_a_reply_in_plain_text_is_reminded_to_answer():
    model = ScriptedModel([said("Here is my report..."), call("Report", REPORT, "2")])

    ReportWriter(model, None, Events()).write(write_task(DAYS))

    assert "Report" in model.seen[-1].content


def test_no_answer_after_the_corrections_stops_with_an_error():
    model = ScriptedModel([said("no"), said("still no"), said("never")])

    with pytest.raises(NoAnswer):
        ReportWriter(model, None, Events()).write(write_task(DAYS))


def test_a_model_that_keeps_replying_in_plain_text_with_tools_still_stops():
    model = ScriptedModel([said(f"thinking {n}") for n in range(MAX_TOOL_CALLS + 5)])

    with pytest.raises(NoAnswer):
        ReportWriter(model, FakeTools(), Events()).write(write_task(DAYS))

    assert len(model.replies) > 0  # stopped before using every scripted reply
