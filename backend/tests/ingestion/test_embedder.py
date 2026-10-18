from voices.ingestion.embedder import EMBED_BATCH_SIZE, NomicEmbedder


class EchoModel:
    """Stand-in for the fastembed model: records what it was given."""

    def __init__(self):
        self.seen = []

    def embed(self, texts, batch_size):
        self.seen += texts
        self.batch_size = batch_size
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


def test_texts_are_embedded_in_small_batches_of_similar_length_and_returned_in_order():
    model = EchoModel()
    texts = ["a much longer reply about reefing", "+1", "medium length reply"]

    vectors = NomicEmbedder(model).embed_documents(texts)

    assert model.seen == sorted(model.seen, key=len)
    assert [v[0] for v in vectors] == [float(len("search_document: " + t)) for t in texts]
    assert model.batch_size == EMBED_BATCH_SIZE
