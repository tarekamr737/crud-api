"""Normalization and validated scraper records."""


def normalize_price(price_text: str) -> float:
    """Convert a Books to Scrape pound price to a numeric GBP value."""
    value = price_text.strip()
    if not value.startswith("£"):
        raise ValueError(f"Invalid GBP price: {price_text!r}")
    try:
        return float(value.removeprefix("£"))
    except ValueError as error:
        raise ValueError(f"Invalid GBP price: {price_text!r}") from error


def normalize_book(raw_record: dict[str, object]) -> dict[str, object]:
    """Add normalized values without removing scraped source text."""
    normalized = dict(raw_record)
    normalized["price_gbp"] = normalize_price(str(raw_record.get("price_text", "")))
    return normalized
