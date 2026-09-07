from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
DATASET_FILES = [
    ROOT / "evaluation" / "golden_dataset.jsonl",
    ROOT / "evaluation" / "golden_dataset_extra.jsonl",
]
EXPECTED_MIX = {"happy": 20, "edge": 12, "known_failure": 6, "adversarial": 2}
DATASET_NAME = "PaperworkPilot Week 4 Golden Dataset v1"


def load_cases(*, require_reviewed: bool = False) -> list[dict[str, Any]]:
    cases: list[dict[str, Any]] = []
    for path in DATASET_FILES:
        for line_number, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if not raw.strip():
                continue
            try:
                cases.append(json.loads(raw))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON in {path.name}:{line_number}: {exc}") from exc
    validate_cases(cases, require_reviewed=require_reviewed)
    return cases


def validate_cases(cases: list[dict[str, Any]], *, require_reviewed: bool = False) -> None:
    ids = [case.get("id") for case in cases]
    if len(ids) != len(set(ids)):
        duplicates = sorted(item for item, count in Counter(ids).items() if count > 1)
        raise ValueError(f"Duplicate case IDs: {duplicates}")
    if len(cases) != 40:
        raise ValueError(f"Expected 40 cases, found {len(cases)}")
    mix = Counter(case.get("metadata", {}).get("scenario") for case in cases)
    if dict(mix) != EXPECTED_MIX:
        raise ValueError(f"Expected scenario mix {EXPECTED_MIX}, found {dict(mix)}")

    required_reference_keys = {"fields", "documents", "warnings", "must_leave_blank", "min_checklist_items"}
    for case in cases:
        if not case.get("input", {}).get("form_text", "").strip():
            raise ValueError(f"{case['id']} has no form text")
        missing = required_reference_keys - set(case.get("reference", {}))
        if missing:
            raise ValueError(f"{case['id']} is missing reference keys: {sorted(missing)}")
        if require_reviewed and case["metadata"].get("label_status") != "reviewed":
            raise ValueError(
                f"{case['id']} has not been owner-reviewed. Review every label, then set label_status to 'reviewed'."
            )


def manifest(cases: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "dataset": DATASET_NAME,
        "version": "1.0.0",
        "cases": len(cases),
        "scenarioMix": dict(Counter(case["metadata"]["scenario"] for case in cases)),
        "difficultyMix": dict(Counter(case["metadata"]["difficulty"] for case in cases)),
        "domainCount": len({case["metadata"]["domain"] for case in cases}),
        "reviewed": sum(case["metadata"].get("label_status") == "reviewed" for case in cases),
        "draft": sum(case["metadata"].get("label_status") != "reviewed" for case in cases),
    }


if __name__ == "__main__":
    print(json.dumps(manifest(load_cases()), indent=2))
