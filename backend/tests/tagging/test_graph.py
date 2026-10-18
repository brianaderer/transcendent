from voices.tagging.decisions import ClusterBrief, DecidedCluster, Decision
from voices.tagging.graph import decide_all


class EchoDecider:
    def decide(self, brief):
        decision = Decision(action="noise", reason=f"decided {brief.name}")
        return DecidedCluster(brief, decision, prompt="p", model="m")


def test_every_cluster_gets_its_own_decision():
    briefs = [ClusterBrief(f"c{n}", "2026-10-15", [1.0], [], [], []) for n in range(4)]

    decided = decide_all(EchoDecider(), briefs)

    assert sorted(d.decision.reason for d in decided) == [f"decided c{n}" for n in range(4)]


def test_no_clusters_means_no_decisions():
    assert decide_all(EchoDecider(), []) == []
