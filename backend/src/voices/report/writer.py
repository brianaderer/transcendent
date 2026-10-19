"""One call of the report agent (atlas plate 60): the model may use its tools, up to a cap,
then answers through the task's answer tool. It is offered exactly the tools its tools object
carries: version A's one reading tool, or version B's four that retrieve (OPEN-39)."""

import time
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Protocol

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from pydantic import BaseModel, ValidationError

from voices.report.tasks import Task
from voices.report.tools import ToolResult

# A cap per call on the turns before only the answer is offered: each tool call spends one, and
# so does a reply that calls nothing, so a model that keeps searching or talking ends.
MAX_TOOL_CALLS = 20
# Once tools run out, a reply without a valid answer is corrected this many times.
CORRECTIONS = 1


class ChatModel(Protocol):
    def bind_tools(self, tools: list) -> "ChatModel": ...
    def invoke(self, messages: list[BaseMessage]) -> AIMessage: ...


class Tools(Protocol):
    @property
    def schemas(self) -> list[dict]: ...  # what the model is offered: one schema per tool
    def run(self, name: str, arguments: dict) -> ToolResult: ...


class Emit(Protocol):
    def __call__(self, event_type: str, **body: object) -> None: ...


class NoAnswer(Exception):
    pass


@dataclass
class Written:
    answer: BaseModel
    tool_calls: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    seconds: float = 0.0
    posts_seen: list[str] = field(default_factory=list)


class ReportWriter:
    def __init__(self, model: ChatModel, tools: Tools, emit: Emit):
        self.model = model
        self.tools = tools
        self.emit = emit

    def write(self, task: Task) -> Written:
        """Runs the task to its answer; raises NoAnswer if none comes after the corrections."""
        started = time.perf_counter()
        call = _Call(self.model, task, self.emit)
        answer = self._answer_with_tools(call) or self._insist_on_an_answer(call)
        call.written.answer = answer
        call.written.seconds = round(time.perf_counter() - started, 1)
        return call.written

    def _answer_with_tools(self, call: "_Call") -> BaseModel | None:
        while call.turns_spent < MAX_TOOL_CALLS:
            reply = call.take_turn([*self.tools.schemas, call.task.answer])
            answer = call.answer_in(reply)
            if answer:
                return answer
            call.respond(reply, self.tools)
        call.tell(f"No more tool calls; answer now by calling {call.answer_name}.")
        return None

    def _insist_on_an_answer(self, call: "_Call") -> BaseModel:
        for attempt in range(1 + CORRECTIONS):
            reply = call.take_turn([call.task.answer])
            answer = call.answer_in(reply)
            if answer:
                return answer
            if attempt < CORRECTIONS:
                call.respond(reply, None)
        raise NoAnswer(f"{call.task.phase}: no {call.answer_name} after being asked again")


class _Call:
    """One task's exchange with the model, with its running totals."""

    def __init__(self, model: ChatModel, task: Task, emit: Emit):
        self.model = model
        self.task = task
        self.emit = emit
        self.answer_name = task.answer.__name__
        self.messages: list[BaseMessage] = [HumanMessage(task.instructions)]
        self.written = Written(answer=task.answer.model_construct())
        self.empty_turns = 0  # replies that called nothing

    @property
    def turns_spent(self) -> int:
        return self.written.tool_calls + self.empty_turns

    def take_turn(self, offered: list) -> AIMessage:
        reply = self.model.bind_tools(offered).invoke(self.messages)
        self._count_usage(reply)
        self.messages.append(reply)
        return reply

    def answer_in(self, reply: AIMessage) -> BaseModel | None:
        for call in reply.tool_calls:
            if call["name"] == self.answer_name:
                try:
                    return self.task.answer.model_validate(call["args"])
                except ValidationError:
                    continue
        return None

    def respond(self, reply: AIMessage, tools: Tools | None) -> None:
        """Answers a reply that gave no valid answer: tool results, why an answer was
        malformed, or a reminder when it called nothing."""
        if not reply.tool_calls:
            self.empty_turns += 1
            self.tell(f"Answer by calling {self.answer_name}.")
        for call in reply.tool_calls:
            text = self._result_of(call, tools)
            self.messages.append(ToolMessage(text, tool_call_id=call["id"]))

    def tell(self, text: str) -> None:
        self.messages.append(HumanMessage(text))

    def _result_of(self, call: dict, tools: Tools | None) -> str:
        if call["name"] == self.answer_name:
            return _why_malformed(self.task.answer, call["args"])
        if tools is None:
            return f"No tools are available; answer by calling {self.answer_name}."
        return self._use_tool(call, tools)

    def _use_tool(self, call: dict, tools: Tools) -> str:
        self.emit("tool.called", phase=self.task.phase, tool=call["name"], arguments=call["args"])
        result = tools.run(call["name"], call["args"])
        self.written.tool_calls += 1
        self.written.posts_seen.extend(result.post_ids)
        self.emit(
            "tool.returned",
            phase=self.task.phase,
            tool=call["name"],
            posts=len(result.post_ids),
            post_ids=result.post_ids,
        )
        return result.text

    def _count_usage(self, reply: AIMessage) -> None:
        usage = reply.usage_metadata or {}
        self.written.input_tokens += usage.get("input_tokens", 0)
        self.written.output_tokens += usage.get("output_tokens", 0)


def _why_malformed(answer: type[BaseModel], arguments: dict) -> str:
    try:
        answer.model_validate(arguments)
    except ValidationError as error:
        return f"That answer was malformed: {error}. Call {answer.__name__} again."
    return f"Call {answer.__name__} again."


__all__: Sequence[str] = ["ReportWriter", "Written", "NoAnswer", "MAX_TOOL_CALLS"]
