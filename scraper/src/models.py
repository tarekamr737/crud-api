"""Normalization and validated scraper records."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl


class BookRecord(BaseModel):
    """The one validated representation written to ``books.json``."""

    model_config = ConfigDict(extra="forbid")

    title: str = Field(min_length=1)
    product_url: HttpUrl
    price_text: str = Field(min_length=1)
    price_gbp: float = Field(ge=0)
    availability_text: str = Field(min_length=1)
    rating_text: str = Field(min_length=1)
    description: str | None
    source_page: HttpUrl
    fetched_at: datetime


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
