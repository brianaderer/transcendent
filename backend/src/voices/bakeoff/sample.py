"""The bake-off's sample data, read from `tagging_cases.json`.

Real r/sailing threads from 23–26 August 2026 with their top comments, a short list of
existing topics written for the bake-off, and cases: a group of threads and the answer a
careful reader would give. Claude labelled the right answers by reading the threads; they
have not yet been reviewed by Brian (atlas plate 60).
"""

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import get_args

from voices.tagging.decisions import Action

CASES_FILE = Path(__file__).with_name("tagging_cases.json")
ACTIONS = get_args(Action)


@dataclass(frozen=True)
class Comment:
    source_id: str
    author: str
    body: str
    replies_to: str
    score: int


@dataclass(frozen=True)
class SampleThread:
    source_id: str
    title: str
    author: str
    day: date
    body: str
    comments: list[Comment]


@dataclass(frozen=True)
class SampleTopic:
    topic_id: int
    label: str
    description: str
    posts_last_week: int


@dataclass(frozen=True)
class Case:
    name: str
    thread_ids: list[str]
    expected: Action
    topic_id: int | None  # the topic to attach to; None unless expected is attach


@dataclass(frozen=True)
class SampleData:
    topics: list[SampleTopic]
    threads: dict[str, SampleThread]
    cases: list[Case]


def load_sample_data(path: Path = CASES_FILE) -> SampleData:
    raw = json.loads(path.read_text())
    return SampleData(
        topics=[_topic(topic) for topic in raw["topics"]],
        threads={source_id: _thread(source_id, t) for source_id, t in raw["threads"].items()},
        cases=[_case(case) for case in raw["cases"]],
    )


def topic_label(sample: SampleData, topic_id: int | None) -> str:
    labels = {topic.topic_id: topic.label for topic in sample.topics}
    return labels.get(topic_id, f"topic {topic_id}, which does not exist")


def _topic(raw: dict) -> SampleTopic:
    return SampleTopic(raw["id"], raw["label"], raw["description"], raw["posts_last_week"])


def _thread(source_id: str, raw: dict) -> SampleThread:
    comments = [
        Comment(c["id"], c["author"], c["body"], c["replies_to"], c["score"])
        for c in raw["comments"]
    ]
    day = date.fromisoformat(raw["day"])
    return SampleThread(source_id, raw["title"], raw["author"], day, raw["body"], comments)


def _case(raw: dict) -> Case:
    return Case(raw["name"], raw["threads"], raw["expected"], raw.get("topic_id"))
