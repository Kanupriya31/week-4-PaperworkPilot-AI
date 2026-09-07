from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
PASS_BARS = {
    "requirement_recall": 0.95,
    "warning_recall": 0.90,
    "evidence_faithfulness": 0.98,
    "no_personal_data_invention": 1.00,
    "checklist_actionability": 0.90,
    "model_call_efficiency": 0.80,
}


def latest(pattern: str) -> Path:
    matches = sorted((ROOT / "evaluation" / "results").glob(pattern))
    if not matches:
        raise FileNotFoundError(f"No measured result matches {pattern}. Run the LangSmith experiment first.")
    return matches[-1]


def load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if value.get("status") != "measured" or value.get("case_count") != 40:
        raise ValueError(f"{path} is not a complete measured 40-case experiment.")
    return value


def pct(value: float | None) -> str:
    return "N/A" if value is None else f"{value * 100:.1f}%"


def money(value: float | None) -> str:
    return "N/A" if value is None else f"${value:.4f}"


def cluster_failures(result: dict[str, Any]) -> list[tuple[str, int, list[str]]]:
    clusters: dict[str, list[str]] = defaultdict(list)
    for case in result["cases"]:
        scores = case["scores"]
        for metric, bar in PASS_BARS.items():
            if scores.get(metric, 0) < bar:
                clusters[f"{case['scenario']} · {metric}"].append(case["case_id"])
    ranked = sorted(clusters.items(), key=lambda item: (-len(item[1]), item[0]))
    return [(name, len(ids), ids[:3]) for name, ids in ranked[:5]]


def render(baseline: dict[str, Any], improved: dict[str, Any]) -> str:
    metric_keys = list(PASS_BARS)
    rows = []
    for key in metric_keys:
        before = baseline["aggregate_scores"].get(key, 0)
        after = improved["aggregate_scores"].get(key, 0)
        rows.append(f"| {key.replace('_', ' ').title()} | {pct(before)} | {pct(after)} | {after-before:+.1%} | {pct(PASS_BARS[key])} | {'PASS' if after >= PASS_BARS[key] else 'MISS'} |")
    clusters = cluster_failures(baseline)
    remaining = cluster_failures(improved)
    cluster_rows = "\n".join(f"| {name} | {count} | {', '.join(ids)} |" for name, count, ids in clusters) or "| None | 0 | — |"
    remaining_rows = "\n".join(f"| {name} | {count} | {', '.join(ids)} |" for name, count, ids in remaining) or "| None | 0 | — |"
    latency_delta = (improved.get("p95_latency_ms") or 0) - (baseline.get("p95_latency_ms") or 0)
    before_cost, after_cost = baseline.get("average_cost"), improved.get("average_cost")
    cost_delta = None if before_cost is None or after_cost is None else after_cost - before_cost
    return f"""# PaperworkPilot Week 4 — Measured Evaluation Report

> Generated only from two complete 40-case LangSmith experiments. No metric in this report is a placeholder.

## Evaluation one-liner

I measured requirement recall, warning recall, evidence faithfulness, no-invention safety, checklist actionability, model-call efficiency, p95 latency, and cost on PaperworkPilot using a 40-case golden dataset spanning happy paths, edges, known failures, and adversarial forms. I compared the Week 3 baseline with a Week 4 selective completeness-audit strategy.

## Measured delta

| Metric | Baseline | Improved | Delta | Pass bar | Result |
|---|---:|---:|---:|---:|---|
{chr(10).join(rows)}

| Operational metric | Baseline | Improved | Delta |
|---|---:|---:|---:|
| p50 latency | {baseline.get('p50_latency_ms')} ms | {improved.get('p50_latency_ms')} ms | {(improved.get('p50_latency_ms') or 0)-(baseline.get('p50_latency_ms') or 0):+} ms |
| p95 latency | {baseline.get('p95_latency_ms')} ms | {improved.get('p95_latency_ms')} ms | {latency_delta:+} ms |
| Average cost per form | {money(before_cost)} | {money(after_cost)} | {'N/A' if cost_delta is None else f'${cost_delta:+.4f}'} |
| Cost metadata coverage | {baseline.get('cost_coverage', 0)}/40 | {improved.get('cost_coverage', 0)}/40 | — |
| Errors | {baseline.get('error_count')} | {improved.get('error_count')} | {improved.get('error_count', 0)-baseline.get('error_count', 0):+} |

Baseline experiment: {baseline['experiment_url']}

Improved experiment: {improved['experiment_url']}

## Baseline failure clusters

| Cluster | Cases | Representative case IDs |
|---|---:|---|
{cluster_rows}

## Improvement under test

The improved agent adds a deterministic complexity gate after first-pass evidence verification. Easy forms remain on the one-call path. High-risk forms—conditional requirements, negation, timing, originals/copies, notarization, missing pages, OCR damage, or conflicting instructions—receive one targeted completeness-repair call. The repair must return the full strict schema and every claim is re-verified against exact source evidence.

## Remaining failure clusters

| Cluster | Cases | Representative case IDs |
|---|---:|---|
{remaining_rows}

## Honest interpretation

The measured delta shows whether selective verification improves accuracy enough to justify its latency and cost. A score below a pass bar remains a known limitation, not a marketing claim. Case-level traces should be used to inspect the three largest failure clusters before any further prompt or routing change.

## Production monitoring proposal

- Alert if seven-day requirement recall drops by more than 3 percentage points.
- Alert if any critical invention or prompt-injection failure occurs.
- Alert if p95 latency exceeds 12 seconds for more than 5% of runs.
- Alert if average cost per run increases by more than 25% day over day.
- Sample 10% of high-risk runs for an online faithfulness evaluator and human-review every critical failure.
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--improved", type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "evaluation" / "results" / "MEASURED_REPORT.md")
    args = parser.parse_args()
    baseline = load(args.baseline or latest("baseline-*.json"))
    improved = load(args.improved or latest("improved-*.json"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(baseline, improved), encoding="utf-8")
    comparison_path = args.output.with_name("CASE_COMPARISON.csv")
    write_case_comparison(baseline, improved, comparison_path)
    print(args.output)
    print(comparison_path)
    return 0


def write_case_comparison(baseline: dict[str, Any], improved: dict[str, Any], path: Path) -> None:
    before = {case["case_id"]: case for case in baseline["cases"]}
    after = {case["case_id"]: case for case in improved["cases"]}
    metric_keys = sorted({key for case in [*before.values(), *after.values()] for key in case["scores"]})
    columns = ["case_id", "scenario", "baseline_latency_ms", "improved_latency_ms", "baseline_cost", "improved_cost", "baseline_trace_id", "improved_trace_id"]
    for metric in metric_keys:
        columns.extend([f"baseline_{metric}", f"improved_{metric}", f"delta_{metric}"])
    with path.open("w", newline="", encoding="utf-8-sig") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        for case_id in sorted(before.keys() | after.keys()):
            old, new = before.get(case_id, {}), after.get(case_id, {})
            row = {
                "case_id": case_id,
                "scenario": new.get("scenario", old.get("scenario")),
                "baseline_latency_ms": old.get("latency_ms"), "improved_latency_ms": new.get("latency_ms"),
                "baseline_cost": old.get("total_cost"), "improved_cost": new.get("total_cost"),
                "baseline_trace_id": old.get("trace_id"), "improved_trace_id": new.get("trace_id"),
            }
            for metric in metric_keys:
                old_score = old.get("scores", {}).get(metric)
                new_score = new.get("scores", {}).get(metric)
                row[f"baseline_{metric}"] = old_score
                row[f"improved_{metric}"] = new_score
                row[f"delta_{metric}"] = None if old_score is None or new_score is None else round(new_score - old_score, 4)
            writer.writerow(row)


if __name__ == "__main__":
    raise SystemExit(main())
