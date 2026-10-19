"""Both versions of a comparison run at once, as a LangGraph fan-out (atlas plate 60): one
branch per version, each writing that version's report and prediction. Inside a branch the
writer's tool loop stays a plain loop over LangChain, as the tagging agent's does inside its
fan-out."""

import operator
from collections.abc import Callable
from typing import Annotated, TypedDict, TypeVar

from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from voices.report.versions import VERSIONS, Version

MAX_PARALLEL_VERSIONS = len(VERSIONS)  # every version at once: each mostly waits on the model

Result = TypeVar("Result")


class VersionsState(TypedDict):
    finished: Annotated[list[tuple[Version, object]], operator.add]  # each version's result
    failed: Annotated[list[Exception], operator.add]


def every_version_at_once(work: Callable[[Version], Result]) -> list[Result]:
    """Runs the work for each version in its own branch, and answers in the order of
    VERSIONS. Each branch sees the caller's context variables (LangGraph runs it in a copy of
    them), so its log lines carry the run's trace id. A version's failure is raised once both
    branches are done, exactly as it was raised."""
    config = {"max_concurrency": MAX_PARALLEL_VERSIONS}
    final = _build_graph(work).invoke({"finished": [], "failed": []}, config=config)
    if final["failed"]:
        raise final["failed"][0]
    by_version = dict(final["finished"])
    return [by_version[version] for version in VERSIONS]  # type: ignore[misc]


def _build_graph(work: Callable[[Version], object]):
    def one_branch_each(_state: VersionsState) -> list[Send]:
        return [Send("version", {"version": version}) for version in VERSIONS]

    def version(task: dict) -> dict:
        # Carried out of the graph rather than raised in it: LangGraph appends the task's name
        # and id to a node's error message, and the message is the reason the page shows.
        try:
            return {"finished": [(task["version"], work(task["version"]))]}
        except Exception as error:
            return {"failed": [error]}

    graph = StateGraph(VersionsState)
    graph.add_node("version", version)
    graph.add_conditional_edges(START, one_branch_each, ["version"])
    graph.add_edge("version", END)
    return graph.compile()
