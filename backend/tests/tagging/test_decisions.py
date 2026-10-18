from voices.tagging.decisions import ClusterBrief, DecidedCluster, Decision, settle_mints


def brief(name, centroid):
    return ClusterBrief(name, "2026-10-15", centroid, [], [], [])


def decided(name, action, centroid, topic_id=None):
    decision = Decision(
        action=action, topic_id=topic_id, label=f"{name} label", description="d", reason="r"
    )
    return DecidedCluster(brief(name, centroid), decision, prompt="p", model="m")


def test_a_second_new_topic_for_the_same_conversation_joins_the_first():
    first = decided("c1", "mint", [1.0, 0.0])
    twin = decided("c2", "mint", [0.99, 0.05])

    settled = settle_mints([first, twin])

    assert settled[0].merged_into is None
    assert settled[1].merged_into == "c1"


def test_new_topics_about_different_things_both_stand():
    settled = settle_mints([decided("c1", "mint", [1.0, 0.0]), decided("c2", "mint", [0.0, 1.0])])

    assert [d.merged_into for d in settled] == [None, None]


def test_attach_and_noise_decisions_pass_through_unchanged():
    decisions = [
        decided("c1", "attach", [1.0, 0.0], topic_id=3),
        decided("c2", "noise", [1.0, 0.0]),
    ]

    assert settle_mints(decisions) == decisions
