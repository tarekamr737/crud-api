"""Scraping pipeline orchestration."""

from collections.abc import Callable

from .parser import parse_next_url


START_URL = "https://books.toscrape.com/"
CATALOGUE_PAGE_LIMIT = 3


def discover_catalogue_pages(
    fetch_page: Callable[[str], str],
    *,
    start_url: str = START_URL,
    page_limit: int = CATALOGUE_PAGE_LIMIT,
) -> list[tuple[str, str]]:
    """Fetch exactly ``page_limit`` catalogue pages by following next links."""
    pages: list[tuple[str, str]] = []
    current_url = start_url

    for page_number in range(page_limit):
        html = fetch_page(current_url)
        pages.append((current_url, html))
        if page_number == page_limit - 1:
            break

        next_url = parse_next_url(html, current_url)
        if next_url is None:
            raise ValueError(f"Missing next link before page {page_limit}: {current_url}")
        current_url = next_url

    return pages
