"""OpenRouter client configuration."""

from __future__ import annotations

import os

from openai import OpenAI
from openai.types.chat import ChatCompletionMessageParam


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
        max_retries=0,
        timeout=30.0,
    )


def configured_model() -> str:
    """Return the configured provider model name."""
    return required_setting("LLM_MODEL")


def complete(messages: list[ChatCompletionMessageParam]) -> str:
    """Request one low-temperature completion and return its text."""
    response = create_client().chat.completions.create(
        model=configured_model(),
        messages=messages,
        temperature=0,
        max_tokens=250,
    )
    if not response.choices or not response.choices[0].message.content:
        raise RuntimeError("Provider returned no completion content")
    return response.choices[0].message.content
