import pytest
from pydantic import ValidationError

from src.models import BookRecord, normalize_book, normalize_price


VALID_RECORD = {
    "title": "A Test Book",
    "product_url": "https://books.toscrape.com/catalogue/a-test-book/index.html",
    "price_text": "£51.77",
    "price_gbp": 51.77,
    "availability_text": "In stock (22 available)",
    "rating_text": "Three",
    "description": None,
    "source_page": "https://books.toscrape.com/",
    "fetched_at": "2026-08-13T10:00:00+00:00",
}


def test_normalize_price_to_float() -> None:
    assert normalize_price("£51.77") == 51.77
    assert isinstance(normalize_price("£51.77"), float)


def test_normalize_book_preserves_original_price_text() -> None:
    normalized = normalize_book({"title": "Book", "price_text": "£10.00"})

    assert normalized["price_text"] == "£10.00"
    assert normalized["price_gbp"] == 10.0


@pytest.mark.parametrize("price_text", ["", "51.77", "£not-a-number"])
def test_malformed_price_is_rejected(price_text: str) -> None:
    with pytest.raises(ValueError, match="Invalid GBP price"):
        normalize_price(price_text)


def test_finished_book_schema_accepts_the_complete_record() -> None:
    record = BookRecord.model_validate(VALID_RECORD)

    assert record.model_dump(mode="json") == {
        **VALID_RECORD,
        "fetched_at": "2026-08-13T10:00:00Z",
    }


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("title", ""),
        ("product_url", "not-a-url"),
        ("price_gbp", -1.0),
        ("fetched_at", "not-a-timestamp"),
    ],
)
def test_finished_book_schema_rejects_malformed_fields(field: str, bad_value: object) -> None:
    malformed = {**VALID_RECORD, field: bad_value}

    with pytest.raises(ValidationError):
        BookRecord.model_validate(malformed)
