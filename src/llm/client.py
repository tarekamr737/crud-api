"""OpenRouter client configuration."""

from __future__ import annotations

import json
import os
import random
import time
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

from openai import APIStatusError, APITimeoutError, OpenAI
from openai.types.chat import ChatCompletionMessageParam

from src.llm.config import LLM_TIMEOUT_SECONDS, MAX_ATTEMPTS, PROMPT_VERSION


class LLMConfigurationError(RuntimeError):
    """Raised when required LLM configuration is missing."""


class LLMProviderTimeoutError(RuntimeError):
    """Raised after all provider timeout attempts are exhausted."""


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
        timeout=LLM_TIMEOUT_SECONDS,
    )


def configured_model() -> str:
    """Return the configured provider model name."""
    return required_setting("LLM_MODEL")


def retry_after_seconds(error: APIStatusError) -> float | None:
    """Parse a Retry-After delta or HTTP date when the provider supplies one."""
    value = error.response.headers.get("retry-after")
    if not value:
        return None
    try:
        return max(0.0, float(value))
    except ValueError:
        try:
            retry_at = parsedate_to_datetime(value)
        except (TypeError, ValueError):
            return None
        if retry_at.tzinfo is None:
            retry_at = retry_at.replace(tzinfo=timezone.utc)
        return max(0.0, (retry_at - datetime.now(timezone.utc)).total_seconds())


def is_retryable(error: Exception) -> bool:
    """Return true only for timeout, 429, and 5xx failures."""
    if isinstance(error, APITimeoutError):
        return True
    return isinstance(error, APIStatusError) and (
        error.status_code == 429 or error.status_code >= 500
    )


def retry_delay(error: Exception, attempt: int) -> float:
    """Return exponential backoff plus jitter, honoring Retry-After."""
    exponential = (2**attempt) + random.uniform(0.0, 0.25)
    if isinstance(error, APIStatusError):
        retry_after = retry_after_seconds(error)
        if retry_after is not None:
            return max(exponential, retry_after)
    return exponential


def log_model_call(
    model: str,
    duration_ms: int,
    repair_count: int,
    response: object | None,
) -> None:
    """Emit one safe structured line for one actual provider call."""
    usage = getattr(response, "usage", None)
    record = {
        "prompt_version": PROMPT_VERSION,
        "model": model,
        "input_tokens": getattr(usage, "prompt_tokens", 0) or 0,
        "output_tokens": getattr(usage, "completion_tokens", 0) or 0,
        "duration_ms": duration_ms,
        "repair_count": repair_count,
    }
    print(json.dumps(record, separators=(",", ":")), flush=True)


def complete(
    messages: list[ChatCompletionMessageParam],
    repair_count: int = 0,
) -> str:
    """Request one completion through the explicit bounded retry policy."""
    client = create_client()
    model = configured_model()
    last_error: Exception | None = None

    for attempt in range(MAX_ATTEMPTS):
        response = None
        started = time.perf_counter()
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0,
                max_tokens=250,
            )
            if not response.choices or not response.choices[0].message.content:
                raise RuntimeError("Provider returned no completion content")
        except Exception as error:
            duration_ms = round((time.perf_counter() - started) * 1000)
            log_model_call(model, duration_ms, repair_count, response)
            last_error = error
            if not is_retryable(error) or attempt == MAX_ATTEMPTS - 1:
                break
            time.sleep(retry_delay(error, attempt))
        else:
            duration_ms = round((time.perf_counter() - started) * 1000)
            log_model_call(model, duration_ms, repair_count, response)
            return response.choices[0].message.content

    if isinstance(last_error, APITimeoutError):
        raise LLMProviderTimeoutError("Provider timeout exhausted") from last_error
    if last_error is not None:
        raise last_error
    raise RuntimeError("Provider call failed without an error")
