# The Polite Scraper

> A respectful, deterministic Python pipeline that collects and validates the
> first 60 books from the Books to Scrape practice sandbox.

[![Python 3.10+](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Tests](https://img.shields.io/badge/tests-32%20passing-2EA44F)](scraper/tests)
[![Scope](https://img.shields.io/badge/scope-60%20books-6F42C1)](scraper/output/sample-run-report.json)

The project follows catalogue pagination instead of hardcoding product URLs,
uses an identifiable and rate-limited HTTP client, caches every successful
response, validates finished records with Pydantic, and reports every run with
auditable counters. One broken detail page is isolated and cannot terminate the
remaining work.

## Verified outcome

| Checkpoint | Result |
|---|---:|
| Catalogue pages followed | 3 |
| Unique product URLs discovered | 60 |
| Valid records written | 60 |
| Invalid records | 0 |
| Failed pages | 0 |
| Cached pages on rerun | 63 |
| Automated tests | 32 passing |

## Pipeline

```text
classify target
      ↓
fetch politely → cache HTML
      ↓
follow 3 catalogue pages
      ↓
discover + deduplicate 60 URLs
      ↓
extract → normalize → validate
      ↓
books.json / errors.json
      ↓
run-report.json
```

Each stage is small and independently testable. Networking is isolated in the
fetcher; parsers and models remain deterministic and make no HTTP requests.

## Quick start

### Prerequisites

- Python 3.10 or newer
- Internet access for the first run only

From the repository root on Windows:

```powershell
cd scraper
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m src.main
```

On macOS or Linux, replace `.\.venv\Scripts\python.exe` with
`.venv/bin/python`.

A successful run ends with:

```text
catalogue_pages=3 discovered=60 unique_urls=60 valid_records=60 invalid_records=0 failed_pages=0
```

## Outputs

The command creates or replaces the following files under `scraper/output/`:

| File | Purpose |
|---|---|
| `books.json` | Validated records only; expected count is 60 |
| `errors.json` | Rejected candidates with validation reasons |
| `run-report.json` | Timing, network/cache, record, and failure counters |

Generated output and cached HTML remain local and are ignored by Git. A
[representative cached-run report](scraper/output/sample-run-report.json) is
committed for review.

## Record contract

```json
{
  "title": "A Light in the Attic",
  "product_url": "https://books.toscrape.com/catalogue/a-light-in-the-attic_1000/index.html",
  "price_text": "£51.77",
  "price_gbp": 51.77,
  "availability_text": "In stock (22 available)",
  "rating_text": "Three",
  "description": "A collection of poems...",
  "source_page": "https://books.toscrape.com/",
  "fetched_at": "2026-08-13T14:19:17.260374Z"
}
```

`product_url` is the canonical identity. `description` may be `null`, while
`price_text`, `source_page`, and `fetched_at` preserve the original value and
provenance.

## Politeness and resilience

- Sends an honest `ThePoliteScraper` User-Agent.
- Applies a 15-second timeout and waits at least 0.5 seconds before every real
  request.
- Parses content only after HTTP 200 and stores successful HTML as UTF-8.
- Retries timeouts and 5xx responses once; never retries 403 or 404.
- Reuses cached pages instead of refetching them.
- Handles detail pages independently and records the failed URL and reason.
- Rebuilds outputs on every run and deduplicates by canonical `product_url`.

## Testing

Run the complete deterministic suite from `scraper/`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.tmp\pytest
```

Coverage focuses on the highest-risk behavior: price normalization, relative
URL resolution, duplicate removal, missing descriptions, malformed records,
cache reuse, retry boundaries, failure isolation, report accuracy, and the
60-good-record fake-URL scenario.

## Project structure

```text
scraper/
├── src/
│   ├── main.py       # CLI entry point
│   ├── fetcher.py    # HTTP safeguards, retries, and cache
│   ├── parser.py     # Catalogue and detail-page parsing
│   ├── models.py     # Normalization and Pydantic schema
│   └── pipeline.py   # Orchestration, storage, and reporting
├── tests/
├── output/
├── requirements.txt
└── README.md
```

## Target classification and ethics

[Books to Scrape](https://books.toscrape.com/) explicitly identifies itself as
a scraping demo. Its `/robots.txt` endpoint returned HTTP 404 when checked on
2026-08-13, meaning no robots directives were published at that location. The
absence of a robots file is not treated as permission for broad crawling: this
implementation remains limited to catalogue pages 1–3 and their 60 products.

I will not reuse this code on another site without checking its rules and terms
first. The scraper does not access authentication walls, bypass blocks, collect
personal data, or execute scraped content.

## Limitations

The selectors intentionally target the current Books to Scrape HTML structure;
a redesign may require parser updates. Browser automation is unnecessary because
all required data is present in server-rendered HTML.

## Earlier repository work

The `app/`, `compose.yaml`, and related root-level tests contain an earlier
FastAPI/PostgreSQL CRUD exercise with Supabase authentication. They remain in
the history and repository, but are independent of the scraper under
`scraper/`.
