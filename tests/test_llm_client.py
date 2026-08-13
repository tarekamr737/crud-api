from __future__ import annotations

import pytest

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from src.llm.client import LLMConfigurationError, complete, configured_model, create_client


def test_client_uses_only_llm_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.setenv("LLM_MODEL", "google/gemma-4-26b-a4b-it:free")

    client = create_client()

    assert str(client.base_url) == "https://openrouter.ai/api/v1/"
    assert configured_model() == "google/gemma-4-26b-a4b-it:free"


@pytest.mark.parametrize("name", ["LLM_BASE_URL", "LLM_API_KEY"])
def test_client_rejects_missing_required_setting(
    monkeypatch: pytest.MonkeyPatch,
    name: str,
) -> None:
    monkeypatch.setenv("LLM_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("LLM_API_KEY", "test-key")
    monkeypatch.delenv(name)

    with pytest.raises(LLMConfigurationError, match=f"{name}$"):
        create_client()


def test_completion_uses_configured_model_and_temperature_zero(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_MODEL", "google/gemma-4-26b-a4b-it:free")
    client = MagicMock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content='{"ok":true}'))]
    )
    messages = [{"role": "user", "content": "synthetic"}]

    with patch("src.llm.client.create_client", return_value=client):
        result = complete(messages)

    assert result == '{"ok":true}'
    client.chat.completions.create.assert_called_once_with(
        model="google/gemma-4-26b-a4b-it:free",
        messages=messages,
        temperature=0,
        max_tokens=250,
    )


def test_completion_rejects_missing_provider_content(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("LLM_MODEL", "google/gemma-4-26b-a4b-it:free")
    client = MagicMock()
    client.chat.completions.create.return_value = SimpleNamespace(choices=None)

    with (
        patch("src.llm.client.create_client", return_value=client),
        pytest.raises(RuntimeError, match="no completion content"),
    ):
        complete([{"role": "user", "content": "synthetic"}])
