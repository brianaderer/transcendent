from voices.db.stand_in_names import StandInNames


def test_authors_are_numbered_in_the_order_they_first_appear():
    names = StandInNames()

    given = [names.name_for(author) for author in ["salty", "skipper", "salty"]]

    assert given == ["sailor-0001", "sailor-0002", "sailor-0001"]


def test_a_mentioned_user_gets_the_same_stand_in_as_their_posts():
    names = StandInNames()
    names.name_for("Lazy-Target-7148")

    text = names.in_text("Mod hat on u/Lazy-Target-7148 - thanks /u/lazy-target-7148.")

    assert text == "Mod hat on u/sailor-0001 - thanks /u/sailor-0001."


def test_a_user_first_seen_in_a_mention_is_given_the_next_number():
    names = StandInNames()

    assert names.in_text("ask u/mike8111") == "ask u/sailor-0001"
    assert names.name_for("mike8111") == "sailor-0001"


def test_text_that_only_looks_like_a_mention_is_left_alone():
    names = StandInNames()

    text = names.in_text("menu/galley, r/sailing, and a 12u/v rating")

    assert text == "menu/galley, r/sailing, and a 12u/v rating"
