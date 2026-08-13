"""Support-triage orchestration."""

from __future__ import annotations

import json
import os
from pathlib import Path

from src.llm.client import complete
from src.llm.schema import Category, SuggestedTeam, TriageResult, Urgency


PROMPT_VERSION = "triage-v1"
PROMPT_PATH = Path(__file__).resolve().parents[2] / "prompts" / f"{PROMPT_VERSION}.md"


class LLMUnavailableError(RuntimeError):
    """Raised while the real-model path is not available."""


def triage(text: str) -> TriageResult:
    """Return a deterministic stub or one validated provider result."""
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
        return TriageResult.model_validate(json.loads(raw_output))
    except Exception as error:
        raise LLMUnavailableError("The LLM triage provider is not available.") from error
