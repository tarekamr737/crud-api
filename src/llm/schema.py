"""Validated request and response contract for support triage."""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator


class Category(str, Enum):
    BILLING = "billing"
    BUG = "bug"
    FEATURE = "feature"
    OTHER = "other"


class Urgency(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class SuggestedTeam(str, Enum):
    BILLING = "billing"
    ENGINEERING = "engineering"
    PRODUCT = "product"
    SUPPORT = "support"


class TriageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str = Field(min_length=1, max_length=2000)


class TriageResult(BaseModel):
    model_config = ConfigDict(extra="forbid")

    category: Category
    urgency: Urgency
    suggested_team: SuggestedTeam
    confidence: float = Field(ge=0.0, le=1.0)
    reason: str = Field(min_length=1, max_length=200)

    @field_validator("reason")
    @classmethod
    def reason_must_be_one_sentence(cls, value: str) -> str:
        reason = value.strip()
        if not reason:
            raise ValueError("reason must not be blank")
        if sum(reason.count(mark) for mark in ".!?") > 1:
            raise ValueError("reason must be one sentence")
        return reason


class JobStatus(str, Enum):
    QUEUED = "queued"
    RUNNING = "running"
    SUCCEEDED = "succeeded"
    FAILED = "failed"


class TriageJobAccepted(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    status: JobStatus
    status_url: str


class TriageJobStatus(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: UUID
    status: JobStatus
    attempts: int = Field(ge=0)
    max_attempts: int = Field(ge=1)
    result: TriageResult | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
