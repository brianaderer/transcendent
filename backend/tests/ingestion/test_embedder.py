from voices.ingestion.embedder import BATCH_TEXT_BUDGET, MAX_BATCH, NomicEmbedder


class EchoModel:
    """Stand-in for the fastembed model: records what it was given."""

    def __init__(self):
        self.seen = []
        self.batches = []

    def embed(self, texts, batch_size):
        assert batch_size == len(texts)
        self.seen += texts
        self.batches.append(list(texts))
        return [[float(len(text)), 2.0] for text in texts]


def test_stored_posts_are_embedded_as_documents_to_be_searched():
    model = EchoModel()

    vectors = NomicEmbedder(model).embed_documents(["Rocna, every time."])

    assert model.seen == ["search_document: Rocna, every time."]
    assert vectors == [[float(len("search_document: Rocna, every time.")), 2.0]]


def test_search_terms_are_embedded_as_queries():
    model = EchoModel()

    NomicEmbedder(model).embed_query("heavy weather")

    assert model.seen == ["search_query: heavy weather"]


def test_replies_checked_for_agreement_are_embedded_for_classification():
    model = EchoModel()

    NomicEmbedder(model).embed_for_comparison(["+1"])

    assert model.seen == ["classification: +1"]


def test_texts_are_embedded_shortest_first_and_returned_in_order():
    model = EchoModel()
    texts = ["a much longer reply about reefing", "+1", "medium length reply"]

    vectors = NomicEmbedder(model).embed_documents(texts)

    assert model.seen == sorted(model.seen, key=len)
    assert [v[0] for v in vectors] == [float(len("search_document: " + t)) for t in texts]


def test_a_batch_never_holds_more_text_than_the_budget_unless_one_text_is_longer():
    model = EchoModel()
    long_post = "x" * (BATCH_TEXT_BUDGET + 10)

    NomicEmbedder(model).embed_documents(["short"] * 3 + [long_post])

    assert all(sum(map(len, b)) <= BATCH_TEXT_BUDGET for b in model.batches if len(b) > 1)
    assert [len(b) for b in model.batches] == [3, 1]


def test_short_texts_go_at_most_the_batch_limit_at_a_time():
    model = EchoModel()

    NomicEmbedder(model).embed_documents(["+1"] * (MAX_BATCH + 1))

    assert [len(b) for b in model.batches] == [MAX_BATCH, 1]
