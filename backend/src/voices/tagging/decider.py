"""The tagging agent's decision for one cluster: attach, mint or noise (atlas plate 60).

The agent may look things up with its tools before answering; it answers by calling the
`Decision` tool, so its answer always has the fixed shape. Every model turn and every tool
result is logged in full (atlas plate 05).
"""

import json
import logging
from typing import Protocol

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from pydantic import ValidationError

from voices.log import log_event
from voices.tagging.decisions import ClusterBrief, DecidedCluster, Decision

MAX_TURNS_BEFORE_DECIDING = 6  # enough to read around a cluster; then it must decide
DECIDE = "Decision"

INSTRUCTIONS = """You sort conversations from r/sailing into topics.

You are shown one cluster: posts from the last three days that an algorithm grouped because
they mean similar things, and the existing topics closest to it. Decide one of:
- attach: the posts continue one of the existing topics shown (give its topic_id);
- mint: they are a real conversation that no existing topic covers (give a short label and a
  one- or two-sentence description that would fit next week's posts on it too);
- noise: they share no real subject (jokes, greetings, unrelated one-liners).

Prefer attach when an existing topic fits; a topic is a subject, not a single thread. You may
use the tools to read more before deciding, then call Decision exactly once."""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Find posts from these three days closest in meaning to a term.",
            "parameters": {
                "type": "object",
                "properties": {"term": {"type": "string"}},
                "required": ["term"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "lookup",
            "description": "Read one post or comment in full, with its thread title and the "
            "id of what it replies to.",
            "parameters": {
                "type": "object",
                "properties": {"post_id": {"type": "string"}},
                "required": ["post_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_tags",
            "description": "Find existing topics closest in meaning to a term, beyond the ones "
            "shown, before minting a topic that may already exist.",
            "parameters": {
                "type": "object",
                "properties": {"term": {"type": "string"}},
                "required": ["term"],
            },
        },
    },
    Decision,
]

logger = logging.getLogger(__name__)


class ChatModel(Protocol):
    def bind_tools(self, tools: list, tool_choice: str | None = None) -> "ChatModel": ...
    def invoke(self, messages: list[BaseMessage]) -> AIMessage: ...


class Tools(Protocol):
    def run(self, name: str, arguments: dict) -> str: ...


class ToolLoopDecider:
    def __init__(
        self,
        model: ChatModel,
        model_name: str,
        tools: Tools,
        max_turns: int = MAX_TURNS_BEFORE_DECIDING,
    ):
        self.model = model
        self.model_name = model_name
        self.tools = tools
        self.max_turns = max_turns

    def decide(self, brief: ClusterBrief) -> DecidedCluster:
        """Lets the agent look around for up to max_turns turns, then makes it decide."""
        conversation = _Conversation(self.model, self.tools, brief)
        for _ in range(self.max_turns):
            reply = conversation.take_turn(tool_choice=None)
            decision = _decision_in(reply)
            if decision:
                return self._decided(conversation, decision)
            conversation.answer(reply)
        decision = _decision_in(conversation.take_turn(tool_choice=DECIDE))
        if not decision:
            raise NoDecision(f"cluster {brief.name}: no decision after {self.max_turns} turns")
        return self._decided(conversation, decision)

    def _decided(self, conversation: "_Conversation", decision: Decision) -> DecidedCluster:
        brief = conversation.brief
        log_event(logger, "tagging.decided", cluster=brief.name, decision=decision.model_dump())
        prompt = f"{INSTRUCTIONS}\n\n{conversation.prompt}"
        return DecidedCluster(brief, decision, prompt, self.model_name)


class _Conversation:
    """One cluster's exchange with the model: every message, and every one of them logged."""

    def __init__(self, model: ChatModel, tools: Tools, brief: ClusterBrief):
        self.model = model
        self.tools = tools
        self.brief = brief
        self.prompt = render_brief(brief)
        self.messages: list[BaseMessage] = [SystemMessage(INSTRUCTIONS), HumanMessage(self.prompt)]

    def take_turn(self, tool_choice: str | None) -> AIMessage:
        reply = self.model.bind_tools(TOOLS, tool_choice=tool_choice).invoke(self.messages)
        self._log("tagging.turn", reply=reply.content, tool_calls=reply.tool_calls)
        self.messages.append(reply)
        return reply

    def answer(self, reply: AIMessage) -> None:
        """Answers every call in a reply that made no valid decision: tool calls get their
        results, a malformed decision gets the reason; a reply with no calls gets a reminder."""
        if not reply.tool_calls:
            self._say(HumanMessage(f"Decide now by calling {DECIDE}."))
        for call in reply.tool_calls:
            self._say(
                ToolMessage(self._result_of(call), tool_call_id=call["id"]), tool=call["name"]
            )

    def _result_of(self, call: dict) -> str:
        if call["name"] != DECIDE:
            return self.tools.run(call["name"], call["args"])
        try:
            _parse_decision(call["args"])
        except MalformedDecision as error:
            return str(error)
        return f"Only one {DECIDE} call is read per turn; call it once."

    def _say(self, message: BaseMessage, tool: str | None = None) -> None:
        self._log("tagging.answer", tool=tool, content=message.content)
        self.messages.append(message)

    def _log(self, event: str, **fields: object) -> None:
        log_event(logger, event, cluster=self.brief.name, **fields)


class NoDecision(Exception):
    pass


class MalformedDecision(Exception):
    pass


def _decision_in(reply: AIMessage) -> Decision | None:
    """The reply's decision, if it made a valid one."""
    for call in reply.tool_calls:
        if call["name"] == DECIDE:
            try:
                return _parse_decision(call["args"])
            except MalformedDecision:
                return None
    return None


def _parse_decision(arguments: dict) -> Decision:
    try:
        return Decision.model_validate(arguments)
    except ValidationError as error:
        raise MalformedDecision(
            f"That decision was malformed: {error}. Call {DECIDE} again."
        ) from error


def render_brief(brief: ClusterBrief) -> str:
    """The cluster as the agent reads it."""
    return json.dumps(
        {
            "day": brief.day,
            "posts_in_cluster": len(brief.member_ids),
            "typical_posts": [vars(post) for post in brief.typical_posts],
            "nearest_existing_topics": [vars(topic) for topic in brief.candidates],
        },
        indent=1,
    )
