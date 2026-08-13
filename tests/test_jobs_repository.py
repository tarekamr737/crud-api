from __future__ import annotations

from uuid import uuid4

import os

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://unused")

from app.repository import connect, init_db
from src.jobs.repository import (
    IdempotencyConflictError,
    claim_next_job,
    complete_job,
    enqueue_triage_job,
    fail_job,
    get_triage_job,
)
from src.llm.schema import Category, JobStatus, SuggestedTeam, TriageResult, Urgency


@pytest.fixture(autouse=True)
def reset_jobs() -> None:
    init_db()
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE triage_jobs")


def make_due() -> None:
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("UPDATE triage_jobs SET available_at = NOW()")


def test_enqueue_is_idempotent_and_rejects_key_reuse() -> None:
    first = enqueue_triage_job("same input", "same-key")
    duplicate = enqueue_triage_job("same input", "same-key")

    assert duplicate["id"] == first["id"]
    assert duplicate["status"] is JobStatus.QUEUED
    with pytest.raises(IdempotencyConflictError):
        enqueue_triage_job("different input", "same-key")


def test_claim_retries_three_times_then_records_safe_failure() -> None:
    created = enqueue_triage_job("retry me", "retry-key")

    for expected_attempt in (1, 2):
        claimed = claim_next_job()
        assert claimed is not None
        assert claimed["attempts"] == expected_attempt
        assert fail_job(claimed) is False
        make_due()

    final_claim = claim_next_job()
    assert final_claim is not None
    assert final_claim["attempts"] == 3
    assert fail_job(final_claim) is True

    failed = get_triage_job(created["id"])
    assert failed is not None
    assert failed["status"] is JobStatus.FAILED
    assert failed["error"] == "Triage processing failed"
    assert claim_next_job() is None


def test_only_current_lease_can_complete_job() -> None:
    created = enqueue_triage_job("finish me", "finish-key")
    claimed = claim_next_job()
    assert claimed is not None
    stale_claim = {**claimed, "lease_token": uuid4()}
    result = TriageResult(
        category=Category.BUG,
        urgency=Urgency.NORMAL,
        suggested_team=SuggestedTeam.ENGINEERING,
        confidence=0.9,
        reason="The message reports a reproducible bug.",
    )

    assert complete_job(stale_claim, result) is False
    assert complete_job(claimed, result) is True
    completed = get_triage_job(created["id"])
    assert completed is not None
    assert completed["status"] is JobStatus.SUCCEEDED
    assert completed["result"] == result.model_dump(mode="json")
