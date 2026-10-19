import threading

from voices.tagging.decisions import ClusterBrief, DecidedCluster, Decision
from voices.tagging.graph import decide_all


class EchoDecider:
    def decide(self, brief):
        decision = Decision(action="noise", reason=f"decided {brief.name}")
        return DecidedCluster(brief, decision, prompt="p", model="m")


def test_every_cluster_gets_its_own_decision():
    briefs = [ClusterBrief(f"c{n}", "2026-10-15", [1.0], [], [], []) for n in range(4)]

    decided = decide_all(EchoDecider(), briefs, lambda _: None)

    assert sorted(d.decision.reason for d in decided) == [f"decided c{n}" for n in range(4)]


def test_no_clusters_means_no_decisions():
    assert decide_all(EchoDecider(), [], lambda _: None) == []


ANNOUNCED_IN_TIME_SECONDS = 5


class SecondWaitsForTheFirstsAnnouncement:
    """Decides c1 at once; decides c2 only after c1 has been announced, which can only happen
    if each decision is announced as it is made rather than all of them at the end."""

    def __init__(self):
        self.first_announced = threading.Event()

    def decide(self, brief):
        if brief.name == "c2" and not self.first_announced.wait(ANNOUNCED_IN_TIME_SECONDS):
            raise AssertionError("c1 was not announced while c2 was being decided")
        return EchoDecider().decide(brief)


def test_each_decision_is_announced_as_it_is_made():
    briefs = [ClusterBrief(name, "2026-10-15", [1.0], [], [], []) for name in ("c1", "c2")]
    decider, announced = SecondWaitsForTheFirstsAnnouncement(), []

    def announce(item):
        announced.append(item.brief.name)
        if item.brief.name == "c1":
            decider.first_announced.set()

    decide_all(decider, briefs, announce)

    assert announced == ["c1", "c2"]
