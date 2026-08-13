from src.parser import parse_product_urls
from src.pipeline import START_URL, deduplicate_urls, discover_book_urls, discover_catalogue_pages


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
