from voices.reddit_links import post_link


def test_a_post_links_to_its_thread():
    assert post_link("abc", "abc", "post") == "https://www.reddit.com/r/sailing/comments/abc/"


def test_a_comment_links_to_itself_inside_its_thread():
    assert (
        post_link("c9", "abc", "comment")
        == "https://www.reddit.com/r/sailing/comments/abc/comment/c9/"
    )
