from __future__ import annotations

import re
from typing import Any, Iterable


STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "before", "by", "for", "from", "if",
    "in", "is", "of", "on", "or", "the", "to", "with", "within", "your",
}


def _normalize(value: str) -> str:
    value = value.casefold().replace("&", " and ").replace("$", " dollar ")
    return " ".join(re.findall(r"[a-z0-9]+", value))


def _tokens(value: str) -> set[str]:
    return {token for token in _normalize(value).split() if token not in STOPWORDS}


def _matches(expected: str, predicted: str) -> bool:
    expected_norm, predicted_norm = _normalize(expected), _normalize(predicted)
    if expected_norm in predicted_norm or predicted_norm in expected_norm:
        return True
    expected_tokens = _tokens(expected)
    if not expected_tokens:
        return False
    return len(expected_tokens & _tokens(predicted)) / len(expected_tokens) >= 0.6


def _coverage(expected: Iterable[str], predicted: Iterable[str]) -> tuple[float, list[str]]:
    expected_list, predicted_list = list(expected), list(predicted)
    missed = [item for item in expected_list if not any(_matches(item, candidate) for candidate in predicted_list)]
    score = 1.0 if not expected_list else (len(expected_list) - len(missed)) / len(expected_list)
    return round(score, 4), missed


def _analysis(outputs: dict[str, Any]) -> dict[str, Any]:
    return outputs.get("analysis", outputs)


def requirement_recall(inputs: dict, outputs: dict, reference_outputs: dict) -> dict[str, Any]:
    analysis = _analysis(outputs)
    expected = list(reference_outputs["fields"]) + list(reference_outputs["documents"])
    predicted = [item.get("label", "") for item in analysis.get("requiredFields", [])]
    predicted += [item.get("name", "") for item in analysis.get("documents", [])]
    score, missed = _coverage(expected, predicted)
    return {"key": "requirement_recall", "score": score, "comment": f"Missed: {missed}" if missed else "All labeled requirements found."}


def warning_recall(inputs: dict, outputs: dict, reference_outputs: dict) -> dict[str, Any]:
    analysis = _analysis(outputs)
    predicted = [f"{item.get('title', '')} {item.get('detail', '')}" for item in analysis.get("warnings", [])]
    predicted += [f"{analysis.get('urgency', {}).get('reason', '')} {analysis.get('confidenceNote', '')}"]
    predicted += [f"{item.get('title', '')} {item.get('detail', '')}" for item in analysis.get("reviewIssues", [])]
    score, missed = _coverage(reference_outputs["warnings"], predicted)
    return {"key": "warning_recall", "score": score, "comment": f"Missed: {missed}" if missed else "All labeled risks found."}


def evidence_faithfulness(inputs: dict, outputs: dict, reference_outputs: dict) -> dict[str, Any]:
    analysis = _analysis(outputs)
    evidence_items = [
        item
        for key in ("requiredFields", "documents", "warnings")
        for item in analysis.get(key, [])
        if item.get("title") != "Reviewer note"
    ]
    verified = sum(bool(item.get("evidence", {}).get("verified")) for item in evidence_items)
    score = 0.0 if not evidence_items else verified / len(evidence_items)
    return {"key": "evidence_faithfulness", "score": round(score, 4), "comment": f"{verified}/{len(evidence_items)} claims have exact verified evidence."}


def no_personal_data_invention(inputs: dict, outputs: dict, reference_outputs: dict) -> dict[str, Any]:
    analysis = _analysis(outputs)
    failures: list[str] = []
    for expected_blank in reference_outputs["must_leave_blank"]:
        matches = [field for field in analysis.get("requiredFields", []) if _matches(expected_blank, field.get("label", ""))]
        if any(str(field.get("currentValue", "")).strip() for field in matches):
            failures.append(expected_blank)
    additionally_invented = [
        field.get("label", "unknown field")
        for field in analysis.get("requiredFields", [])
        if field.get("status") == "missing" and str(field.get("currentValue", "")).strip()
    ]
    failures.extend(additionally_invented)
    return {"key": "no_personal_data_invention", "score": 0 if failures else 1, "comment": f"Invented values: {failures}" if failures else "No missing personal values were invented."}


def checklist_actionability(inputs: dict, outputs: dict, reference_outputs: dict) -> dict[str, Any]:
    checklist = _analysis(outputs).get("checklist", [])
    required = max(1, int(reference_outputs["min_checklist_items"]))
    score = min(1.0, len(checklist) / required)
    vague = sum(len(str(item.get("detail", "")).split()) < 4 for item in checklist)
    if checklist and vague:
        score *= max(0.5, 1 - vague / len(checklist))
    return {"key": "checklist_actionability", "score": round(score, 4), "comment": f"{len(checklist)} steps; {vague} have underspecified detail."}


def model_call_efficiency(inputs: dict, outputs: dict, reference_outputs: dict) -> dict[str, Any]:
    calls = int(_analysis(outputs).get("modelCalls", outputs.get("model_calls", 0)))
    score = 1.0 if calls <= 1 else 0.75 if calls == 2 else 0.0
    return {"key": "model_call_efficiency", "score": score, "comment": f"{calls} model call(s); two are allowed only on high-risk forms."}


CODE_EVALUATORS = [
    requirement_recall,
    warning_recall,
    evidence_faithfulness,
    no_personal_data_invention,
    checklist_actionability,
    model_call_efficiency,
]
