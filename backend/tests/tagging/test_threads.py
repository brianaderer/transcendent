from voices.tagging.threads import THREAD_TEXT_CHARACTERS, Reply, thread_text


def test_a_thread_reads_as_its_post_then_its_best_scored_replies():
    replies = [Reply(f"reply{n}", score=n) for n in range(6)]

    text = thread_text("The post", replies)

    assert text.startswith("The post\n\nreply5\n\nreply4")
    assert "reply1" in text and "reply0" not in text


def test_a_thread_with_no_replies_is_just_its_post():
    assert thread_text("The post", []) == "The post"


def test_a_thread_is_cut_at_the_character_limit():
    long_reply = Reply("x" * THREAD_TEXT_CHARACTERS, score=1)

    assert len(thread_text("The post", [long_reply])) == THREAD_TEXT_CHARACTERS
