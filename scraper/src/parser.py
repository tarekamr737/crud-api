"""Catalogue and book-detail HTML parsing."""

from urllib.parse import urljoin

from bs4 import BeautifulSoup


def parse_next_url(html: str, page_url: str) -> str | None:
    """Return the absolute next-catalogue URL, if one is present."""
    soup = BeautifulSoup(html, "html.parser")
    link = soup.select_one("li.next a[href]")
    if link is None:
        return None
    return urljoin(page_url, str(link["href"]))


def parse_product_urls(html: str, page_url: str) -> list[str]:
    """Extract absolute product URLs from one catalogue page."""
    soup = BeautifulSoup(html, "html.parser")
    return [
        urljoin(page_url, str(link["href"]))
        for link in soup.select("article.product_pod h3 a[href]")
    ]
