import math

from tests.stand_ins import topic_info
from voices.comparison.matching import MATCH_SIMILARITY, match_names


class TableEmbedder:
    """Looks each text up in a table of vectors, and counts its calls."""

    def __init__(self, vectors):
        self.vectors, self.calls = vectors, 0

    def embed_for_comparison(self, texts):
        self.calls += 1
        return [self.vectors[text] for text in texts]


def at_similarity(similarity):
    """A unit vector whose cosine similarity is `similarity` with Winterizing and 0 with
    Impellers."""
    return [similarity, 0.0, math.sqrt(1 - similarity**2)]


TOPICS = [topic_info(1, label="Winterizing"), topic_info(2, label="Impellers")]
TOPIC_VECTORS = {"Winterizing: d": [1.0, 0.0, 0.0], "Impellers: d": [0.0, 1.0, 0.0]}


def match(names, vectors, topics=TOPICS):
    return match_names(names, topics, TableEmbedder({**TOPIC_VECTORS, **vectors}))


def test_a_name_matches_the_topic_closest_in_meaning():
    matches = match(
        ["winter prep", "water pump"],
        {"winter prep": [0.9, 0.1, 0.0], "water pump": [0.1, 0.9, 0.0]},
    )

    assert matches == {"winter prep": 1, "water pump": 2}


def test_a_name_at_the_threshold_matches():
    assert match(["winter prep"], {"winter prep": at_similarity(MATCH_SIMILARITY + 1e-9)}) == {
        "winter prep": 1
    }


def test_a_name_just_below_the_threshold_matches_nothing():
    assert match(["winter prep"], {"winter prep": at_similarity(MATCH_SIMILARITY - 0.01)}) == {
        "winter prep": None
    }


def test_two_names_for_one_topic_the_closer_keeps_it():
    vectors = {"winter prep": at_similarity(0.8), "haul-out": at_similarity(0.95)}

    assert match(["winter prep", "haul-out"], vectors) == {"winter prep": None, "haul-out": 1}


def test_a_repeated_name_is_matched_once():
    assert match(["winter prep", "winter prep"], {"winter prep": [1.0, 0.0, 0.0]}) == {
        "winter prep": 1
    }


def test_no_names_match_nothing_and_embed_nothing():
    embedder = TableEmbedder(TOPIC_VECTORS)

    assert match_names([], TOPICS, embedder) == {}
    assert embedder.calls == 0


def test_with_no_topics_every_name_matches_nothing():
    assert match(["winter prep"], {"winter prep": [1.0, 0.0, 0.0]}, topics=[]) == {
        "winter prep": None
    }


def test_a_name_with_an_empty_embedding_matches_nothing():
    assert match(["blank"], {"blank": [0.0, 0.0, 0.0]}) == {"blank": None}
