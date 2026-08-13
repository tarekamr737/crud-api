import pytest

from src.models import normalize_book, normalize_price


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
