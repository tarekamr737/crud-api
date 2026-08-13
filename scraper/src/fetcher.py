"""Polite HTTP fetching and HTML caching."""

from collections.abc import Callable
import time
from typing import Protocol

import requests


USER_AGENT = (
    "ThePoliteScraper/1.0 "
    "(educational scraper for books.toscrape.com; contact: tarekamr737 on GitHub)"
)
DEFAULT_TIMEOUT = 15.0
MIN_REQUEST_DELAY = 0.5


class ResponseLike(Protocol):
    status_code: int
    text: str


class SessionLike(Protocol):
    def get(
        self, url: str, *, headers: dict[str, str], timeout: float
    ) -> ResponseLike: ...


class FetchError(RuntimeError):
    """A page could not be fetched safely."""


def fetch_http(
    url: str,
    *,
    session: SessionLike = requests,
    timeout: float = DEFAULT_TIMEOUT,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    """Fetch one page with the project's required request safeguards."""
    sleep(MIN_REQUEST_DELAY)
    response = session.get(
        url,
        headers={"User-Agent": USER_AGENT},
        timeout=timeout,
    )
    if response.status_code != 200:
        raise FetchError(f"{url}: HTTP {response.status_code}")
    return response.text
