from __future__ import annotations

import pytest

from src.llm.client import LLMConfigurationError, configured_model, create_client


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
