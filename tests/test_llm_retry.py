from __future__ import annotations

import json
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import httpx
import pytest
from openai import APIStatusError, APITimeoutError

from src.llm.client import LLMProviderTimeoutError, complete


MESSAGES = [{"role": "user", "content": "synthetic"}]


def status_error(code: int, retry_after: str | None = None) -> APIStatusError:
    headers = {"Retry-After": retry_after} if retry_after else None
    request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    response = httpx.Response(code, headers=headers, request=request)
    return APIStatusError("provider error", response=response, body=None)


def valid_response() -> SimpleNamespace:
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok":true}'))],
        usage=SimpleNamespace(prompt_tokens=11, completion_tokens=7),
    )


def configured_client(side_effect: object) -> MagicMock:
    client = MagicMock()
    client.chat.completions.create.side_effect = side_effect
    return client


def test_429_retries_then_logs_each_actual_call(capsys: pytest.CaptureFixture[str]) -> None:
    client = configured_client([status_error(429, "4"), valid_response()])
    with (
        patch("src.llm.client.create_client", return_value=client),
        patch("src.llm.client.configured_model", return_value="test-model"),
        patch("src.llm.client.random.uniform", return_value=0.0),
        patch("src.llm.client.time.sleep") as sleep,
    ):
        assert complete(MESSAGES) == '{"ok":true}'

    sleep.assert_called_once_with(4.0)
    assert client.chat.completions.create.call_count == 2
    records = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert len(records) == 2
    assert records[-1] == {
        "prompt_version": "triage-v1",
        "model": "test-model",
        "input_tokens": 11,
        "output_tokens": 7,
        "duration_ms": records[-1]["duration_ms"],
        "repair_count": 0,
    }


@pytest.mark.parametrize("code", [400, 401, 403])
def test_non_retryable_client_errors_make_one_call(code: int) -> None:
    client = configured_client(status_error(code))
    with (
        patch("src.llm.client.create_client", return_value=client),
        patch("src.llm.client.configured_model", return_value="test-model"),
        patch("src.llm.client.time.sleep") as sleep,
        pytest.raises(APIStatusError),
    ):
        complete(MESSAGES)

    assert client.chat.completions.create.call_count == 1
    sleep.assert_not_called()


def test_5xx_stops_after_three_total_attempts(
    capsys: pytest.CaptureFixture[str],
) -> None:
    client = configured_client(status_error(503))
    with (
        patch("src.llm.client.create_client", return_value=client),
        patch("src.llm.client.configured_model", return_value="test-model"),
        patch("src.llm.client.random.uniform", return_value=0.0),
        patch("src.llm.client.time.sleep") as sleep,
        pytest.raises(APIStatusError),
    ):
        complete(MESSAGES, repair_count=1)

    assert client.chat.completions.create.call_count == 3
    assert [call.args[0] for call in sleep.call_args_list] == [1.0, 2.0]
    records = [json.loads(line) for line in capsys.readouterr().out.splitlines()]
    assert len(records) == 3
    assert all(record["repair_count"] == 1 for record in records)


def test_timeout_stops_after_three_total_attempts_and_maps_error() -> None:
    request = httpx.Request("POST", "https://openrouter.ai/api/v1/chat/completions")
    client = configured_client(APITimeoutError(request))
    with (
        patch("src.llm.client.create_client", return_value=client),
        patch("src.llm.client.configured_model", return_value="test-model"),
        patch("src.llm.client.random.uniform", return_value=0.0),
        patch("src.llm.client.time.sleep"),
        pytest.raises(LLMProviderTimeoutError),
    ):
        complete(MESSAGES)

    assert client.chat.completions.create.call_count == 3
