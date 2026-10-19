from datetime import date

import pytest

from voices.bakeoff.sample import Case, Comment, SampleData, SampleThread, SampleTopic


class WordEmbedder:
    """Stand-in embedder: one dimension per known word, so texts sharing words are close."""

    WORDS = ["stolen", "boat", "reef", "sail", "lesson", "learn", "galley", "dolphin"]

    def embed_documents(self, texts):
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text):
        # A small floor on every dimension keeps a text with no known words from being all zeros.
        lowered = text.lower()
        return [float(lowered.count(word)) + 0.01 for word in self.WORDS]


REPLY = Comment("c1", "u", "Stolen again?", "t1", 3)


def thread(source_id, body, comments=()):
    return SampleThread(source_id, body[:20], "op", date(2026, 8, 24), body, list(comments))


@pytest.fixture
def sample():
    return SampleData(
        topics=[
            SampleTopic(1, "Stolen boats", "Boats stolen from marinas.", 6),
            SampleTopic(2, "Learning to sail", "Lessons and learning to sail.", 9),
        ],
        threads={
            "t1": thread("t1", "Stolen boat in NYC", [REPLY]),
            "t2": thread("t2", "Another stolen boat"),
            "t3": thread("t3", "Where can I learn, any lesson nearby?"),
        },
        cases=[
            Case("theft", ["t1", "t2"], "attach", 1),
            Case("lessons", ["t3"], "attach", 2),
        ],
    )


@pytest.fixture
def embedder():
    return WordEmbedder()
