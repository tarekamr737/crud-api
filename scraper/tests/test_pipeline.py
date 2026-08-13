import json

from src.fetcher import FetchError
from src.models import normalize_book
from src.parser import parse_product_urls
from src.pipeline import (
    START_URL,
    collect_book_records,
    deduplicate_records,
    deduplicate_urls,
    discover_book_urls,
    discover_catalogue_pages,
    validate_and_store,
)


VALID_RAW_RECORD = {
    "title": "A Test Book",
    "product_url": "https://books.toscrape.com/catalogue/a-test-book/index.html",
    "price_text": "£51.77",
    "availability_text": "In stock (22 available)",
    "rating_text": "Three",
    "description": None,
    "source_page": "https://books.toscrape.com/",
    "fetched_at": "2026-08-13T10:00:00+00:00",
}


def test_discovers_exactly_three_catalogue_pages_via_next_links() -> None:
    page_2 = "https://books.toscrape.com/catalogue/page-2.html"
    page_3 = "https://books.toscrape.com/catalogue/page-3.html"
    html_by_url = {
        START_URL: '<li class="next"><a href="catalogue/page-2.html">next</a></li>',
        page_2: '<li class="next"><a href="page-3.html">next</a></li>',
        page_3: '<li class="next"><a href="page-4.html">next</a></li>',
    }
    calls: list[str] = []

    def fake_fetch(url: str) -> str:
        calls.append(url)
        return html_by_url[url]

    pages = discover_catalogue_pages(fake_fetch)

    assert [url for url, _ in pages] == [START_URL, page_2, page_3]
    assert calls == [START_URL, page_2, page_3]


def test_missing_next_link_is_reported_before_scope_is_complete() -> None:
    def fake_fetch(_: str) -> str:
        return "<html><body>No pagination</body></html>"

    try:
        discover_catalogue_pages(fake_fetch)
    except ValueError as error:
        assert "Missing next link before page 3" in str(error)
    else:
        raise AssertionError("missing next link should fail catalogue discovery")


def test_product_links_are_absolute_and_deduplicated_to_sixty() -> None:
    pages: list[tuple[str, str]] = []
    for page_number in range(1, 4):
        first_book = (page_number - 1) * 20 + 1
        links = "".join(
            f'<article class="product_pod"><h3><a href="book-{book}/index.html">Book</a></h3></article>'
            for book in range(first_book, first_book + 20)
        )
        if page_number == 3:
            links += '<article class="product_pod"><h3><a href="book-1/index.html">Duplicate</a></h3></article>'
        pages.append((f"https://books.toscrape.com/catalogue/page-{page_number}.html", links))

    urls = discover_book_urls(pages)

    assert len(urls) == 60
    assert len(set(urls)) == 60
    assert urls[0] == "https://books.toscrape.com/catalogue/book-1/index.html"
    assert urls[-1] == "https://books.toscrape.com/catalogue/book-60/index.html"


def test_relative_product_url_uses_page_url_as_its_base() -> None:
    html = '<article class="product_pod"><h3><a href="../a-book/index.html">Book</a></h3></article>'

    assert parse_product_urls(
        html, "https://books.toscrape.com/catalogue/category/page-2.html"
    ) == ["https://books.toscrape.com/catalogue/a-book/index.html"]


def test_duplicate_removal_preserves_first_seen_order() -> None:
    assert deduplicate_urls(["b", "a", "b", "c", "a"]) == ["b", "a", "c"]


def test_validation_routes_good_and_bad_records_to_separate_files(tmp_path) -> None:
    valid_candidate = normalize_book(VALID_RAW_RECORD)
    invalid_candidate = {
        **valid_candidate,
        "title": "",
        "product_url": "https://books.toscrape.com/catalogue/an-invalid-book/index.html",
    }

    valid, invalid = validate_and_store([valid_candidate, invalid_candidate], tmp_path)

    stored_books = json.loads((tmp_path / "books.json").read_text(encoding="utf-8"))
    stored_errors = json.loads((tmp_path / "errors.json").read_text(encoding="utf-8"))
    assert valid == stored_books
    assert invalid == stored_errors
    assert len(stored_books) == 1
    assert stored_books[0]["title"] == "A Test Book"
    assert len(stored_errors) == 1
    assert stored_errors[0]["product_url"] == invalid_candidate["product_url"]
    assert "title" in stored_errors[0]["reason"]
    assert all(record["title"] for record in stored_books)


def test_rerun_rebuilds_one_record_per_canonical_product_url(tmp_path) -> None:
    candidate = normalize_book(VALID_RAW_RECORD)
    duplicate = {**candidate, "title": "Duplicate should not win"}

    assert deduplicate_records([candidate, duplicate]) == [candidate]

    validate_and_store([candidate, duplicate], tmp_path)
    first_output = (tmp_path / "books.json").read_text(encoding="utf-8")
    validate_and_store([candidate, duplicate], tmp_path)
    second_output = (tmp_path / "books.json").read_text(encoding="utf-8")

    assert first_output == second_output
    assert len(json.loads(second_output)) == 1


def test_one_failed_detail_page_does_not_stop_later_books() -> None:
    urls = [
        "https://books.toscrape.com/catalogue/book-1/index.html",
        "https://books.toscrape.com/catalogue/broken/index.html",
        "https://books.toscrape.com/catalogue/book-2/index.html",
    ]
    source = "https://books.toscrape.com/"
    calls: list[str] = []

    def fake_fetch(url: str) -> str:
        calls.append(url)
        if url.endswith("broken/index.html"):
            raise FetchError(f"{url}: HTTP 404")
        return """
        <div class="product_main">
          <h1>Book</h1><p class="price_color">£12.34</p>
          <p class="instock availability">In stock</p>
          <p class="star-rating Four"></p>
        </div>
        """

    records, failures = collect_book_records(
        [(url, source) for url in urls],
        fake_fetch,
        timestamp_factory=lambda: "2026-08-13T10:00:00+00:00",
    )

    assert calls == urls
    assert [record["product_url"] for record in records] == [urls[0], urls[2]]
    assert failures == [{"url": urls[1], "reason": f"{urls[1]}: HTTP 404"}]
