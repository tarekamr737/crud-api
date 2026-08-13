"""Polite HTTP fetching and HTML caching."""

from collections.abc import Callable
from dataclasses import dataclass
import hashlib
from pathlib import Path
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


@dataclass
class FetchStats:
    pages_fetched: int = 0
    cache_hits: int = 0


def fetch_http(
    url: str,
    *,
    session: SessionLike = requests,
    timeout: float = DEFAULT_TIMEOUT,
    sleep: Callable[[float], None] = time.sleep,
) -> str:
    """Fetch one page with safeguards and one allowed transient retry."""
    for attempt in range(2):
        sleep(MIN_REQUEST_DELAY)
        try:
            response = session.get(
                url,
                headers={"User-Agent": USER_AGENT},
                timeout=timeout,
            )
        except requests.Timeout as error:
            if attempt == 0:
                continue
            raise FetchError(f"{url}: timeout after one retry") from error
        except requests.RequestException as error:
            raise FetchError(f"{url}: request failed: {error}") from error

        if response.status_code == 200:
            return response.text
        if 500 <= response.status_code <= 599 and attempt == 0:
            continue
        raise FetchError(f"{url}: HTTP {response.status_code}")

    raise AssertionError("unreachable fetch state")


def cache_path_for(url: str, cache_dir: Path) -> Path:
    """Return the stable cache location for a URL."""
    digest = hashlib.sha256(url.encode("utf-8")).hexdigest()
    return cache_dir / f"{digest}.html"


def fetch(
    url: str,
    *,
    cache_dir: Path,
    stats: FetchStats,
    http_fetch: Callable[[str], str] = fetch_http,
) -> str:
    """Read cached HTML or fetch and cache it once."""
    cache_path = cache_path_for(url, cache_dir)
    if cache_path.exists():
        stats.cache_hits += 1
        print(f"CACHE HIT {url}")
        return cache_path.read_text(encoding="utf-8")

    print(f"FETCH {url}")
    html = http_fetch(url)
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_path.write_text(html, encoding="utf-8")
    stats.pages_fetched += 1
    return html
