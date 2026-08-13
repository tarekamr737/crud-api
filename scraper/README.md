# The Polite Scraper

A small, deterministic Python scraper for the first three catalogue pages of
[Books to Scrape](https://books.toscrape.com/).

Setup, usage, data schema, and verified run details will be completed as the
pipeline checkpoints are implemented.

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
