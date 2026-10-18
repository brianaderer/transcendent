from langchain_core.messages import AIMessage

from voices.tagging.decider import ToolLoopDecider
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

    decided = ToolLoopDecider(model, FakeTools(), max_tool_calls=5).decide(BRIEF)

    assert decided.decision.action == "attach"
    assert decided.decision.topic_id == 3
    assert "Impeller died" in decided.prompt


def test_the_agent_may_look_things_up_before_deciding():
    tools = FakeTools()
    model = ScriptedModel([call("search", {"term": "impeller"}), call("Decision", DECIDE, "2")])

    ToolLoopDecider(model, tools, max_tool_calls=5).decide(BRIEF)

    assert tools.calls == [("search", {"term": "impeller"})]
    assert "result of search" in str(model.seen[-1][-1].content)


def test_at_the_tool_call_limit_the_agent_must_decide():
    tools = FakeTools()
    model = ScriptedModel([call("search", {"term": "x"}), call("Decision", DECIDE, "2")])

    ToolLoopDecider(model, tools, max_tool_calls=1).decide(BRIEF)

    assert model.tool_choice == "Decision"
