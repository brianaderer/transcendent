from voices.tagging.keywords import distinctive_keywords

CLUSTER = [
    "My impeller failed again on the Yanmar",
    "Impeller replacement on a Yanmar 3GM, any tips?",
    "Spare impeller kit recommendations",
]
WINDOW = CLUSTER + ["Best anchor for mud", "Reefing early in a gale", "Anchor dragged overnight"]


def test_words_common_in_the_cluster_and_rare_elsewhere_come_first():
    assert distinctive_keywords(CLUSTER, WINDOW, limit=2) == ["impeller", "yanmar"]


def test_short_and_common_words_are_never_keywords():
    keywords = distinctive_keywords(CLUSTER, WINDOW, limit=10)

    assert not {"the", "on", "a", "any", "my", "again"} & set(keywords)
