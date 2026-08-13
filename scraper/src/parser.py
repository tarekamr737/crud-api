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


def _required_text(soup: BeautifulSoup, selector: str, field: str) -> str:
    element = soup.select_one(selector)
    if element is None:
        raise ValueError(f"Missing required field: {field}")
    value = element.get_text(" ", strip=True)
    if not value:
        raise ValueError(f"Empty required field: {field}")
    return value


def parse_book(
    html: str,
    *,
    product_url: str,
    source_page: str,
    fetched_at: str,
) -> dict[str, str | None]:
    """Extract the eight required raw fields from one book detail page."""
    soup = BeautifulSoup(html, "html.parser")
    rating_element = soup.select_one("div.product_main p.star-rating")
    if rating_element is None:
        raise ValueError("Missing required field: rating_text")
    rating_text = next(
        (class_name for class_name in rating_element.get("class", []) if class_name != "star-rating"),
        None,
    )
    if rating_text is None:
        raise ValueError("Empty required field: rating_text")

    description_heading = soup.select_one("#product_description")
    description_element = (
        description_heading.find_next_sibling("p") if description_heading is not None else None
    )
    description = (
        description_element.get_text(" ", strip=True) if description_element is not None else None
    )

    return {
        "title": _required_text(soup, "div.product_main h1", "title"),
        "product_url": product_url,
        "price_text": _required_text(soup, "div.product_main p.price_color", "price_text"),
        "availability_text": _required_text(
            soup, "div.product_main p.instock.availability", "availability_text"
        ),
        "rating_text": rating_text,
        "description": description,
        "source_page": source_page,
        "fetched_at": fetched_at,
    }
