"""The tagging agent's decision for one cluster: attach, mint or noise (atlas plate 60).

The agent may look things up with its tools before answering; it answers by calling the
`Decision` tool, so its answer always has the fixed shape. Every turn is logged in full
(atlas plate 05).
"""

import json
import logging
from typing import Protocol

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage, ToolMessage
from pydantic import ValidationError

from voices.log import log_event
from voices.tagging.decisions import ClusterBrief, DecidedCluster, Decision

MAX_TOOL_CALLS = 6  # enough to read around a cluster; past this the agent must decide
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
    def __init__(self, model: ChatModel, tools: Tools, max_tool_calls: int = MAX_TOOL_CALLS):
        self.model = model
        self.tools = tools
        self.max_tool_calls = max_tool_calls

    def decide(self, brief: ClusterBrief) -> DecidedCluster:
        prompt = render_brief(brief)
        messages: list[BaseMessage] = [SystemMessage(INSTRUCTIONS), HumanMessage(prompt)]
        for _ in range(self.max_tool_calls):
            decision = self._turn(brief, messages, tool_choice=None)
            if decision:
                return self._decided(brief, decision, prompt)
        decision = self._turn(brief, messages, tool_choice=DECIDE)
        if not decision:
            raise RuntimeError(
                f"cluster {brief.name}: no decision after {self.max_tool_calls} tools"
            )
        return self._decided(brief, decision, prompt)

    def _turn(
        self, brief: ClusterBrief, messages: list[BaseMessage], tool_choice: str | None
    ) -> Decision | None:
        """One model turn. Returns the decision if the model gave one; otherwise answers its
        tool calls (or reminds it to decide) and returns None."""
        reply = self.model.bind_tools(TOOLS, tool_choice=tool_choice).invoke(messages)
        log_event(
            logger,
            "tagging.turn",
            cluster=brief.name,
            reply=reply.content,
            tool_calls=reply.tool_calls,
        )
        messages.append(reply)
        if not reply.tool_calls:
            messages.append(HumanMessage(f"Decide now by calling {DECIDE}."))
            return None
        return self._answer_calls(reply, messages)

    def _answer_calls(self, reply: AIMessage, messages: list[BaseMessage]) -> Decision | None:
        for call in reply.tool_calls:
            if call["name"] == DECIDE:
                try:
                    return Decision.model_validate(call["args"])
                except ValidationError as error:
                    result = f"That decision was malformed: {error}. Call {DECIDE} again."
            else:
                result = self.tools.run(call["name"], call["args"])
            messages.append(ToolMessage(result, tool_call_id=call["id"]))
        return None

    def _decided(self, brief: ClusterBrief, decision: Decision, prompt: str) -> DecidedCluster:
        log_event(logger, "tagging.decided", cluster=brief.name, decision=decision.model_dump())
        model_name = getattr(self.model, "model_name", "unknown")
        return DecidedCluster(
            brief, decision, prompt=f"{INSTRUCTIONS}\n\n{prompt}", model=model_name
        )


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
