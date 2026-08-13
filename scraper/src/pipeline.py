"""Scraping pipeline orchestration."""

from collections.abc import Callable
from datetime import datetime, timezone
import json
from pathlib import Path

from pydantic import ValidationError

from .fetcher import FetchError
from .models import BookRecord, normalize_book
from .parser import parse_book, parse_next_url, parse_product_urls


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


def deduplicate_urls(urls: list[str]) -> list[str]:
    """Keep one occurrence of each canonical URL in first-seen order."""
    return list(dict.fromkeys(urls))


def discover_book_urls(pages: list[tuple[str, str]]) -> list[str]:
    """Collect and deduplicate product links from fetched catalogue pages."""
    return [product_url for product_url, _ in discover_book_sources(pages)]


def discover_book_sources(pages: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """Return each unique product URL with its first source catalogue page."""
    discovered: list[tuple[str, str]] = []
    seen_urls: set[str] = set()
    for source_page, html in pages:
        for product_url in parse_product_urls(html, source_page):
            if product_url in seen_urls:
                continue
            seen_urls.add(product_url)
            discovered.append((product_url, source_page))
    return discovered


def deduplicate_records(records: list[dict[str, object]]) -> list[dict[str, object]]:
    """Keep the first candidate for each non-empty canonical product URL."""
    unique_records: list[dict[str, object]] = []
    seen_urls: set[str] = set()
    for record in records:
        product_url = str(record.get("product_url", ""))
        if product_url and product_url in seen_urls:
            continue
        if product_url:
            seen_urls.add(product_url)
        unique_records.append(record)
    return unique_records


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def collect_book_records(
    book_sources: list[tuple[str, str]],
    fetch_page: Callable[[str], str],
    *,
    timestamp_factory: Callable[[], str] = utc_now,
) -> tuple[list[dict[str, object]], list[dict[str, str]]]:
    """Fetch and transform each detail page without aborting later books."""
    records: list[dict[str, object]] = []
    failures: list[dict[str, str]] = []

    for product_url, source_page in book_sources:
        try:
            html = fetch_page(product_url)
            raw_record = parse_book(
                html,
                product_url=product_url,
                source_page=source_page,
                fetched_at=timestamp_factory(),
            )
            records.append(normalize_book(raw_record))
        except (FetchError, ValueError, OSError) as error:
            reason = str(error)
            failures.append({"url": product_url, "reason": reason})
            print(f"FAILED {product_url}: {reason}")

    return records, failures


def validate_and_store(
    normalized_records: list[dict[str, object]], output_dir: Path
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    """Validate every candidate and write separate valid/error JSON outputs."""
    valid_records: list[dict[str, object]] = []
    invalid_records: list[dict[str, object]] = []

    for candidate in deduplicate_records(normalized_records):
        try:
            valid_records.append(BookRecord.model_validate(candidate).model_dump(mode="json"))
        except ValidationError as error:
            invalid_records.append(
                {
                    "product_url": str(candidate.get("product_url", "")),
                    "reason": str(error),
                    "record": candidate,
                }
            )

    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "books.json").write_text(
        json.dumps(valid_records, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    (output_dir / "errors.json").write_text(
        json.dumps(invalid_records, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    return valid_records, invalid_records
