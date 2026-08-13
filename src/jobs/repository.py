"""PostgreSQL-backed triage job queue."""

from __future__ import annotations

import hashlib
from datetime import datetime
from typing import TypedDict
from uuid import UUID, uuid4

from psycopg.types.json import Jsonb

from app.repository import connect
from src.llm.schema import JobStatus, TriageResult


MAX_JOB_ATTEMPTS = 3
LEASE_SECONDS = 120


class IdempotencyConflictError(ValueError):
    """Raised when an idempotency key is reused for different input."""


class TriageJob(TypedDict):
    id: UUID
    input_text: str
    status: JobStatus
    attempts: int
    max_attempts: int
    result: dict[str, object] | None
    error: str | None
    created_at: datetime
    updated_at: datetime


class ClaimedJob(TypedDict):
    id: UUID
    input_text: str
    attempts: int
    max_attempts: int
    lease_token: UUID


def _request_hash(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _row_to_job(row: tuple[object, ...]) -> TriageJob:
    return TriageJob(
        id=row[0],
        input_text=row[1],
        status=JobStatus(row[2]),
        attempts=row[3],
        max_attempts=row[4],
        result=row[5],
        error=row[6],
        created_at=row[7],
        updated_at=row[8],
    )


def enqueue_triage_job(text: str, idempotency_key: str) -> TriageJob:
    """Create one job, or return the existing job for an identical retry."""
    request_hash = _request_hash(text)
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO triage_jobs (
                    id, idempotency_key, request_hash, input_text, max_attempts
                )
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (idempotency_key) DO NOTHING
                RETURNING id, input_text, status, attempts, max_attempts,
                          result, error, created_at, updated_at
                """,
                (uuid4(), idempotency_key, request_hash, text, MAX_JOB_ATTEMPTS),
            )
            row = cursor.fetchone()
            if row is None:
                cursor.execute(
                    """
                    SELECT id, input_text, status, attempts, max_attempts,
                           result, error, created_at, updated_at, request_hash
                    FROM triage_jobs
                    WHERE idempotency_key = %s
                    """,
                    (idempotency_key,),
                )
                existing = cursor.fetchone()
                if existing is None:
                    raise RuntimeError("idempotent job lookup failed")
                if existing[9] != request_hash:
                    raise IdempotencyConflictError(
                        "Idempotency-Key was already used for different input"
                    )
                row = existing[:9]
    return _row_to_job(row)


def get_triage_job(job_id: UUID) -> TriageJob | None:
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT id, input_text, status, attempts, max_attempts,
                       result, error, created_at, updated_at
                FROM triage_jobs
                WHERE id = %s
                """,
                (job_id,),
            )
            row = cursor.fetchone()
    return _row_to_job(row) if row is not None else None


def claim_next_job() -> ClaimedJob | None:
    """Lease one due job without allowing two workers to own its completion."""
    lease_token = uuid4()
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                WITH candidate AS (
                    SELECT id
                    FROM triage_jobs
                    WHERE (
                        status = 'queued' AND available_at <= NOW()
                    ) OR (
                        status = 'running' AND lease_expires_at <= NOW()
                    )
                    ORDER BY available_at, created_at
                    FOR UPDATE SKIP LOCKED
                    LIMIT 1
                )
                UPDATE triage_jobs AS job
                SET status = 'running',
                    attempts = CASE
                        WHEN job.status = 'queued' THEN job.attempts + 1
                        ELSE job.attempts
                    END,
                    lease_token = %s,
                    lease_expires_at = NOW() + (%s * INTERVAL '1 second'),
                    updated_at = NOW()
                FROM candidate
                WHERE job.id = candidate.id
                RETURNING job.id, job.input_text, job.attempts,
                          job.max_attempts, job.lease_token
                """,
                (lease_token, LEASE_SECONDS),
            )
            row = cursor.fetchone()
    if row is None:
        return None
    return ClaimedJob(
        id=row[0],
        input_text=row[1],
        attempts=row[2],
        max_attempts=row[3],
        lease_token=row[4],
    )


def complete_job(job: ClaimedJob, result: TriageResult) -> bool:
    """Commit a result only if this worker still owns the active lease."""
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE triage_jobs
                SET status = 'succeeded', result = %s, error = NULL,
                    lease_token = NULL, lease_expires_at = NULL, updated_at = NOW()
                WHERE id = %s AND status = 'running' AND lease_token = %s
                """,
                (Jsonb(result.model_dump(mode="json")), job["id"], job["lease_token"]),
            )
            return cursor.rowcount == 1


def fail_job(job: ClaimedJob) -> bool:
    """Schedule a bounded retry; return True only for terminal failure."""
    terminal = job["attempts"] >= job["max_attempts"]
    retry_delay = 2 ** (job["attempts"] - 1)
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                UPDATE triage_jobs
                SET status = %s,
                    error = %s,
                    available_at = CASE
                        WHEN %s THEN available_at
                        ELSE NOW() + (%s * INTERVAL '1 second')
                    END,
                    lease_token = NULL,
                    lease_expires_at = NULL,
                    updated_at = NOW()
                WHERE id = %s AND status = 'running' AND lease_token = %s
                """,
                (
                    "failed" if terminal else "queued",
                    "Triage processing failed" if terminal else None,
                    terminal,
                    retry_delay,
                    job["id"],
                    job["lease_token"],
                ),
            )
            updated = cursor.rowcount == 1
    return terminal and updated
