"""Run the eight labelled triage cases against the real configured model."""

from __future__ import annotations

import json
import os
import sys
from collections.abc import Callable
from datetime import date
from pathlib import Path
from typing import Any

from dotenv import load_dotenv


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.llm.config import PROMPT_VERSION
from src.llm.schema import TriageResult
from src.llm.service import triage


CASES_PATH = Path(__file__).with_name("cases.json")
SCORED_FIELDS = ("category", "urgency", "suggested_team")


def load_cases(path: Path = CASES_PATH) -> list[dict[str, Any]]:
    return json.loads(path.read_text(encoding="utf-8"))


def evaluate(
    cases: list[dict[str, Any]],
    classify: Callable[[str], TriageResult] = triage,
) -> dict[str, Any]:
    passed_checks = 0
    total_checks = len(cases) * len(SCORED_FIELDS)
    failed_case_ids: list[str] = []

    for case in cases:
        try:
            actual = classify(case["text"]).model_dump(mode="json")
        except Exception as error:
            failed_case_ids.append(case["id"])
            print(f"FAIL {case['id']}: {type(error).__name__}")
            continue

        mismatches = []
        for field in SCORED_FIELDS:
            expected = case["expected"][field]
            if actual[field] == expected:
                passed_checks += 1
            else:
                mismatches.append(
                    f"{field} expected={expected} actual={actual[field]}"
                )
        if mismatches:
            failed_case_ids.append(case["id"])
            print(f"FAIL {case['id']}: {'; '.join(mismatches)}")
        else:
            print(f"PASS {case['id']}")

    score = round(100 * passed_checks / total_checks, 1)
    report = {
        "score": score,
        "passed_checks": passed_checks,
        "total_checks": total_checks,
        "failed_case_ids": failed_case_ids,
        "date": date.today().isoformat(),
        "prompt_version": PROMPT_VERSION,
    }
    print(json.dumps(report, separators=(",", ":")))
    return report


def main() -> None:
    load_dotenv(ROOT / ".env")
    os.environ["LLM_ENABLED"] = "true"
    os.environ["LLM_STUB"] = "0"
    evaluate(load_cases())


if __name__ == "__main__":
    main()
