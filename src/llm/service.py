"""Support-triage orchestration."""

from __future__ import annotations

import os

from src.llm.schema import Category, SuggestedTeam, TriageResult, Urgency


class LLMUnavailableError(RuntimeError):
    """Raised while the real-model path is not available."""


def triage(text: str) -> TriageResult:
    """Return deterministic valid output in stub mode."""
    del text
    if os.getenv("LLM_STUB", "0") == "1":
        return TriageResult(
            category=Category.OTHER,
            urgency=Urgency.LOW,
            suggested_team=SuggestedTeam.SUPPORT,
            confidence=0.25,
            reason="Stub mode returns a safe deterministic result.",
        )
    raise LLMUnavailableError("The LLM triage provider is not available.")
