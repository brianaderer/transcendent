import json
from datetime import UTC, datetime

import httpx
import pytest

from voices.ingestion.arctic_shift import ArchiveUnavailable, ArcticShift

DAY_START = datetime(2026, 10, 15, tzinfo=UTC)
DAY_END = datetime(2026, 10, 16, tzinfo=UTC)


def comment(n, created):
    return {
        "id": f"c{n}",
        "author": "a",
        "created_utc": created,
        "body": "hi",
        "parent_id": "t3_p",
        "link_id": "t3_p",
        "score": 1,
    }


def archive(handler):
    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="https://archive")
    return ArcticShift(client, pause_seconds=0, attempts=3)


def answer(data=None, error=None, status=200):
    return httpx.Response(status, content=json.dumps({"data": data, "error": error}))


def test_a_busy_day_is_read_page_by_page_until_a_short_page():
    first = [comment(n, 1792022400 + n) for n in range(100)]
    second = [comment(100 + n, 1792022500 + n) for n in range(5)]
    seen_after = []

    def handler(request):
        seen_after.append(request.url.params["after"])
        return answer(first if len(seen_after) == 1 else second)

    comments = archive(handler).comments_created_between(DAY_START, DAY_END)

    assert len(comments) == 105
    assert seen_after == [str(int(DAY_START.timestamp())), str(first[-1]["created_utc"])]


def test_an_item_repeated_across_a_page_boundary_is_kept_once():
    first = [comment(n, 1792022401 + n) for n in range(100)]
    second = [first[-1], comment(100, 1792022600)]

    def handler(request):
        return answer(first if request.url.params["after"] == "1792022400" else second)

    assert len(archive(handler).comments_created_between(DAY_START, DAY_END)) == 101


def test_a_full_page_from_a_single_second_cannot_trap_the_reader():
    same_second = [comment(n, 1792022401) for n in range(100)]
    asked_after = []

    def handler(request):
        asked_after.append(request.url.params["after"])
        return answer(same_second if len(asked_after) <= 2 else [])

    archive(handler).comments_created_between(DAY_START, DAY_END)

    assert asked_after == ["1792022400", "1792022401", "1792022402"]


def test_a_slow_down_answer_is_retried():
    replies = iter(
        [answer(error="Timeout. Maybe slow down a bit"), answer([comment(1, 1792022401)])]
    )

    comments = archive(lambda request: next(replies)).comments_created_between(DAY_START, DAY_END)

    assert [c.source_id for c in comments] == ["c1"]


def test_the_archive_is_reported_unavailable_after_the_last_attempt():
    with pytest.raises(ArchiveUnavailable):
        archive(lambda request: answer(status=503)).comments_created_between(DAY_START, DAY_END)


def test_threads_are_looked_up_by_id():
    def handler(request):
        assert request.url.path == "/api/posts/ids"
        assert request.url.params["ids"] == "p1,p2"
        return answer(
            [{"id": "p1", "author": "a", "created_utc": 1792022400, "title": "Old thread"}]
        )

    [thread] = archive(handler).posts_by_id(["p1", "p2"])

    assert thread.title == "Old thread"
