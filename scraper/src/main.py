"""Command-line entry point for The Polite Scraper."""

from pathlib import Path
import time

from .pipeline import run_pipeline


def main() -> None:
    project_dir = Path(__file__).resolve().parents[1]
    report = run_pipeline(
        cache_dir=project_dir / "cache",
        output_dir=project_dir / "output",
        monotonic=time.monotonic,
    )
    print(
        "catalogue_pages={catalogue_pages} discovered={discovered} "
        "unique_urls={unique_urls} valid_records={valid_records} "
        "invalid_records={invalid_records} failed_pages={failed_pages}".format(**report)
    )


if __name__ == "__main__":
    main()
