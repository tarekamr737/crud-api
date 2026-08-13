from __future__ import annotations

import pytest

from evals.run_evals import evaluate, load_cases
from src.llm.schema import TriageResult


def test_eval_set_has_exactly_the_eight_required_cases() -> None:
    cases = load_cases()

    assert len(cases) == 8
    assert {case["id"] for case in cases} == {
        "normal-billing",
        "clear-bug",
        "feature-request",
        "generic-other",
        "urgent-outage",
        "ambiguous",
        "prompt-injection",
        "empty-ish-valid",
    }


def test_eval_runner_scores_key_fields_and_prints_failures(
    capsys: pytest.CaptureFixture[str],
) -> None:
    cases = load_cases()[:2]
    results = iter(
        (
            TriageResult(
                category="billing",
                urgency="normal",
                suggested_team="billing",
                confidence=0.9,
                reason="The message reports a subscription charge.",
            ),
            TriageResult(
                category="other",
                urgency="normal",
                suggested_team="support",
                confidence=0.4,
                reason="The request is unclear.",
            ),
        )
    )

    report = evaluate(cases, classify=lambda _: next(results))

    assert report["passed_checks"] == 4
    assert report["total_checks"] == 6
    assert report["score"] == 66.7
    assert report["failed_case_ids"] == ["clear-bug"]
    assert "FAIL clear-bug" in capsys.readouterr().out
