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
        prompt = render_brief(brief)
        messages: list[BaseMessage] = [SystemMessage(INSTRUCTIONS), HumanMessage(prompt)]
        for _ in range(self.max_turns):
            decision = self._decision_after_turn(brief, messages, tool_choice=None)
            if decision:
                return self._decided(brief, decision, prompt)
        decision = self._decision_after_turn(brief, messages, tool_choice=DECIDE)
        if not decision:
            raise NoDecision(f"cluster {brief.name}: no decision after {self.max_turns} turns")
        return self._decided(brief, decision, prompt)

    def _decision_after_turn(
        self, brief: ClusterBrief, messages: list[BaseMessage], tool_choice: str | None
    ) -> Decision | None:
        reply = self._turn(brief, messages, tool_choice)
        decision = self._decision_in(reply, messages)
        if decision is None:
            self._answer_tool_calls(brief, reply, messages)
        return decision

    def _turn(
        self, brief: ClusterBrief, messages: list[BaseMessage], tool_choice: str | None
    ) -> AIMessage:
        reply = self.model.bind_tools(TOOLS, tool_choice=tool_choice).invoke(messages)
        log_event(
            logger,
            "tagging.turn",
            cluster=brief.name,
            reply=reply.content,
            tool_calls=reply.tool_calls,
        )
        messages.append(reply)
        return reply

    def _decision_in(self, reply: AIMessage, messages: list[BaseMessage]) -> Decision | None:
        """The decision, if the reply made one. A malformed one is answered so the model can
        try again."""
        for call in reply.tool_calls:
            if call["name"] == DECIDE:
                try:
                    return _parse_decision(call["args"])
                except MalformedDecision as error:
                    messages.append(ToolMessage(str(error), tool_call_id=call["id"]))
        return None

    def _answer_tool_calls(
        self, brief: ClusterBrief, reply: AIMessage, messages: list[BaseMessage]
    ) -> None:
        if not reply.tool_calls:
            messages.append(HumanMessage(f"Decide now by calling {DECIDE}."))
        for call in reply.tool_calls:
            if call["name"] != DECIDE:
                result = self.tools.run(call["name"], call["args"])
                log_event(
                    logger,
                    "tagging.tool_result",
                    cluster=brief.name,
                    tool=call["name"],
                    arguments=call["args"],
                    result=result,
                )
                messages.append(ToolMessage(result, tool_call_id=call["id"]))

    def _decided(self, brief: ClusterBrief, decision: Decision, prompt: str) -> DecidedCluster:
        log_event(logger, "tagging.decided", cluster=brief.name, decision=decision.model_dump())
        return DecidedCluster(brief, decision, f"{INSTRUCTIONS}\n\n{prompt}", self.model_name)


class NoDecision(Exception):
    pass


class MalformedDecision(Exception):
    pass


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
