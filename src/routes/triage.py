"""HTTP route for support triage."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from src.llm.schema import TriageRequest, TriageResult
from src.llm.service import (
    LLMOutputInvalidError,
    LLMTimeoutError,
    LLMUnavailableError,
    triage,
)


router = APIRouter()


@router.post("/triage", response_model=TriageResult, summary="Triage a support message")
def triage_message(payload: TriageRequest) -> TriageResult:
    try:
        return triage(payload.text)
    except LLMOutputInvalidError:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="Model output did not match the required schema",
        ) from None
    except LLMTimeoutError:
        raise HTTPException(
            status_code=status.HTTP_504_GATEWAY_TIMEOUT,
            detail="LLM provider timed out",
        ) from None
    except LLMUnavailableError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="LLM service unavailable",
        ) from None
