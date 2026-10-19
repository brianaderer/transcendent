"""The sample data held in memory behind the tagging tools' store interface, searched by
meaning with the real embedding model, so the agent's tools behave as they do on Postgres."""

from collections.abc import Sequence
from datetime import date
from typing import Protocol

import numpy as np

from voices.bakeoff.sample import Case, Comment, SampleData, SampleThread
from voices.db.tagging_store import EXCERPT_CHARACTERS, TYPICAL_POST_CHARACTERS, PostNotFound
from voices.tagging.day_tagging import CANDIDATE_TOPICS_SHOWN, TYPICAL_POSTS_SHOWN
from voices.tagging.decisions import CandidateTopic, ClusterBrief, TypicalPost
from voices.tagging.threads import thread_text
from voices.tagging.tools import TaggingTools


class Embedder(Protocol):
    def embed_documents(self, texts: Sequence[str]) -> list[list[float]]: ...
    def embed_query(self, text: str) -> list[float]: ...


class SampleStore:
    def __init__(self, sample: SampleData, embedder: Embedder):
        """Embeds every post, comment, thread and topic once, here: with the real model that
        takes some seconds."""
        self.sample = sample
        self._embedder = embedder
        self._posts = _posts_by_id(sample)
        self._post_vectors = self._embedded({i: post["text"] for i, post in self._posts.items()})
        self._thread_vectors = self._embedded(
            {i: thread_text(thread.body, thread.comments) for i, thread in sample.threads.items()}
        )
        self._topic_vectors = self._embedded(
            {topic.topic_id: f"{topic.label}: {topic.description}" for topic in sample.topics}
        )

    def case_day(self, case: Case) -> date:
        return max(self.sample.threads[i].day for i in case.thread_ids)

    def tools_for(self, case: Case) -> TaggingTools:
        """The production tagging tools, reading this store, as on the case's day."""
        return TaggingTools(self, self._embedder, self.case_day(case))

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

    def _embedded(self, texts: dict) -> dict:
        keys = list(texts)
        vectors = self._embedder.embed_documents([texts[key] for key in keys])
        return {
            key: _unit(np.asarray(vector, dtype=float))
            for key, vector in zip(keys, vectors, strict=True)
        }

    def _hit(self, post_id: str, closeness: float) -> dict:
        post = self._posts[post_id]
        excerpt = post["text"][:EXCERPT_CHARACTERS]
        return {**_without(post, "text", "replies_to"), "excerpt": excerpt, "closeness": closeness}

    def _typical_posts(self, thread_ids: list[str], centroid: np.ndarray) -> list[TypicalPost]:
        members = {i: self._thread_vectors[i] for i in thread_ids}
        ranked = _closest(members, centroid, TYPICAL_POSTS_SHOWN)
        threads = [self.sample.threads[thread_id] for thread_id, _ in ranked]
        return [
            TypicalPost(thread.source_id, thread.author, thread.body[:TYPICAL_POST_CHARACTERS])
            for thread in threads
        ]

    def _nearest_topics(self, embedding: Sequence[float], limit: int) -> list[CandidateTopic]:
        topics = {topic.topic_id: topic for topic in self.sample.topics}
        return [
            CandidateTopic(
                topic_id,
                topics[topic_id].label,
                topics[topic_id].description,
                similarity,
                topics[topic_id].posts_last_week,
            )
            for topic_id, similarity in _closest(self._topic_vectors, embedding, limit)
        ]


def _posts_by_id(sample: SampleData) -> dict[str, dict]:
    """Each thread's post and comments, shaped as the store's lookup returns them."""
    posts = {}
    for thread in sample.threads.values():
        posts[thread.source_id] = _thread_post(thread)
        posts.update(
            {comment.source_id: _comment_post(thread, comment) for comment in thread.comments}
        )
    return posts


def _thread_post(thread: SampleThread) -> dict:
    return {
        "post_id": thread.source_id,
        "author": thread.author,
        "date": thread.day,
        "thread": thread.title,
        "text": thread.body,
        "replies_to": None,
    }


def _comment_post(thread: SampleThread, comment: Comment) -> dict:
    return {
        "post_id": comment.source_id,
        "author": comment.author,
        "date": thread.day,
        "thread": thread.title,
        "text": comment.body,
        "replies_to": comment.replies_to,
    }


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
