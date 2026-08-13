from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.llm.schema import TriageRequest, TriageResult


def test_request_accepts_only_text_between_one_and_two_thousand_characters() -> None:
    assert TriageRequest(text="x").text == "x"
    assert len(TriageRequest(text="x" * 2000).text) == 2000

    for payload in ({"text": ""}, {"text": "x" * 2001}, {"text": "ok", "extra": 1}):
        with pytest.raises(ValidationError):
            TriageRequest.model_validate(payload)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("category", "sales"),
        ("urgency", "critical"),
        ("suggested_team", "security"),
        ("confidence", 1.1),
        ("reason", "First sentence. Second sentence."),
    ),
)
def test_result_rejects_values_outside_the_closed_contract(
    field: str,
    value: object,
) -> None:
    payload = {
        "category": "other",
        "urgency": "low",
        "suggested_team": "support",
        "confidence": 0.25,
        "reason": "The request is unclear.",
    }
    payload[field] = value

    with pytest.raises(ValidationError):
        TriageResult.model_validate(payload)
