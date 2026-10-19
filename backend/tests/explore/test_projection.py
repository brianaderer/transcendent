import numpy as np

from voices.explore.projection import flatten


def two_clusters(per_cluster=15, dimensions=8):
    generator = np.random.default_rng(1)
    near_a = generator.normal(0, 0.05, (per_cluster, dimensions)) + np.eye(dimensions)[0]
    near_b = generator.normal(0, 0.05, (per_cluster, dimensions)) + np.eye(dimensions)[1]
    return np.vstack([near_a, near_b]).tolist()


def test_nothing_to_flatten_gives_no_points():
    assert flatten([]) == []


def test_a_handful_of_posts_are_laid_out_without_failing():
    for count in range(1, 5):
        assert len(flatten(two_clusters()[:count])) == count


def test_the_same_posts_always_give_the_same_map():
    vectors = two_clusters()

    assert flatten(vectors) == flatten(vectors)


def test_posts_close_in_meaning_land_close_together():
    points = np.array(flatten(two_clusters()))
    centre_a, centre_b = points[:15].mean(axis=0), points[15:].mean(axis=0)
    spread_a = np.linalg.norm(points[:15] - centre_a, axis=1).mean()

    assert np.linalg.norm(centre_a - centre_b) > 3 * spread_a


def test_the_map_fits_in_a_square_from_minus_one_to_one():
    points = np.array(flatten(two_clusters()))

    assert np.abs(points).max() == 1.0
