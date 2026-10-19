import pytest
from langchain_core.messages import AIMessage

from voices.bakeoff.metering import CountingTools, Meter, MeteredModel, MissingUsage


class OneReplyModel:
    def __init__(self, usage):
        self.usage = usage

    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        return AIMessage(content="", usage_metadata=self.usage)


USAGE = {"input_tokens": 100, "output_tokens": 7, "total_tokens": 107}


def test_every_model_call_adds_its_tokens_to_the_meter():
    meter = Meter()
    model = MeteredModel(OneReplyModel(USAGE), meter).bind_tools([])

    model.invoke([])
    model.invoke([])

    assert (meter.model_calls, meter.tokens_in, meter.tokens_out) == (2, 200, 14)


def test_a_reply_without_token_counts_raises():
    with pytest.raises(MissingUsage):
        MeteredModel(OneReplyModel(None), Meter()).invoke([])


def test_every_tool_call_counts_as_a_look_up():
    class Tools:
        def run(self, name, arguments):
            return "ok"

    meter = Meter()
    CountingTools(Tools(), meter).run("search", {"term": "x"})

    assert meter.look_ups == 1
