from __future__ import annotations

import os
from pathlib import Path
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "postgresql://unused")
os.environ.setdefault("SUPABASE_URL", "https://example.supabase.co")
os.environ.setdefault("SUPABASE_KEY", "test-anon-key")

import app.repository as repository


original_init_db = repository.init_db
repository.init_db = lambda: None
from app.main import app

repository.init_db = original_init_db

from fastapi.testclient import TestClient

from src.llm.client import LLMProviderTimeoutError


client = TestClient(app)


def test_final_http_status_matrix(tmp_path: Path) -> None:
    valid = (
        '{"category":"billing","urgency":"normal",'
        '"suggested_team":"billing","confidence":0.9,'
        '"reason":"The message reports a duplicate charge."}'
    )
    cases = (
        (
            {"LLM_ENABLED": "true", "LLM_STUB": "0"},
            {"text": "I was charged twice."},
            [valid],
            200,
        ),
        (
            {"LLM_ENABLED": "true", "LLM_STUB": "0"},
            {"text": ""},
            [],
            400,
        ),
        (
            {"LLM_ENABLED": "true", "LLM_STUB": "0"},
            {"text": "Unclear"},
            ["bad-first", "bad-second"],
            422,
        ),
        (
            {"LLM_ENABLED": "false", "LLM_STUB": "0"},
            {"text": "Valid input"},
            [],
            503,
        ),
        (
            {"LLM_ENABLED": "true", "LLM_STUB": "0"},
            {"text": "Valid input"},
            [LLMProviderTimeoutError("private timeout")],
            504,
        ),
    )

    with patch("src.llm.service.QUARANTINE_PATH", tmp_path / "quarantine.jsonl"):
        for environment, body, effects, expected_status in cases:
            with (
                patch.dict(os.environ, environment),
                patch("src.llm.service.complete", side_effect=effects) as completion,
            ):
                response = client.post("/triage", json=body)

            assert response.status_code == expected_status
            if expected_status == 422:
                assert completion.call_count == 2
                assert "bad-first" not in response.text
                assert "bad-second" not in response.text
            if expected_status in {400, 503}:
                completion.assert_not_called()
            if expected_status == 504:
                assert "private" not in response.text
