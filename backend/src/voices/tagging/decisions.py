"""What the tagging agent sees for each cluster, and what it decides (atlas plates 21, 60)."""

from collections.abc import Sequence
from dataclasses import dataclass, replace
from typing import Literal

import numpy as np
from pydantic import BaseModel, Field

# Two clusters minted in one run whose centres are this close are the same new conversation.
SAME_NEW_TOPIC_SIMILARITY = 0.90


class Decision(BaseModel):
    """The tagging agent's answer for one cluster of posts."""

    action: Literal["attach", "mint", "noise"] = Field(
        description="attach: these posts continue an existing topic; mint: a new topic; "
        "noise: chatter that belongs to no topic"
    )
    topic_id: int | None = Field(default=None, description="for attach: the topic's id")
    label: str | None = Field(default=None, description="for mint: a short topic name")
    description: str | None = Field(
        default=None, description="for mint: one or two sentences on what the topic is about"
    )
    reason: str = Field(description="one sentence on why")


@dataclass(frozen=True)
class TypicalPost:
    source_id: str
    author: str
    text: str


@dataclass(frozen=True)
class CandidateTopic:
    topic_id: int
    label: str
    description: str
    similarity: float
    posts_last_week: int


@dataclass(frozen=True)
class ClusterBrief:
    """Everything the agent is shown about one cluster."""

    name: str
    day: str
    centroid: Sequence[float]
    typical_posts: list[TypicalPost]
    candidates: list[CandidateTopic]
    member_ids: list[str]


@dataclass(frozen=True)
class DecidedCluster:
    brief: ClusterBrief
    decision: Decision
    prompt: str
    model: str
    merged_into: str | None = None  # a second mint for the same new topic joins the first


def settle_mints(decided: list[DecidedCluster]) -> list[DecidedCluster]:
    """Two clusters in one run may both mint a topic for the same new conversation; the later
    one joins the earlier one's new topic instead of creating a duplicate."""
    minted: list[DecidedCluster] = []
    settled = []
    for item in decided:
        twin = _close_mint(item, minted) if item.decision.action == "mint" else None
        if twin:
            item = replace(item, merged_into=twin.brief.name)
        elif item.decision.action == "mint":
            minted.append(item)
        settled.append(item)
    return settled


def _close_mint(item: DecidedCluster, minted: list[DecidedCluster]) -> DecidedCluster | None:
    return next(
        (
            m
            for m in minted
            if _cosine(item.brief.centroid, m.brief.centroid) >= SAME_NEW_TOPIC_SIMILARITY
        ),
        None,
    )


def _cosine(a: Sequence[float], b: Sequence[float]) -> float:
    a, b = np.asarray(a, dtype=float), np.asarray(b, dtype=float)
    size = np.linalg.norm(a) * np.linalg.norm(b)
    return float(a @ b / size) if size else 0.0
