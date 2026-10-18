"""Reads r/sailing from the Arctic Shift archive of Reddit (atlas OPEN-8).

The archive returns at most 100 items per request and asks callers to slow down when they
go too fast, so reads are paged, paced and retried.
"""

import logging
import time
from collections.abc import Callable, Sequence
from datetime import datetime

import httpx

from voices.ingestion.items import Item, comment_from_archive, post_from_archive
from voices.log import log_event

ARCHIVE_URL = "https://arctic-shift.photon-reddit.com"
SUBREDDIT = "sailing"
PAGE_SIZE = 100  # the archive's maximum
USER_AGENT = "community-voices/0.1 (coding challenge; github.com/brianaderer/transcendent)"

logger = logging.getLogger(__name__)


class ArchiveUnavailable(Exception):
    pass


class ArcticShift:
    def __init__(self, client: httpx.Client, pause_seconds: float, attempts: int):
        self.client = client
        self.pause_seconds = pause_seconds
        self.attempts = attempts

    def posts_created_between(self, start: datetime, end: datetime) -> list[Item]:
        return self._all_pages("/api/posts/search", start, end, post_from_archive)

    def comments_created_between(self, start: datetime, end: datetime) -> list[Item]:
        return self._all_pages("/api/comments/search", start, end, comment_from_archive)

    def posts_by_id(self, ids: Sequence[str]) -> list[Item]:
        posts = []
        for first in range(0, len(ids), PAGE_SIZE):
            chunk = ",".join(ids[first : first + PAGE_SIZE])
            posts += [post_from_archive(raw) for raw in self._get("/api/posts/ids", {"ids": chunk})]
        return posts

    def _all_pages(
        self, path: str, start: datetime, end: datetime, convert: Callable[[dict], Item]
    ) -> list[Item]:
        found: dict[str, Item] = {}
        after = int(start.timestamp())
        while True:
            page = self._get(path, _page_query(after, end))
            found.update((raw["id"], convert(raw)) for raw in page)
            if len(page) < PAGE_SIZE:
                return list(found.values())
            after = _next_page_start(after, page[-1]["created_utc"])

    def _get(self, path: str, query: dict) -> list[dict]:
        for attempt in range(1, self.attempts + 1):
            time.sleep(self.pause_seconds * attempt)
            data = self._try_get(path, query)
            if data is not None:
                return data
            log_event(logger, "archive.retry", path=path, attempt=attempt)
        raise ArchiveUnavailable(f"{path} failed {self.attempts} times")

    def _try_get(self, path: str, query: dict) -> list[dict] | None:
        """The page's items, or None when the archive asks us to try again."""
        try:
            response = self.client.get(path, params=query)
        except httpx.TransportError:
            return None
        if response.status_code != httpx.codes.OK:
            return None
        body = response.json()
        return None if body.get("error") else body["data"]


def _next_page_start(previous: int, last_on_page: int) -> int:
    """Pages start at the last item's second. If a whole page shared one second, step past it,
    or the same page would come back forever; the rare items lost are a fair price."""
    return last_on_page if last_on_page > previous else previous + 1


def _page_query(after: int, end: datetime) -> dict:
    return {
        "subreddit": SUBREDDIT,
        "after": after,
        "before": int(end.timestamp()),
        "limit": PAGE_SIZE,
        "sort": "asc",
    }


def connect_to_archive() -> ArcticShift:
    client = httpx.Client(base_url=ARCHIVE_URL, headers={"User-Agent": USER_AGENT}, timeout=30)
    return ArcticShift(client, pause_seconds=1.0, attempts=5)
