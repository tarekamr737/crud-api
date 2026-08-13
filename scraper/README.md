# The Polite Scraper

A small, deterministic Python scraper for the first three catalogue pages of
[Books to Scrape](https://books.toscrape.com/). It follows catalogue `next`
links, discovers 60 products, extracts and normalizes their details, validates
each finished record with Pydantic, and writes clean JSON plus an honest run
report. A failed detail page is recorded without stopping later books.

## Requirements and installation

- Python 3.10 or newer
- Internet access for the first run only

From the repository root:

```powershell
cd scraper
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

On macOS or Linux, use `.venv/bin/python` in place of
`.\.venv\Scripts\python.exe`.

## Run

From `scraper/`, run one command:

```powershell
.\.venv\Scripts\python.exe -m src.main
```

The command creates or replaces:

- `output/books.json` — valid records only; expected count: 60
- `output/errors.json` — schema-rejected candidates and reasons
- `output/run-report.json` — timing, cache, result, and failure counters

HTML is cached under `cache/`. Later runs reuse it and do not append duplicate
records. Generated run files and cached HTML are ignored by Git; the repository
contains only `output/sample-run-report.json` as representative output.

## Target classification

- **Target:** `https://books.toscrape.com/`, a public sandbox whose homepage
  says it is a demo website for web-scraping practice. It has no login or
  personal data and is appropriate for this educational exercise.
- **robots.txt result:** a checked request to
  `https://books.toscrape.com/robots.txt` returned HTTP 404 on 2026-08-13, so
  the site publishes no robots directives at that location.
- **Scope:** only catalogue pages 1, 2, and 3 and the 60 unique detail pages
  discovered from their `next` links.
- **Collected fields:** title, canonical product URL, price text,
  availability, rating, description, source catalogue page, and fetch time.

Even without published robots directives, this project uses an identifiable
User-Agent, timeouts, status checks, caching, and at least 0.5 seconds between
real requests.

I will not reuse this code on another site without checking its rules and terms first.

## Record schema

Each object in `books.json` has this shape:

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

`description` may be `null`. `product_url` is the canonical identity, and
`price_text`, `source_page`, and `fetched_at` preserve provenance.

## Politeness and failure behavior

- Every real request sends an identifiable `ThePoliteScraper` User-Agent, uses
  a 15-second timeout, and waits at least 0.5 seconds.
- HTTP content is parsed only after a 200 response and cached as UTF-8 HTML.
- Timeouts and 5xx responses retry once. HTTP 403 and 404 never retry.
- Cached pages are never fetched again unnecessarily.
- Each detail page is isolated; a fetch, parse, or normalization failure is
  logged and processing continues.

## Sample successful rerun report

```json
{
  "start_time": "2026-08-13T14:19:17.260374+00:00",
  "duration": 0.5,
  "pages_fetched": 0,
  "cache_hits": 63,
  "catalogue_pages": 3,
  "discovered": 60,
  "unique_urls": 60,
  "valid_records": 60,
  "invalid_records": 0,
  "failed_pages": 0,
  "failures": []
}
```

## Tests

From `scraper/`:

```powershell
.\.venv\Scripts\python.exe -m pytest -q --basetemp=.tmp\pytest
```

## Limitation and why no browser was required

The selectors are intentionally specific to the current Books to Scrape HTML;
a site redesign can require parser updates. No browser automation is needed
because catalogue links and book fields are present in the server-rendered
HTML—`requests` and Beautiful Soup are smaller, faster, and easier to cache.

## Ethics note

This code is limited to a public scraping practice sandbox, avoids personal or
authenticated data, does not bypass blocks, and collects only assignment
fields. A missing robots file is not treated as permission for broad crawling;
the fixed three-page scope and conservative request behavior still apply.
