from __future__ import annotations

import os
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.repository import connect, init_db
from src.jobs.worker import process_one_job


client = TestClient(app)


def test_submit_worker_status_and_idempotent_replay() -> None:
    init_db()
    with connect() as connection:
        with connection.cursor() as cursor:
            cursor.execute("TRUNCATE TABLE triage_jobs")

    headers = {"Idempotency-Key": "end-to-end-stub-job"}
    body = {"text": "The application crashes on startup."}
    with (
        patch.dict(os.environ, {"LLM_ENABLED": "true", "LLM_STUB": "1"}),
        patch("src.llm.service.complete") as completion,
    ):
        accepted = client.post("/triage", headers=headers, json=body)
        queued = client.get(accepted.json()["status_url"])
        worked = process_one_job()
        succeeded = client.get(accepted.json()["status_url"])
        replay = client.post("/triage", headers=headers, json=body)

    assert accepted.status_code == 202
    assert accepted.headers["location"] == accepted.json()["status_url"]
    assert queued.json()["status"] == "queued"
    assert worked is True
    assert succeeded.status_code == 200
    assert succeeded.json()["status"] == "succeeded"
    assert succeeded.json()["attempts"] == 1
    assert succeeded.json()["result"] == {
        "category": "other",
        "urgency": "low",
        "suggested_team": "support",
        "confidence": 0.25,
        "reason": "Stub mode returns a safe deterministic result.",
    }
    assert replay.status_code == 202
    assert replay.json()["id"] == accepted.json()["id"]
    completion.assert_not_called()
