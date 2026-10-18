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
ERROR_TEXT_CHARACTERS = 200
# The archive asks callers to back off with this message, sometimes with status 422.
SLOW_DOWN = "slow down"
RATE_LIMIT_RESET = "x-ratelimit-reset"  # seconds until the archive's limit resets
ATTEMPTS = 7  # waits of about 1, 2, 4, 8, 16, 32 and 64 seconds: two minutes in all
USER_AGENT = "community-voices/0.1 (coding challenge; github.com/brianaderer/transcendent)"

logger = logging.getLogger(__name__)


class ArchiveUnavailable(Exception):
    pass


class ArcticShift:
    def __init__(
        self,
        client: httpx.Client,
        pause_seconds: float,
        attempts: int,
        sleep: Callable[[float], None] = time.sleep,
    ):
        self.client = client
        self.pause_seconds = pause_seconds
        self.attempts = attempts
        self.sleep = sleep

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
        """Each try waits first: a short pause, then twice as long after every failure, or as
        long as the archive says when it says."""
        last_error: _TryAgain | None = None
        wait = self.pause_seconds
        for attempt in range(1, self.attempts + 1):
            self.sleep(wait)
            try:
                return self._try_get(path, query)
            except _TryAgain as error:
                last_error = error
                log_event(logger, "archive.retry", path=path, attempt=attempt, reason=str(error))
                wait = max(self.pause_seconds * 2**attempt, error.wait_seconds)
        raise ArchiveUnavailable(
            f"{path} failed {self.attempts} times; last: {last_error}"
        ) from last_error

    def _try_get(self, path: str, query: dict) -> list[dict]:
        try:
            response = self.client.get(path, params=query)
        except httpx.TransportError as error:
            raise _TryAgain(repr(error)) from error
        if _worth_retrying(response.status_code):
            raise _TryAgain(f"status {response.status_code}", _stated_wait(response))
        body = _json_or_none(response)
        if response.status_code == httpx.codes.OK and body and not body.get("error"):
            return body["data"]
        reason = _reason(response, body)
        if SLOW_DOWN in reason:
            raise _TryAgain(f"slow down: {reason}", _stated_wait(response))
        raise ArchiveUnavailable(f"{path}: {response.status_code}: {reason}")


class _TryAgain(Exception):
    """The archive is busy or briefly unreachable; the same request may work in a moment."""

    def __init__(self, reason: str, wait_seconds: float = 0):
        super().__init__(reason)
        self.wait_seconds = wait_seconds


def _stated_wait(response: httpx.Response) -> float:
    """How long the archive says to wait before its limit resets, if it says."""
    try:
        return float(response.headers.get(RATE_LIMIT_RESET, 0))
    except ValueError:
        return 0


def _json_or_none(response: httpx.Response) -> dict | None:
    try:
        body = response.json()
    except ValueError:
        return None
    return body if isinstance(body, dict) else None


def _reason(response: httpx.Response, body: dict | None) -> str:
    """The archive's own error message, or the start of whatever page came back instead.

    Never empty: an answer with no text, or an error with no message, is named as such.
    """
    if body is None:
        return response.text[:ERROR_TEXT_CHARACTERS] or "an empty answer"
    return str(body.get("error") or "no reason given")


def _worth_retrying(status: int) -> bool:
    return status == httpx.codes.TOO_MANY_REQUESTS or status >= httpx.codes.INTERNAL_SERVER_ERROR


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
    return ArcticShift(client, pause_seconds=1.0, attempts=ATTEMPTS)
