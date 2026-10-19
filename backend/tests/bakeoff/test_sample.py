from voices.bakeoff.sample import ACTIONS, load_sample_data


def test_the_committed_sample_loads_with_cases_of_every_kind():
    sample = load_sample_data()

    assert {case.expected for case in sample.cases} == set(ACTIONS)


def test_every_case_names_threads_that_are_in_the_sample():
    sample = load_sample_data()

    assert all(t in sample.threads for case in sample.cases for t in case.thread_ids)


def test_every_attach_case_names_a_topic_that_exists_and_no_other_case_does():
    sample = load_sample_data()
    topic_ids = {topic.topic_id for topic in sample.topics}

    for case in sample.cases:
        assert (case.topic_id in topic_ids) == (case.expected == "attach"), case.name


def test_no_sample_thread_is_a_removed_post():
    sample = load_sample_data()

    assert not [t for t in sample.threads.values() if t.body.endswith("[removed]")]
