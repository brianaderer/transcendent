"""Counts what one decision costs: model calls, tokens read and written, and look-ups."""

from dataclasses import dataclass

from langchain_core.messages import AIMessage, BaseMessage

from voices.tagging.decider import ChatModel, Tools


@dataclass
class Meter:
    model_calls: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    look_ups: int = 0


class MissingUsage(Exception):
    """The model's reply carried no token counts, so the cost can't be measured."""


class MeteredModel:
    """A chat model that adds each reply's token counts to a meter."""

    def __init__(self, model: ChatModel, meter: Meter):
        self.model = model
        self.meter = meter

    def bind_tools(self, tools: list) -> "MeteredModel":
        return MeteredModel(self.model.bind_tools(tools), self.meter)

    def invoke(self, messages: list[BaseMessage]) -> AIMessage:
        reply = self.model.invoke(messages)
        if not reply.usage_metadata:
            raise MissingUsage("the model's reply has no token counts")
        self.meter.model_calls += 1
        self.meter.tokens_in += reply.usage_metadata["input_tokens"]
        self.meter.tokens_out += reply.usage_metadata["output_tokens"]
        return reply


class CountingTools:
    def __init__(self, tools: Tools, meter: Meter):
        self.tools = tools
        self.meter = meter

    def run(self, name: str, arguments: dict) -> str:
        self.meter.look_ups += 1
        return self.tools.run(name, arguments)
