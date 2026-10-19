import pytest
from langchain_core.messages import AIMessage

from voices.tagging.decider import NoDecision, ToolLoopDecider
from voices.tagging.decisions import ClusterBrief, TypicalPost


class ScriptedModel:
    """Stand-in chat model: answers with the next scripted message, records what it saw."""

    model_name = "scripted"

    def __init__(self, replies):
        self.replies = list(replies)
        self.seen = []
        self.tool_choice = None

    def bind_tools(self, tools, tool_choice=None):
        self.tool_choice = tool_choice
        return self

    def invoke(self, messages):
        self.seen.append(list(messages))
        return self.replies.pop(0)


class FakeTools:
    def __init__(self):
        self.calls = []

    def run(self, name, arguments):
        self.calls.append((name, arguments))
        return f"result of {name}"


def call(name, arguments, call_id="1"):
    return AIMessage(content="", tool_calls=[{"name": name, "args": arguments, "id": call_id}])


DECIDE = {"action": "attach", "topic_id": 3, "reason": "Same impeller conversation."}
BRIEF = ClusterBrief("c1", "2026-10-15", [1.0], [TypicalPost("p1", "u", "Impeller died")], [], [])


def test_the_decision_is_taken_from_the_decide_tool():
    model = ScriptedModel([call("Decision", DECIDE)])

    decided = ToolLoopDecider(model, "scripted", FakeTools(), max_look_ups=5).decide(BRIEF)

    assert decided.decision.action == "attach"
    assert decided.decision.topic_id == 3
    assert "Impeller died" in decided.prompt


def test_the_agent_may_look_things_up_before_deciding():
    tools = FakeTools()
    model = ScriptedModel([call("search", {"term": "impeller"}), call("Decision", DECIDE, "2")])

    ToolLoopDecider(model, "scripted", tools, max_look_ups=5).decide(BRIEF)

    assert tools.calls == [("search", {"term": "impeller"})]
    assert "result of search" in str(model.seen[-1][-1].content)


def test_at_the_look_up_limit_the_agent_must_decide():
    tools = FakeTools()
    model = ScriptedModel([call("search", {"term": "x"}), call("Decision", DECIDE, "2")])

    ToolLoopDecider(model, "scripted", tools, max_look_ups=1).decide(BRIEF)

    assert model.tool_choice == "Decision"


def test_a_malformed_decision_is_answered_and_the_agent_tries_again():
    model = ScriptedModel(
        [call("Decision", {"action": "maybe", "reason": "?"}), call("Decision", DECIDE, "2")]
    )

    decided = ToolLoopDecider(model, "scripted", FakeTools(), max_look_ups=5).decide(BRIEF)

    assert decided.decision.topic_id == 3
    assert "malformed" in str(model.seen[-1][-1].content)


def test_a_reply_in_plain_text_gets_a_reminder_to_decide():
    model = ScriptedModel([AIMessage(content="Hmm, these look related."), call("Decision", DECIDE)])

    ToolLoopDecider(model, "scripted", FakeTools(), max_look_ups=5).decide(BRIEF)

    assert "Decide now" in str(model.seen[-1][-1].content)


def test_by_default_the_agent_gets_three_look_ups_then_must_decide():
    tools = FakeTools()
    look_ups = [call("search", {"term": f"t{n}"}, str(n)) for n in range(3)]
    model = ScriptedModel([*look_ups, call("Decision", DECIDE, "3")])

    ToolLoopDecider(model, "scripted", tools).decide(BRIEF)

    assert len(tools.calls) == 3
    assert model.tool_choice == "Decision"


def test_several_look_ups_in_one_turn_count_toward_the_limit():
    tools = FakeTools()
    searches = AIMessage(
        content="",
        tool_calls=[{"name": "search", "args": {"term": f"t{n}"}, "id": str(n)} for n in range(4)],
    )
    model = ScriptedModel([searches, call("Decision", DECIDE, "9")])

    ToolLoopDecider(model, "scripted", tools).decide(BRIEF)

    assert len(tools.calls) == 3
    assert "No look-ups left" in str(model.seen[-1][-1].content)
    assert model.tool_choice == "Decision"


def test_no_decision_even_when_forced_stops_with_an_error():
    model = ScriptedModel([AIMessage(content="thinking"), AIMessage(content="still thinking")])

    with pytest.raises(NoDecision):
        ToolLoopDecider(model, "scripted", FakeTools(), max_look_ups=1).decide(BRIEF)


def test_the_model_name_given_is_recorded_with_the_decision():
    model = ScriptedModel([call("Decision", DECIDE)])

    decided = ToolLoopDecider(model, "anthropic/claude-sonnet-5.5", FakeTools()).decide(BRIEF)

    assert decided.model == "anthropic/claude-sonnet-5.5"


def test_a_valid_decision_after_a_malformed_one_in_the_same_reply_is_used():
    reply = AIMessage(
        content="",
        tool_calls=[
            {"name": "Decision", "args": {"action": "maybe", "reason": "?"}, "id": "1"},
            {"name": "Decision", "args": DECIDE, "id": "2"},
        ],
    )

    decided = ToolLoopDecider(ScriptedModel([reply]), "scripted", FakeTools()).decide(BRIEF)

    assert decided.decision.topic_id == 3


def test_every_answer_sent_to_the_model_is_logged(caplog):
    caplog.set_level("INFO")
    model = ScriptedModel([call("search", {"term": "impeller"}), call("Decision", DECIDE, "2")])

    ToolLoopDecider(model, "scripted", FakeTools()).decide(BRIEF)

    [answer] = [r for r in caplog.records if r.getMessage() == "tagging.answer"]
    assert (answer.tool, answer.content) == ("search", "result of search")
