"""The sample data held in memory behind the tagging tools' store interface, searched by
meaning with the real embedding model, so the agent's tools behave as they do on Postgres."""

from collections.abc import Sequence
from datetime import date
from typing import Protocol

import numpy as np

from voices.bakeoff.sample import Case, SampleData, SampleThread
from voices.db.tagging_store import EXCERPT_CHARACTERS, TYPICAL_POST_CHARACTERS, PostNotFound
from voices.tagging.day_tagging import CANDIDATE_TOPICS_SHOWN, TYPICAL_POSTS_SHOWN
from voices.tagging.decisions import CandidateTopic, ClusterBrief, TypicalPost

# A thread is grouped as one text: its post and its best-scored replies (atlas OPEN-29).
TOP_COMMENTS_IN_THREAD_TEXT = 5
THREAD_TEXT_CHARACTERS = 3000


class DocumentEmbedder(Protocol):
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...


class SampleStore:
    def __init__(self, sample: SampleData, embedder: DocumentEmbedder):
        self.sample = sample
        self._posts = _posts_by_id(sample)
        self._post_vectors = _embedded(embedder, {i: p["text"] for i, p in self._posts.items()})
        threads = {i: thread_text(t) for i, t in sample.threads.items()}
        self._thread_vectors = _embedded(embedder, threads)
        topics = {t.topic_id: f"{t.label}: {t.description}" for t in sample.topics}
        self._topic_vectors = _embedded(embedder, topics)

    def case_day(self, case: Case) -> date:
        return max(self.sample.threads[i].day for i in case.thread_ids)

    def topic_label(self, topic_id: int | None) -> str:
        labels = {topic.topic_id: topic.label for topic in self.sample.topics}
        return labels.get(topic_id, f"topic {topic_id}, which does not exist")

    def brief(self, case: Case) -> ClusterBrief:
        """The case as the tagging agent is shown it: shaped like a production brief."""
        centroid = _unit(np.mean([self._thread_vectors[i] for i in case.thread_ids], axis=0))
        return ClusterBrief(
            name=case.name,
            day=self.case_day(case).isoformat(),
            centroid=centroid.tolist(),
            typical_posts=self._typical_posts(case.thread_ids, centroid),
            candidates=self._nearest_topics(centroid, CANDIDATE_TOPICS_SHOWN),
            member_ids=list(case.thread_ids),
        )

    def search_posts(
        self, embedding: Sequence[float], first_day: date, last_day: date, limit: int
    ) -> list[dict]:
        """Every sample post is in the window, so the days are not used."""
        ranked = _closest(self._post_vectors, embedding, limit)
        return [self._hit(post_id, closeness) for post_id, closeness in ranked]

    def lookup_post(self, post_id: str) -> dict:
        if post_id not in self._posts:
            raise PostNotFound(post_id)
        return self._posts[post_id]

    def search_topics(self, embedding: Sequence[float], limit: int) -> list[dict]:
        return [vars(topic) for topic in self._nearest_topics(embedding, limit)]

    def record_retrievals(self, post_ids: Sequence[str], run: str, agent: str, tool: str) -> None:
        """The bake-off keeps no retrieval statistics."""

    def _hit(self, post_id: str, closeness: float) -> dict:
        post = self._posts[post_id]
        excerpt = post["text"][:EXCERPT_CHARACTERS]
        return {**_without(post, "text", "replies_to"), "excerpt": excerpt, "closeness": closeness}

    def _typical_posts(self, thread_ids: list[str], centroid: np.ndarray) -> list[TypicalPost]:
        members = {i: self._thread_vectors[i] for i in thread_ids}
        ranked = _closest(members, centroid, TYPICAL_POSTS_SHOWN)
        threads = [self.sample.threads[i] for i, _ in ranked]
        return [
            TypicalPost(t.source_id, t.author, t.body[:TYPICAL_POST_CHARACTERS]) for t in threads
        ]

    def _nearest_topics(self, embedding: Sequence[float], limit: int) -> list[CandidateTopic]:
        topics = {t.topic_id: t for t in self.sample.topics}
        return [
            CandidateTopic(i, topics[i].label, topics[i].description, s, topics[i].posts_last_week)
            for i, s in _closest(self._topic_vectors, embedding, limit)
        ]


def thread_text(thread: SampleThread) -> str:
    best = sorted(thread.comments, key=lambda c: -c.score)[:TOP_COMMENTS_IN_THREAD_TEXT]
    return "\n\n".join([thread.body, *(c.body for c in best)])[:THREAD_TEXT_CHARACTERS]


def _posts_by_id(sample: SampleData) -> dict[str, dict]:
    """Each thread's post and comments, shaped as the store's lookup returns them."""
    posts = {}
    for thread in sample.threads.values():
        posts[thread.source_id] = _post(thread.source_id, thread.author, thread, thread.body, None)
        for c in thread.comments:
            posts[c.source_id] = _post(c.source_id, c.author, thread, c.body, c.replies_to)
    return posts


def _post(post_id: str, author: str, thread: SampleThread, text: str, replies_to: str | None):
    return {
        "post_id": post_id,
        "author": author,
        "date": thread.day,
        "thread": thread.title,
        "text": text,
        "replies_to": replies_to,
    }


def _embedded(embedder: DocumentEmbedder, texts: dict) -> dict:
    keys = list(texts)
    vectors = embedder.embed_documents([texts[k] for k in keys])
    return {k: _unit(np.asarray(v, dtype=float)) for k, v in zip(keys, vectors, strict=True)}


def _closest(vectors: dict, embedding: Sequence[float], limit: int) -> list[tuple]:
    """The keys of the vectors closest in meaning, with their closeness, best first."""
    target = _unit(np.asarray(embedding, dtype=float))
    scored = [(key, round(float(vector @ target), 3)) for key, vector in vectors.items()]
    return sorted(scored, key=lambda pair: -pair[1])[:limit]


def _unit(vector: np.ndarray) -> np.ndarray:
    length = np.linalg.norm(vector)
    return vector / length if length else vector


def _without(post: dict, *fields: str) -> dict:
    return {key: value for key, value in post.items() if key not in fields}
