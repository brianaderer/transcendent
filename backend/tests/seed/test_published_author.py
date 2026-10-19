from voices.db.seed_export import published_author


def test_author_names_are_kept_as_they_are_until_usernames_are_decided():
    """Atlas OPEN-37 is open; this is the one place a decision would change."""
    assert published_author("salty_sailor") == "salty_sailor"
