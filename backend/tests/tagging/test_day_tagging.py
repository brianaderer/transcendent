from datetime import date

from voices.tagging.clustering import Cluster, WindowPost
from voices.tagging.day_tagging import DayTagging
from voices.tagging.decisions import DecidedCluster, Decision

DAY = date(2026, 10, 15)


def cluster(name, pending=True):
    members = [WindowPost(f"{name}-{n}", [1.0, 0.0], None if pending else 7) for n in range(3)]
    return Cluster(members, [1.0, 0.0])


class FakeStore:
    def __init__(self):
        self.applied, self.expired_before, self.rebuilt = None, None, None

    def window_posts(self, first_day, last_day):
        self.window = (first_day, last_day)
        return []

    def typical_posts(self, ids, centroid, limit):
        return []

    def nearest_topics(self, centroid, limit):
        return []

    def texts(self, ids):
        return ["impeller failed", "impeller spare"]

    def apply_decisions(self, day, settled, keywords):
        self.applied = (day, settled, keywords)
        return {"attached": 3}

    def delete_expired_pending(self, before):
        self.expired_before = before
        return 2

    def rebuild_engagement(self, first_day, last_day):
        self.rebuilt = (first_day, last_day)


def decide_noise(day, briefs):
    return [DecidedCluster(b, Decision(action="noise", reason="r"), "p", "m") for b in briefs]


def run(clusters, store, emitted):
    def emit(event_type, **body):
        emitted.append(event_type)

    return DayTagging(store, decide_noise, emit, clusters_of=lambda posts: clusters).tag(DAY)


def test_the_window_is_the_day_and_the_two_before_it():
    store = FakeStore()
    run([], store, [])

    assert store.window == (date(2026, 10, 13), DAY)
    assert store.rebuilt == (date(2026, 10, 13), DAY)


def test_only_clusters_with_posts_still_waiting_for_a_tag_are_decided():
    store = FakeStore()
    run([cluster("new"), cluster("settled", pending=False)], store, [])

    _, settled, _ = store.applied
    assert [d.brief.name for d in settled] == ["cluster-1"]


def test_posts_still_waiting_from_before_the_window_are_deleted_as_noise():
    store = FakeStore()
    counts = run([], store, [])

    assert store.expired_before == date(2026, 10, 13)
    assert counts["expired"] == 2


def test_each_decision_is_announced_live():
    emitted = []
    run([cluster("a"), cluster("b")], FakeStore(), emitted)

    assert emitted.count("decision.made") == 2


def decide_mints(day, briefs):
    return [
        DecidedCluster(b, Decision(action="mint", label="x", reason="r"), "p", "m") for b in briefs
    ]


def test_keywords_are_picked_only_for_new_topics_not_merged_into_another():
    store = FakeStore()
    tagging = DayTagging(
        store,
        decide_mints,
        lambda event_type, **body: None,
        clusters_of=lambda posts: [cluster("a"), cluster("b")],  # same centre: b merges into a
    )

    counts = tagging.tag(DAY)

    _, _, keywords = store.applied
    assert keywords == {"cluster-1": ["impeller", "failed", "spare"]}
    assert counts["clusters"] == 2
