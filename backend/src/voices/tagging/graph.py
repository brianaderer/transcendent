"""Runs the tagging agent on every cluster of a day in parallel, as a LangGraph fan-out."""

import operator
from typing import Annotated, Protocol, TypedDict

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from voices.tagging.decisions import ClusterBrief, DecidedCluster


class Decider(Protocol):
    def decide(self, brief: ClusterBrief) -> DecidedCluster: ...


class TaggingState(TypedDict):
    briefs: list[ClusterBrief]
    decided: Annotated[list[DecidedCluster], operator.add]


def decide_all(decider: Decider, briefs: list[ClusterBrief]) -> list[DecidedCluster]:
    if not briefs:
        return []
    final = _build_graph(decider).invoke({"briefs": briefs, "decided": []})
    order = {brief.name: n for n, brief in enumerate(briefs)}
    return sorted(final["decided"], key=lambda item: order[item.brief.name])


def _build_graph(decider: Decider):
    def one_cluster_each(state: TaggingState) -> list[Send]:
        return [Send("decide", {"brief": brief}) for brief in state["briefs"]]

    def decide(task: dict) -> dict:
        return {"decided": [decider.decide(task["brief"])]}

    graph = StateGraph(TaggingState)
    graph.add_node("decide", decide)
    graph.add_conditional_edges(START, one_cluster_each, ["decide"])
    graph.add_edge("decide", END)
    return graph.compile()
