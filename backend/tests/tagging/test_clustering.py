import random

from voices.tagging.clustering import WindowPost, find_clusters


def post(source_id, direction, topic_id=None, noise=0.05, seed=0):
    rng = random.Random(f"{source_id}-{seed}")
    vector = [d + rng.uniform(-noise, noise) for d in direction]
    return WindowPost(source_id, vector, topic_id)


ANCHORS = [1.0, 0.0, 0.0, 0.0]
SAILS = [0.0, 1.0, 0.0, 0.0]


def test_posts_that_mean_the_same_thing_form_one_cluster():
    posts = [post(f"a{n}", ANCHORS) for n in range(6)] + [post(f"s{n}", SAILS) for n in range(6)]

    clusters = find_clusters(posts, min_cluster_size=3)

    groups = sorted(sorted(p.source_id[0] for p in c.members) for c in clusters)
    assert groups == [["a"] * 6, ["s"] * 6]


def test_a_post_unlike_any_other_belongs_to_no_cluster():
    posts = [post(f"a{n}", ANCHORS) for n in range(6)] + [post("odd", [0.0, 0.0, 0.0, 1.0])]

    clusters = find_clusters(posts, min_cluster_size=3)

    assert "odd" not in {p.source_id for c in clusters for p in c.members}


def test_too_few_posts_make_no_clusters():
    assert find_clusters([post("a1", ANCHORS), post("a2", ANCHORS)], min_cluster_size=3) == []


def sails(count=4):
    """A second conversation: HDBSCAN finds groups only where there is more than one."""
    return [post(f"s{n}", SAILS) for n in range(count)]


def cluster_of(clusters, source_id):
    return next(c for c in clusters if source_id in {p.source_id for p in c.members})


def test_a_clusters_centre_is_the_average_direction_of_its_members():
    posts = [post(f"a{n}", ANCHORS, noise=0) for n in range(4)] + sails()

    cluster = cluster_of(find_clusters(posts, min_cluster_size=3), "a0")

    assert [round(x, 6) for x in cluster.centroid] == [1.0, 0.0, 0.0, 0.0]


def test_a_cluster_says_which_of_its_members_still_need_a_tag():
    posts = [
        post("a1", ANCHORS, topic_id=7),
        post("a2", ANCHORS),
        post("a3", ANCHORS),
        post("a4", ANCHORS, topic_id=7),
    ] + sails()

    cluster = cluster_of(find_clusters(posts, min_cluster_size=3), "a1")

    assert sorted(p.source_id for p in cluster.pending) == ["a2", "a3"]
    assert cluster.has_pending
