from __future__ import annotations

from time import perf_counter
from typing import Any, Literal

from agent.graph import PaperworkGraph


Variant = Literal["baseline", "improved"]


def make_target(variant: Variant):
    strategy = "baseline" if variant == "baseline" else "selective-audit"

    def target(inputs: dict[str, Any]) -> dict[str, Any]:
        started = perf_counter()
        graph = PaperworkGraph(quality_strategy=strategy)
        paused = graph.start(
            source_text=inputs["form_text"],
            source_name=inputs.get("source_name", "Evaluation case"),
            profile=inputs.get("profile", {}),
            mode="ai",
            simulate_failure=False,
            failure_scenario="none",
        )
        if paused.get("status") != "waiting_review":
            return {
                "variant": variant,
                "status": paused.get("status", "failed"),
                "error": paused.get("error", "Agent did not reach the human checkpoint."),
                "analysis": {},
                "runtime_ms": round((perf_counter() - started) * 1000),
            }

        completed = graph.resume(paused["runId"], {
            "action": "approve",
            "note": "Automated evaluation approval; no form answer was changed.",
        })
        analysis = completed.get("analysis", {})
        analysis["reviewIssues"] = paused.get("review", {}).get("issues", [])
        return {
            "variant": variant,
            "status": completed.get("status", "failed"),
            "analysis": analysis,
            "model_usage": analysis.get("modelUsage", []),
            "runtime_ms": round((perf_counter() - started) * 1000),
            "case_id": inputs.get("case_id", "unknown"),
        }

    target.__name__ = f"paperworkpilot_{variant}_target"
    return target
