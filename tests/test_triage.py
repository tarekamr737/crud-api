from __future__ import annotations

import os
from datetime import datetime, timezone
from unittest.mock import patch
from uuid import uuid4

from fastapi.testclient import TestClient

os.environ.setdefault("DATABASE_URL", "postgresql://unused")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-anon-key")

import app.repository as app_repository


original_init_db = app_repository.init_db
app_repository.init_db = lambda: None
from app.main import app

app_repository.init_db = original_init_db
from src.jobs.repository import IdempotencyConflictError
from src.llm.schema import JobStatus


client = TestClient(app)


def job_record(status: JobStatus = JobStatus.QUEUED) -> dict[str, object]:
    now = datetime.now(timezone.utc)
    return {
        "id": uuid4(),
        "input_text": "I was charged twice.",
        "status": status,
        "attempts": 0,
        "max_attempts": 3,
        "result": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
    }


def test_submit_returns_202_without_calling_model() -> None:
    job = job_record()
    with (
        patch("src.routes.triage.enqueue_triage_job", return_value=job) as enqueue,
        patch("src.llm.service.complete") as completion,
    ):
        response = client.post(
            "/triage",
            headers={"Idempotency-Key": "request-123"},
            json={"text": "I was charged twice."},
        )

    assert response.status_code == 202
    assert response.json() == {
        "id": str(job["id"]),
        "status": "queued",
        "status_url": f"/triage/jobs/{job['id']}",
    }
    assert response.headers["location"] == f"/triage/jobs/{job['id']}"
    assert response.headers["retry-after"] == "1"
    enqueue.assert_called_once_with("I was charged twice.", "request-123")
    completion.assert_not_called()


def test_submission_requires_valid_input_and_idempotency_key() -> None:
    cases = (
        ({"Idempotency-Key": "key"}, {}, "text"),
        ({"Idempotency-Key": "key"}, {"text": ""}, "text"),
        ({"Idempotency-Key": "key"}, {"text": "x" * 2001}, "text"),
        ({"Idempotency-Key": "key"}, {"text": "ok", "extra": True}, "extra"),
        ({}, {"text": "ok"}, "idempotency-key"),
        ({"Idempotency-Key": "   "}, {"text": "ok"}, "idempotency-key"),
    )
    with patch("src.routes.triage.enqueue_triage_job") as enqueue:
        for headers, body, field in cases:
            response = client.post("/triage", headers=headers, json=body)
            assert response.status_code == 400
            assert field in response.json()["error"]
    enqueue.assert_not_called()


def test_reused_key_with_different_input_returns_409() -> None:
    with patch(
        "src.routes.triage.enqueue_triage_job",
        side_effect=IdempotencyConflictError,
    ):
        response = client.post(
            "/triage",
            headers={"Idempotency-Key": "same-key"},
            json={"text": "Different input"},
        )

    assert response.status_code == 409
    assert response.json() == {
        "detail": "Idempotency-Key was already used for different input"
    }


def test_status_returns_validated_result_without_input_text() -> None:
    job = job_record(JobStatus.SUCCEEDED)
    job["attempts"] = 1
    job["result"] = {
        "category": "billing",
        "urgency": "normal",
        "suggested_team": "billing",
        "confidence": 0.98,
        "reason": "The message reports a duplicate charge.",
    }
    with patch("src.routes.triage.get_triage_job", return_value=job):
        response = client.get(f"/triage/jobs/{job['id']}")

    assert response.status_code == 200
    assert response.json()["status"] == "succeeded"
    assert response.json()["result"] == job["result"]
    assert "input_text" not in response.json()


def test_unknown_status_job_returns_404() -> None:
    with patch("src.routes.triage.get_triage_job", return_value=None):
        response = client.get(f"/triage/jobs/{uuid4()}")

    assert response.status_code == 404
    assert response.json() == {"detail": "Triage job not found"}


def test_submit_does_not_consult_llm_kill_switch() -> None:
    job = job_record()
    with (
        patch.dict(os.environ, {"LLM_ENABLED": "false"}),
        patch("src.routes.triage.enqueue_triage_job", return_value=job),
        patch("src.llm.service.complete") as completion,
    ):
        response = client.post(
            "/triage",
            headers={"Idempotency-Key": "queued-while-disabled"},
            json={"text": "Valid input"},
        )

    assert response.status_code == 202
    completion.assert_not_called()
