from datetime import date

from voices.tagging.day_tagging import DayTagging
from voices.tagging.decisions import DecidedCluster, Decision
from voices.tagging.grouping import EncodedThread, Group, group_by_meaning
from voices.tagging.threads import DueThread, Reply

DAY = date(2026, 10, 15)


def due(source_id, post="Impeller failed again", replies=()):
    return DueThread(source_id, post, list(replies))


class FakeStore:
    def __init__(self, threads=()):
        self.threads = list(threads)
        self.saved, self.applied, self.rebuilt = None, None, None
        self.steps = []

    def threads_due(self, day):
        self.asked_for = day
        return self.threads

    def save_thread_embeddings(self, embeddings):
        self.saved = embeddings

    def typical_threads(self, ids, centroid, limit):
        return []

    def nearest_topics(self, centroid, limit):
        return []

    def apply_decisions(self, day, settled, keywords):
        self.applied = (day, settled, keywords)
        self.steps.append("apply")
        return {"attached": 3}

    def expire_noise(self, day):
        self.expired_on = day
        self.steps.append("expire")
        return 2

    def rebuild_engagement(self, first_day, last_day):
        self.rebuilt = (first_day, last_day)
        self.steps.append("rebuild")


class FakeEmbedder:
    def __init__(self):
        self.texts = []

    def embed_documents(self, texts):
        self.texts.extend(texts)
        return [[1.0, 0.0] for _ in texts]


def one_group_each(threads):
    return [Group([thread], [1.0, 0.0]) for thread in threads]


def decide(action):
    def decide_all(day, briefs, announce):
        decision = Decision(action=action, label="x", reason="r")
        decided = [DecidedCluster(b, decision, "p", "m") for b in briefs]
        for item in decided:
            announce(item)
        return decided

    return decide_all


def run(store, embedder=None, action="noise", emitted=None, groups_of=one_group_each):
    def emit(event_type, **body):
        (emitted if emitted is not None else []).append(event_type)

    tagging = DayTagging(store, embedder or FakeEmbedder(), decide(action), emit, groups_of)
    return tagging.tag(DAY)


def test_each_thread_due_is_encoded_as_its_post_and_replies_and_the_encoding_is_kept():
    store, embedder = FakeStore([due("t1", replies=[Reply("Carry a spare.", 4)])]), FakeEmbedder()

    run(store, embedder)

    assert embedder.texts == ["Impeller failed again\n\nCarry a spare."]
    assert store.saved == {"t1": [1.0, 0.0]}


def test_every_group_is_decided_even_a_thread_on_its_own():
    store = FakeStore([due("t1"), due("t2")])

    counts = run(store)

    _, settled, _ = store.applied
    assert [d.brief.member_ids for d in settled] == [["t1"], ["t2"]]
    assert counts["groups"] == 2 and counts["threads"] == 2


def test_engagement_is_rebuilt_for_the_day_and_the_two_before_it():
    store = FakeStore()

    run(store)

    assert store.asked_for == DAY
    assert store.rebuilt == (date(2026, 10, 13), DAY)


def test_threads_still_without_a_topic_are_expired_after_the_decisions_before_engagement():
    store = FakeStore([due("t1")])

    counts = run(store)

    assert store.steps == ["apply", "expire", "rebuild"]
    assert store.expired_on == DAY
    assert counts["noise_expired"] == 2


def test_each_decision_is_announced_live():
    emitted = []

    run(FakeStore([due("t1"), due("t2")]), emitted=emitted)

    assert emitted.count("decision.made") == 2


def test_keywords_are_picked_only_for_new_topics_not_merged_into_another():
    threads = [due("t1", "impeller failed"), due("t2", "impeller spare")]
    store = FakeStore(threads)

    run(store, action="mint")  # both groups have the same centre, so the second merges

    _, _, keywords = store.applied
    assert keywords == {"group-1": ["failed", "impeller"]}


def test_a_day_with_no_threads_due_decides_nothing():
    store = FakeStore()

    counts = run(store, groups_of=group_by_meaning)

    assert counts["groups"] == 0 and store.applied[1] == []


def test_groups_are_made_from_the_encoded_threads():
    seen = []

    def remember(threads):
        seen.extend(threads)
        return []

    run(FakeStore([due("t1")]), groups_of=remember)

    assert seen == [EncodedThread("t1", [1.0, 0.0])]


def mint_all_as(label):
    """Every group mints a topic with the same label, so the later ones merge into the first."""

    def decide_all(day, briefs, announce):
        decision = Decision(action="mint", label=label, description="d", reason="r")
        decided = [DecidedCluster(b, decision, "p", "m") for b in briefs]
        for item in decided:
            announce(item)
        return decided

    return decide_all


def test_a_second_mint_of_the_same_topic_is_announced_as_merged_into_the_first():
    events = []
    emit = lambda kind, **body: events.append((kind, body))  # noqa: E731
    tagging = DayTagging(
        FakeStore([due("t1"), due("t2")]),
        FakeEmbedder(),
        mint_all_as("Impellers"),
        emit,
        one_group_each,
    )

    tagging.tag(DAY)

    assert [body for kind, body in events if kind == "mint.merged"] == [
        {"group": "group-2", "into": "group-1"}
    ]


def test_a_day_without_merges_announces_none():
    emitted = []

    run(FakeStore([due("t1"), due("t2")]), emitted=emitted)

    assert "mint.merged" not in emitted
