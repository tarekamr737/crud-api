"""OpenRouter client configuration."""

from __future__ import annotations

import os

from openai import OpenAI


class LLMConfigurationError(RuntimeError):
    """Raised when required LLM configuration is missing."""


def required_setting(name: str) -> str:
    """Return a non-empty environment setting without exposing its value."""
    value = os.getenv(name, "").strip()
    if not value:
        raise LLMConfigurationError(f"Missing required environment variable: {name}")
    return value


def create_client() -> OpenAI:
    """Create an OpenAI-compatible client using environment settings only."""
    return OpenAI(
        base_url=required_setting("LLM_BASE_URL"),
        api_key=required_setting("LLM_API_KEY"),
    )


def configured_model() -> str:
    """Return the configured provider model name."""
    return required_setting("LLM_MODEL")
