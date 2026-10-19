from datetime import date

import pytest
from langchain_core.messages import AIMessage

from voices.bakeoff.sample import Case, Comment, SampleData, SampleThread, SampleTopic


class WordEmbedder:
    """Stand-in embedder: one dimension per known word, so texts sharing words are close."""

    WORDS = ["stolen", "boat", "reef", "sail", "lesson", "learn", "galley", "dolphin"]

    def embed_documents(self, texts):
        return [self.embed_query(text) for text in texts]

    def embed_query(self, text):
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


USAGE = {"input_tokens": 1000, "output_tokens": 100, "total_tokens": 1100}


class AlwaysAttachesToTheft:
    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        arguments = {"action": "attach", "topic_id": 1, "reason": "Theft."}
        call = {"name": "Decision", "args": arguments, "id": "1"}
        return AIMessage(content="", tool_calls=[call], usage_metadata=USAGE)


class NeverDecides:
    def bind_tools(self, tools):
        return self

    def invoke(self, messages):
        return AIMessage(content="hmm", usage_metadata=USAGE)
