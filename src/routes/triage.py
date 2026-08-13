"""HTTP route for support triage."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from src.llm.schema import TriageRequest, TriageResult
from src.llm.service import LLMUnavailableError, triage


router = APIRouter()


@router.post("/triage", response_model=TriageResult, summary="Triage a support message")
def triage_message(payload: TriageRequest) -> TriageResult:
    try:
        return triage(payload.text)
    except LLMUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service unavailable",
        ) from None
