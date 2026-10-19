import json
from datetime import date

from voices.explore.day_range import DayRange
from voices.report.reading_tools import (
    NOTHING_LEFT_TO_READ,
    READ_BATCH,
    READ_BUDGET,
    ReadingTools,
)

WINDOW = DayRange(date(2026, 10, 12), date(2026, 10, 18))


class FakeReader:
    """`in_store` posts written in the window (thirty unless told otherwise), handed out in
    order, never one already given."""

    def __init__(self, in_store=30):
        self.posts = [{"post_id": f"p{n}", "text": f"Post {n}"} for n in range(in_store)]
        self.asked = []

    def sample_posts(self, days, limit, seed, exclude_ids):
        self.asked.append((days, limit, seed, list(exclude_ids)))
        return [p for p in self.posts if p["post_id"] not in exclude_ids][:limit]


def reading(reader):
    return ReadingTools(reader, WINDOW, "report-run-1")


def test_reading_hands_back_a_batch_of_whole_posts_from_the_window_in_the_runs_shuffle():
    reader = FakeReader()

    result = reading(reader).run("read_posts", {})

    assert reader.asked == [(WINDOW, READ_BATCH, "report-run-1", [])]
    assert result.post_ids == [f"p{n}" for n in range(READ_BATCH)]
    assert json.loads(result.text)[0]["text"] == "Post 0"


def test_a_second_read_skips_the_posts_already_given():
    reader = FakeReader()
    tools = reading(reader)

    tools.run("read_posts", {})
    second = tools.run("read_posts", {})

    assert reader.asked[1][3] == [f"p{n}" for n in range(READ_BATCH)]
    assert second.post_ids[0] == f"p{READ_BATCH}"


def test_once_the_budget_is_spent_the_agent_is_told_to_answer_and_the_store_is_not_asked():
    reader = FakeReader()
    tools = reading(reader)
    for _ in range(READ_BUDGET // READ_BATCH):
        tools.run("read_posts", {})

    spent = tools.run("read_posts", {})

    assert spent.text == NOTHING_LEFT_TO_READ and spent.post_ids == []
    assert len(reader.asked) == READ_BUDGET // READ_BATCH


FIRST_READ_FOUND = 3


class ShortFirstReader(FakeReader):
    """Has only FIRST_READ_FOUND posts for the first read, as a quiet day might."""

    def sample_posts(self, days, limit, seed, exclude_ids):
        posts = super().sample_posts(days, limit, seed, exclude_ids)
        return posts[:FIRST_READ_FOUND] if len(self.asked) == 1 else posts


def test_the_last_read_asks_only_for_what_is_left_of_the_budget():
    reader = ShortFirstReader()
    tools = reading(reader)

    for _ in range(3):
        tools.run("read_posts", {})

    expected = READ_BUDGET - FIRST_READ_FOUND - READ_BATCH
    assert [asked[1] for asked in reader.asked] == [READ_BATCH, READ_BATCH, expected]


def test_a_day_inside_the_window_narrows_the_read_to_that_day():
    reader = FakeReader()

    reading(reader).run("read_posts", {"day": "2026-10-14"})

    assert reader.asked[0][0] == DayRange(date(2026, 10, 14), date(2026, 10, 14))


def test_a_day_outside_the_window_or_not_a_date_is_explained_not_read():
    reader = FakeReader()
    tools = reading(reader)

    outside = tools.run("read_posts", {"day": "2026-10-25"})
    garbled = tools.run("read_posts", {"day": "next Tuesday"})

    assert "2026-10-12 to 2026-10-18" in outside.text
    assert "YYYY-MM-DD" in garbled.text
    assert reader.asked == []


def test_no_posts_left_in_the_period_is_said_plainly():
    result = reading(FakeReader(in_store=0)).run("read_posts", {})

    assert "No more posts" in result.text and result.post_ids == []


def test_only_read_posts_is_offered_and_retrieval_tools_are_refused():
    reader = FakeReader()
    tools = reading(reader)

    refused = tools.run("search", {"term": "impeller"})

    assert [s["function"]["name"] for s in tools.schemas] == ["read_posts"]
    assert "no tool named search" in refused.text and reader.asked == []
