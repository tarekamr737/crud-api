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
from src.llm.schema import JobStatus


client = TestClient(app)


def test_async_triage_http_contract() -> None:
    now = datetime.now(timezone.utc)
    job_id = uuid4()
    queued = {
        "id": job_id,
        "input_text": "Valid input",
        "status": JobStatus.QUEUED,
        "attempts": 0,
        "max_attempts": 3,
        "result": None,
        "error": None,
        "created_at": now,
        "updated_at": now,
    }
    failed = {
        **queued,
        "status": JobStatus.FAILED,
        "attempts": 3,
        "error": "Triage processing failed",
    }

    with (
        patch("src.routes.triage.enqueue_triage_job", return_value=queued),
        patch("src.routes.triage.get_triage_job", side_effect=[queued, failed]),
        patch("src.llm.service.complete") as completion,
    ):
        accepted = client.post(
            "/triage",
            headers={"Idempotency-Key": "audit-key"},
            json={"text": "Valid input"},
        )
        waiting = client.get(f"/triage/jobs/{job_id}")
        terminal = client.get(f"/triage/jobs/{job_id}")

    assert accepted.status_code == 202
    assert waiting.json()["status"] == "queued"
    assert waiting.json()["result"] is None
    assert terminal.json()["status"] == "failed"
    assert terminal.json()["attempts"] == 3
    assert terminal.json()["error"] == "Triage processing failed"
    assert "input_text" not in terminal.text
    completion.assert_not_called()
