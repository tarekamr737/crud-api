import pytest

from src.parser import parse_book


BOOK_HTML = """
<html><body>
  <div class="product_main">
    <h1>A Test Book</h1>
    <p class="price_color">£51.77</p>
    <p class="instock availability"> In stock (22 available) </p>
    <p class="star-rating Three"></p>
  </div>
  <div id="product_description"><h2>Product Description</h2></div>
  <p>A useful description.</p>
</body></html>
"""


def test_extracts_all_eight_raw_book_fields() -> None:
    record = parse_book(
        BOOK_HTML,
        product_url="https://books.toscrape.com/catalogue/a-test-book/index.html",
        source_page="https://books.toscrape.com/",
        fetched_at="2026-08-13T10:00:00+00:00",
    )

    assert record == {
        "title": "A Test Book",
        "product_url": "https://books.toscrape.com/catalogue/a-test-book/index.html",
        "price_text": "£51.77",
        "availability_text": "In stock (22 available)",
        "rating_text": "Three",
        "description": "A useful description.",
        "source_page": "https://books.toscrape.com/",
        "fetched_at": "2026-08-13T10:00:00+00:00",
    }


def test_missing_description_is_none() -> None:
    record = parse_book(
        BOOK_HTML.replace(
            '<div id="product_description"><h2>Product Description</h2></div>\n  <p>A useful description.</p>',
            "",
        ),
        product_url="https://books.toscrape.com/catalogue/a-test-book/index.html",
        source_page="https://books.toscrape.com/",
        fetched_at="2026-08-13T10:00:00+00:00",
    )

    assert record["description"] is None


def test_missing_required_field_is_rejected() -> None:
    with pytest.raises(ValueError, match="Missing required field: title"):
        parse_book(
            BOOK_HTML.replace("<h1>A Test Book</h1>", ""),
            product_url="https://books.toscrape.com/catalogue/a-test-book/index.html",
            source_page="https://books.toscrape.com/",
            fetched_at="2026-08-13T10:00:00+00:00",
        )
