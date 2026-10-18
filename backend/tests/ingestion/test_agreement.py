from voices.ingestion.agreement import AgreementDetector


class MeaningByWords:
    """Stand-in embedder: agreement-like words point one way, everything else another."""

    AGREEING = {"+1", "this", "same", "agree", "agreed", "exactly", "yes", "true", "100%"}

    def embed_for_comparison(self, texts):
        return [self._vector(text) for text in texts]

    def _vector(self, text):
        words = set(text.lower().replace(".", "").replace("!", "").split())
        return [1.0, 0.0] if words & self.AGREEING else [0.0, 1.0]


detector = AgreementDetector(MeaningByWords())


def test_a_short_reply_that_means_agreement_is_an_upvote():
    assert detector.agreeing(["+1", "Same here!", "Agreed."]) == [True, True, True]


def test_a_short_reply_that_says_something_else_is_not():
    assert detector.agreeing(["Rocna anchor."]) == [False]


def test_a_question_is_never_an_upvote():
    assert detector.agreeing(["this?"]) == [False]


def test_a_link_is_never_an_upvote():
    assert detector.agreeing(["this https://example.com"]) == [False]


def test_a_long_reply_is_never_an_upvote_however_agreeable():
    long_reply = (
        "yes this is exactly what I found when I sailed the boat down the coast last spring"
    )

    assert detector.agreeing([long_reply]) == [False]
