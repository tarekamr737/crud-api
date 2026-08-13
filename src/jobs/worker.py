"""Polling worker for durable support-triage jobs."""

from __future__ import annotations

import json
import time

from app.repository import init_db
from src.jobs.repository import claim_next_job, complete_job, fail_job
from src.llm.service import triage


POLL_SECONDS = 1.0


def process_one_job() -> bool:
    """Process one available job and report whether work was claimed."""
    job = claim_next_job()
    if job is None:
        return False

    try:
        result = triage(job["input_text"])
    except Exception:
        if fail_job(job):
            print(
                json.dumps(
                    {
                        "event": "triage_job_failed",
                        "job_id": str(job["id"]),
                        "attempts": job["attempts"],
                        "alert": True,
                    }
                ),
                flush=True,
            )
    else:
        complete_job(job, result)
    return True


def run_worker() -> None:
    init_db()
    while True:
        try:
            worked = process_one_job()
        except Exception:
            print(
                json.dumps(
                    {"event": "triage_worker_error", "alert": True},
                ),
                flush=True,
            )
            worked = False
        if not worked:
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    run_worker()
