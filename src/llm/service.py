"""Support-triage orchestration."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

from pydantic import ValidationError

from src.llm.client import LLMProviderTimeoutError, complete
from src.llm.config import PROMPT_VERSION
from src.llm.schema import Category, SuggestedTeam, TriageResult, Urgency


PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / f"{PROMPT_VERSION}.md"
QUARANTINE_PATH = Path(__file__).resolve().parents[2] / "logs" / "quarantine.jsonl"


class LLMUnavailableError(RuntimeError):
    """Raised while the real-model path is not available."""


class LLMOutputInvalidError(RuntimeError):
    """Raised when the model remains invalid after one repair."""


class LLMTimeoutError(RuntimeError):
    """Raised when all provider timeout attempts are exhausted."""


class OutputValidationFailure(ValueError):
    """Internal safe description of invalid untrusted model output."""


def parse_result(raw_output: str) -> TriageResult:
    """Parse and strictly validate untrusted provider text."""
    try:
        payload = json.loads(raw_output)
    except json.JSONDecodeError as error:
        raise OutputValidationFailure(
            f"invalid_json at line {error.lineno}, column {error.colno}"
        ) from None

    try:
        return TriageResult.model_validate(payload)
    except ValidationError as error:
        details = "; ".join(
            f"{'.'.join(str(part) for part in item['loc'])}: {item['type']}"
            for item in error.errors(include_url=False, include_input=False)
        )
        raise OutputValidationFailure(f"schema_invalid: {details}") from None


def repair_messages(
    raw_output: str,
    error: OutputValidationFailure,
) -> list[dict[str, str]]:
    """Build one JSON-encoded repair request for invalid output."""
    return [
        {"role": "system", "content": PROMPT_PATH.read_text(encoding="utf-8")},
        {
            "role": "user",
            "content": json.dumps(
                {
                    "task": (
                        "Repair this invalid output into the exact triage schema "
                        "and return JSON only."
                    ),
                    "invalid_output": raw_output,
                    "validation_error": str(error),
                },
                ensure_ascii=False,
            ),
        },
    ]


def sanitized_input(text: str, limit: int = 500) -> str:
    """Remove control characters and bound quarantined user text."""
    return "".join(character if character.isprintable() else " " for character in text)[
        :limit
    ]


def quarantine_failure(
    text: str,
    raw_output: str,
    error: OutputValidationFailure,
) -> None:
    """Append one bounded JSONL record after repair validation fails."""
    QUARANTINE_PATH.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sanitized_input": sanitized_input(text),
        "raw_model_output": raw_output[:2000],
        "error": str(error),
        "prompt_version": PROMPT_VERSION,
    }
    with QUARANTINE_PATH.open("a", encoding="utf-8") as quarantine:
        quarantine.write(json.dumps(record, ensure_ascii=False) + "\n")


def triage(text: str) -> TriageResult:
    """Return a deterministic stub or one validated provider result."""
    if os.getenv("LLM_ENABLED", "true").lower() == "false":
        raise LLMUnavailableError("LLM calls are disabled")
    if os.getenv("LLM_STUB", "0") == "1":
        return TriageResult(
            category=Category.OTHER,
            urgency=Urgency.LOW,
            suggested_team=SuggestedTeam.SUPPORT,
            confidence=0.25,
            reason="Stub mode returns a safe deterministic result.",
        )

    messages = [
        {"role": "system", "content": PROMPT_PATH.read_text(encoding="utf-8")},
        {
            "role": "user",
            "content": json.dumps({"text": text}, ensure_ascii=False),
        },
    ]
    try:
        raw_output = complete(messages)
    except LLMProviderTimeoutError as error:
        raise LLMTimeoutError("The LLM provider timed out.") from error
    except Exception as error:
        raise LLMUnavailableError("The LLM triage provider is not available.") from error

    try:
        return parse_result(raw_output)
    except OutputValidationFailure as first_error:
        try:
            repaired_output = complete(
                repair_messages(raw_output, first_error),
                repair_count=1,
            )
        except LLMProviderTimeoutError as error:
            raise LLMTimeoutError("The LLM provider timed out.") from error
        except Exception as error:
            raise LLMUnavailableError("The LLM triage provider is not available.") from error

    try:
        return parse_result(repaired_output)
    except OutputValidationFailure as final_error:
        quarantine_failure(text, repaired_output, final_error)
        raise LLMOutputInvalidError("Model output remained invalid after repair") from None
