from src.pipeline import START_URL, discover_catalogue_pages


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
