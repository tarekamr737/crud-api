from __future__ import annotations

import json
import os
from unittest.mock import patch
from uuid import uuid4

import pytest

os.environ.setdefault("DATABASE_URL", "postgresql://unused")

from src.jobs.worker import process_one_job, run_worker
from src.llm.schema import Category, SuggestedTeam, TriageResult, Urgency


def claimed_job(attempts: int = 1) -> dict[str, object]:
    return {
        "id": uuid4(),
        "input_text": "The app crashes.",
        "attempts": attempts,
        "max_attempts": 3,
        "lease_token": uuid4(),
    }


def valid_result() -> TriageResult:
    return TriageResult(
        category=Category.BUG,
        urgency=Urgency.NORMAL,
        suggested_team=SuggestedTeam.ENGINEERING,
        confidence=0.9,
        reason="The message reports an application crash.",
    )


def test_idle_worker_does_not_call_triage() -> None:
    with (
        patch("src.jobs.worker.claim_next_job", return_value=None),
        patch("src.jobs.worker.triage") as triage,
    ):
        assert process_one_job() is False
    triage.assert_not_called()


def test_worker_completes_claimed_job() -> None:
    job = claimed_job()
    result = valid_result()
    with (
        patch("src.jobs.worker.claim_next_job", return_value=job),
        patch("src.jobs.worker.triage", return_value=result) as triage,
        patch("src.jobs.worker.complete_job", return_value=True) as complete,
        patch("src.jobs.worker.fail_job") as fail,
    ):
        assert process_one_job() is True

    triage.assert_called_once_with(job["input_text"])
    complete.assert_called_once_with(job, result)
    fail.assert_not_called()


def test_worker_schedules_retry_without_alert(capsys: object) -> None:
    job = claimed_job(attempts=1)
    with (
        patch("src.jobs.worker.claim_next_job", return_value=job),
        patch("src.jobs.worker.triage", side_effect=RuntimeError("private detail")),
        patch("src.jobs.worker.fail_job", return_value=False) as fail,
    ):
        assert process_one_job() is True

    fail.assert_called_once_with(job)
    assert capsys.readouterr().out == ""  # type: ignore[attr-defined]


def test_terminal_failure_emits_safe_structured_alert(capsys: object) -> None:
    job = claimed_job(attempts=3)
    with (
        patch("src.jobs.worker.claim_next_job", return_value=job),
        patch(
            "src.jobs.worker.triage",
            side_effect=RuntimeError("private provider failure"),
        ),
        patch("src.jobs.worker.fail_job", return_value=True),
    ):
        assert process_one_job() is True

    output = capsys.readouterr().out  # type: ignore[attr-defined]
    alert = json.loads(output)
    assert alert == {
        "event": "triage_job_failed",
        "job_id": str(job["id"]),
        "attempts": 3,
        "alert": True,
    }
    assert "private" not in output
    assert job["input_text"] not in output


def test_worker_loop_alerts_and_survives_queue_error(capsys: object) -> None:
    with (
        patch("src.jobs.worker.init_db"),
        patch(
            "src.jobs.worker.process_one_job",
            side_effect=[RuntimeError("private database detail"), KeyboardInterrupt],
        ),
        patch("src.jobs.worker.time.sleep"),
        pytest.raises(KeyboardInterrupt),
    ):
        run_worker()

    output = capsys.readouterr().out  # type: ignore[attr-defined]
    assert json.loads(output) == {"event": "triage_worker_error", "alert": True}
    assert "private" not in output
