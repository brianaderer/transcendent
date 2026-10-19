import random

from voices.tagging.grouping import EncodedThread, group_by_meaning


def thread(source_id, direction, noise=0.05):
    rng = random.Random(source_id)
    return EncodedThread(source_id, [d + rng.uniform(-noise, noise) for d in direction])


ANCHORS = [1.0, 0.0, 0.0, 0.0]
SAILS = [0.0, 1.0, 0.0, 0.0]


def members(groups):
    return sorted(sorted(t.source_id for t in group.members) for group in groups)


def test_threads_that_mean_the_same_thing_form_one_group():
    threads = [thread(f"a{n}", ANCHORS) for n in range(3)] + [
        thread(f"s{n}", SAILS) for n in range(3)
    ]

    assert members(group_by_meaning(threads)) == [["a0", "a1", "a2"], ["s0", "s1", "s2"]]


def test_a_thread_unlike_any_other_is_a_group_of_its_own():
    threads = [thread(f"a{n}", ANCHORS) for n in range(3)] + [thread("odd", [0.0, 0.0, 0.0, 1.0])]

    assert ["odd"] in members(group_by_meaning(threads))


def test_one_thread_is_one_group_and_none_is_none():
    assert members(group_by_meaning([thread("only", ANCHORS)])) == [["only"]]
    assert group_by_meaning([]) == []


def test_a_groups_centre_points_the_way_its_threads_do():
    [group] = group_by_meaning([thread(f"a{n}", ANCHORS) for n in range(3)])

    assert group.centroid[0] > 0.99
