from __future__ import annotations

import argparse
import json
import os
from datetime import datetime, timezone
from pathlib import Path
from statistics import mean
from typing import Any

from dotenv import load_dotenv
from langsmith import Client

from evaluation.benchmark import DATASET_NAME, load_cases, manifest
from evaluation.evaluators import CODE_EVALUATORS
from evaluation.llm_judge import make_grounded_quality_judge
from evaluation.targets import make_target


ROOT = Path(__file__).resolve().parents[1]
RESULTS_DIR = ROOT / "evaluation" / "results"
load_dotenv(ROOT / ".env")
PRICING_VERSION = "openai-official-standard-short-context-v1"
PUBLIC_MODEL_PRICING = {
    "gpt-5.6-luna": {"input": 0.20, "cached_input": 0.02, "output": 1.20},
}


def upload_dataset(client: Client, *, allow_unreviewed: bool) -> None:
    cases = load_cases(require_reviewed=not allow_unreviewed)
    if client.has_dataset(dataset_name=DATASET_NAME):
        dataset = client.read_dataset(dataset_name=DATASET_NAME)
        existing = list(client.list_examples(dataset_id=dataset.id))
        if existing:
            print(f"Dataset already exists with {len(existing)} examples: {dataset.id}")
            return
    else:
        dataset = client.create_dataset(
            dataset_name=DATASET_NAME,
            description="40 owner-reviewed forms: 20 happy, 12 edge, 6 known failure, 2 adversarial cases.",
        )
    examples = [{
        "inputs": {**case["input"], "case_id": case["id"]},
        "outputs": case["reference"],
        "metadata": {**case["metadata"], "case_id": case["id"], "dataset_version": "1.0.0"},
    } for case in cases]
    client.create_examples(dataset_id=dataset.id, examples=examples)
    print(f"Uploaded {len(examples)} examples to {dataset.name}: {dataset.id}")


def run_experiment(client: Client, variant: str, *, with_judge: bool, max_concurrency: int) -> Path:
    evaluators = list(CODE_EVALUATORS)
    if with_judge:
        evaluators.append(make_grounded_quality_judge())
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M")
    results = client.evaluate(
        make_target(variant),
        data=DATASET_NAME,
        evaluators=evaluators,
        experiment_prefix=f"paperworkpilot-{variant}-{stamp}",
        description=(
            "Week 3 baseline: single extraction pass plus deterministic evidence verification."
            if variant == "baseline" else
            "Week 4 candidate: risk-routed selective completeness repair plus deterministic evidence verification."
        ),
        max_concurrency=max_concurrency,
        metadata={
            "agent_version": variant,
            "dataset_version": "1.0.0",
            "models": [f"openai:{os.getenv('OPENAI_MODEL', 'gpt-5.6-luna')}"],
            "quality_strategy": "baseline" if variant == "baseline" else "selective-audit",
        },
    )
    rows = list(results)
    payload = serialize_experiment(results, rows, variant)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output = RESULTS_DIR / f"{variant}-{stamp}.json"
    output.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Saved local evidence: {output}")
    print(f"LangSmith experiment: {results.url}")
    return output


def serialize_experiment(results, rows: list[dict[str, Any]], variant: str) -> dict[str, Any]:
    cases: list[dict[str, Any]] = []
    for row in rows:
        run = row["run"]
        scores = {
            result.key: result.score
            for result in row["evaluation_results"]["results"]
            if result.score is not None
        }
        latency_ms = None
        if run.end_time and run.start_time:
            latency_ms = round((run.end_time - run.start_time).total_seconds() * 1000)
        outputs = getattr(run, "outputs", {}) or {}
        usage = outputs.get("model_usage", []) if isinstance(outputs, dict) else []
        if not usage and isinstance(outputs, dict):
            usage = (outputs.get("analysis") or {}).get("modelUsage", [])
        usage = usage if isinstance(usage, list) else []
        input_tokens = sum(int(item.get("input_tokens", 0) or 0) for item in usage if isinstance(item, dict))
        output_tokens = sum(int(item.get("output_tokens", 0) or 0) for item in usage if isinstance(item, dict))
        estimated_cost = estimate_cost(usage)
        cases.append({
            "case_id": row["example"].metadata.get("case_id"),
            "scenario": row["example"].metadata.get("scenario"),
            "scores": scores,
            "latency_ms": latency_ms,
            "prompt_tokens": run_metric(run, "prompt_tokens", "input_tokens"),
            "completion_tokens": run_metric(run, "completion_tokens", "output_tokens"),
            "total_tokens": run_metric(run, "total_tokens"),
            "total_cost": run_metric(run, "total_cost"),
            "model_usage": usage,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "estimated_cost": estimated_cost,
            "error": run.error,
            "trace_id": str(run.trace_id or run.id),
        })
    score_keys = sorted({key for case in cases for key in case["scores"]})
    aggregate_scores = {
        key: round(mean(case["scores"][key] for case in cases if key in case["scores"]), 4)
        for key in score_keys
    }

    latencies = sorted(case["latency_ms"] for case in cases if case["latency_ms"] is not None)
    costs = [float(case["estimated_cost"]) for case in cases if case["estimated_cost"] is not None]
    usage_cases = [case for case in cases if case["model_usage"]]
    return {
        "status": "measured",
        "variant": variant,
        "experiment_name": results.experiment_name,
        "experiment_url": results.url,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "case_count": len(cases),
        "aggregate_scores": aggregate_scores,
        "p50_latency_ms": percentile(latencies, 0.50),
        "p95_latency_ms": percentile(latencies, 0.95),
        "total_cost": round(sum(costs), 6) if costs else None,
        "average_cost": round(sum(costs) / len(costs), 6) if costs else None,
        "cost_coverage": len(costs),
        "usage_coverage": len(usage_cases),
        "pricing_version": PRICING_VERSION,
        "error_count": sum(bool(case["error"]) for case in cases),
        "cases": cases,
    }


def run_metric(run: Any, *names: str) -> Any:
    """Read usage/cost across LangSmith Run and RunTree result shapes."""
    for name in names:
        value = getattr(run, name, None)
        if value is not None:
            return value
    extra = getattr(run, "extra", {}) or {}
    usage = extra.get("usage_metadata") or extra.get("token_usage") or extra.get("usage") or {}
    if isinstance(usage, dict):
        for name in names:
            value = usage.get(name)
            if value is not None:
                return value
    metadata = getattr(run, "metadata", {}) or {}
    if isinstance(metadata, dict):
        usage = metadata.get("usage_metadata") or metadata.get("token_usage") or {}
        if isinstance(usage, dict):
            for name in names:
                value = usage.get(name)
                if value is not None:
                    return value
    return None


def estimate_cost(usage: list[dict[str, Any]]) -> float | None:
    """Estimate USD from provider usage and documented model rates."""
    model = str(usage[0].get("model", "")) if usage else os.getenv("OPENAI_MODEL", "gpt-5.6-luna")
    rates = PUBLIC_MODEL_PRICING.get(model, {})
    try:
        input_rate = float(os.getenv("OPENAI_INPUT_USD_PER_1M", rates.get("input", "")))
        cached_rate = float(os.getenv("OPENAI_CACHED_INPUT_USD_PER_1M", rates.get("cached_input", input_rate)))
        output_rate = float(os.getenv("OPENAI_OUTPUT_USD_PER_1M", rates.get("output", "")))
    except (TypeError, ValueError):
        return None
    if input_rate < 0 or cached_rate < 0 or output_rate < 0:
        return None
    total = 0.0
    for item in usage:
        if not isinstance(item, dict):
            continue
        input_tokens = int(item.get("input_tokens", 0) or 0)
        cached_tokens = min(input_tokens, int(item.get("cached_input_tokens", 0) or 0))
        total += ((input_tokens - cached_tokens) * input_rate) + (cached_tokens * cached_rate)
        total += (int(item.get("output_tokens", 0) or 0) * output_rate)
    return round(total / 1_000_000, 8)


def percentile(values: list[int], fraction: float) -> int | None:
    if not values:
        return None
    return values[min(len(values) - 1, round((len(values) - 1) * fraction))]


def main() -> int:
    parser = argparse.ArgumentParser(description="PaperworkPilot Week 4 LangSmith evaluation runner")
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("validate")
    upload = subparsers.add_parser("upload")
    upload.add_argument("--allow-unreviewed", action="store_true", help="Testing only; never use for final submission")
    run = subparsers.add_parser("run")
    run.add_argument("--variant", choices=["baseline", "improved", "both"], default="both")
    run.add_argument("--with-llm-judge", action="store_true")
    run.add_argument("--max-concurrency", type=int, default=2)
    args = parser.parse_args()

    if args.command == "validate":
        print(json.dumps(manifest(load_cases()), indent=2))
        return 0
    required_secrets = ("LANGSMITH_API_KEY",) if args.command == "upload" else ("OPENAI_API_KEY", "LANGSMITH_API_KEY")
    missing = [name for name in required_secrets if not os.getenv(name)]
    if missing:
        parser.error(f"Missing required secrets: {', '.join(missing)}")
    client = Client()
    if args.command == "upload":
        upload_dataset(client, allow_unreviewed=args.allow_unreviewed)
        return 0
    variants = ["baseline", "improved"] if args.variant == "both" else [args.variant]
    for variant in variants:
        run_experiment(client, variant, with_judge=args.with_llm_judge, max_concurrency=args.max_concurrency)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
