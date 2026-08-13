"""HTTP routes for asynchronous support triage."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Header, HTTPException, Response, status

from src.jobs.repository import (
    IdempotencyConflictError,
    enqueue_triage_job,
    get_triage_job,
)
from src.llm.schema import TriageJobAccepted, TriageJobStatus, TriageRequest


router = APIRouter()


@router.post(
    "/triage",
    response_model=TriageJobAccepted,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Queue a support message for triage",
)
def triage_message(
    payload: TriageRequest,
    response: Response,
    idempotency_key: str = Header(
        min_length=1,
        max_length=200,
        pattern=r".*\S.*",
    ),
) -> TriageJobAccepted:
    idempotency_key = idempotency_key.strip()
    try:
        job = enqueue_triage_job(payload.text, idempotency_key)
    except IdempotencyConflictError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Idempotency-Key was already used for different input",
        ) from None

    status_url = f"/triage/jobs/{job['id']}"
    response.headers["Location"] = status_url
    response.headers["Retry-After"] = "1"
    return TriageJobAccepted(
        id=job["id"],
        status=job["status"],
        status_url=status_url,
    )


@router.get(
    "/triage/jobs/{job_id}",
    response_model=TriageJobStatus,
    summary="Get a support triage job",
)
def triage_job_status(job_id: UUID) -> TriageJobStatus:
    job = get_triage_job(job_id)
    if job is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Triage job not found",
        ) from None

    return TriageJobStatus(
        id=job["id"],
        status=job["status"],
        attempts=job["attempts"],
        max_attempts=job["max_attempts"],
        result=job["result"],
        error=job["error"],
        created_at=job["created_at"],
        updated_at=job["updated_at"],
    )
