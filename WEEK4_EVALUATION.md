# Week 4 Evaluation Design — PaperworkPilot

## Decision

Evaluate PaperworkPilot's ability to convert administrative forms into complete, source-grounded submission plans. This is an evaluation project: the product is the evidence showing where the Week 3 agent fails and whether a bounded improvement actually fixes it.

## Evaluation one-liner

I will measure requirement recall, warning recall, evidence faithfulness, no-invention safety, checklist actionability, model-call efficiency, p95 latency, and cost on PaperworkPilot using 40 owner-reviewed cases covering happy paths, edge cases, known failures, and adversarial content. I will compare the Week 3 baseline against a risk-routed selective completeness audit in LangSmith.

## Metric contract

| Metric | User outcome | Judge | Pass bar |
|---|---|---|---:|
| Requirement recall | User does not submit an incomplete form | Deterministic fuzzy set match to owner labels | ≥95% |
| Warning recall | User sees deadlines, conditions, and dangerous ambiguity | Deterministic concept coverage; optional calibrated LLM judge | ≥90% |
| Evidence faithfulness | Every claim is grounded in exact form text | Code check on verified evidence quotes | ≥98% |
| No personal-data invention | Missing answers stay missing | Exact behavioral check | 100% |
| Checklist actionability | User receives enough concrete steps | Code-based coverage and detail check | ≥90% |
| Model-call efficiency | Accuracy is not purchased with an unbounded loop | Code check: one call normally, at most two for high risk | ≥80% |
| p95 latency | The product remains usable | LangSmith trace timing | <12 seconds |
| Average cost | The workflow can support an affordable product | LangSmith token/cost metadata | <$0.05 per form |

## Dataset

- 40 cases across 26 domains
- 20 happy paths, 12 edge cases, 6 known failures, and 2 adversarial cases
- 13 easy, 9 medium, and 18 hard examples
- Privacy-safe text cases; no real applicant data
- Every reference label must receive owner review before upload

## Baseline

The baseline uses PaperworkPilot's Week 3 path: structured extraction, exact-quote evidence verification, profile matching, uncertainty review, a human checkpoint, and deterministic checklist generation. Complexity is recorded but no second repair call is allowed.

## Improvement hypothesis

Forms with conditionality, negation, deadlines, originals/copies, notarization, missing-page references, OCR damage, or conflicting instructions are more likely to contain silent omissions. A deterministic complexity gate should identify those forms and selectively request one independent completeness repair. Easy forms remain on the one-call path.

Expected effect: higher requirement and warning recall on hard cases, unchanged invention safety, a modest latency/cost increase concentrated only on high-risk forms.

## Trace contract

Every case-level LangSmith trace includes:

- Case ID, scenario, difficulty, dataset version, agent version, prompt strategy, and model
- LangGraph child runs for safety, dependency check, extraction, evidence verification, completeness gate, profile matching, uncertainty review, human checkpoint, and plan assembly
- Wrapped OpenAI child calls with token and cost metadata
- Final output, evaluator scores, errors, and elapsed time

Baseline and improved experiments use the same dataset version, evaluator code, concurrency, and model so the measured delta is attributable to the strategy change.

## Failure analysis method

1. Sort cases by requirement recall, then warning recall.
2. Inspect trace evidence for the lowest-scoring cases.
3. Cluster failures by scenario and metric rather than fixing isolated examples.
4. Quantify cluster frequency and operational cost.
5. Change only one bounded mechanism, re-run all 40 cases, and report improvements and regressions.

The report generator ranks the five largest scenario/metric clusters and inserts representative case IDs for trace review.

## Commands

```bash
python -m evaluation.run_week4 validate
python -m evaluation.run_week4 upload
python -m evaluation.run_week4 run --variant baseline
python -m evaluation.run_week4 run --variant improved
python -m evaluation.generate_report
```

Use `--with-llm-judge` only after the eight-case human calibration passes. Use `--allow-unreviewed` only to test plumbing, never for the submitted experiment.

## Evidence rules

- Never publish placeholder numbers as measured results.
- Never describe draft labels as human-reviewed.
- Keep the dataset fixed between baseline and improved runs.
- Preserve failed cases and regressions in the report.
- Link one representative LangSmith trace for each major failure cluster.
- State when a cost field is unavailable rather than treating it as zero.

## Production monitoring proposal

- Seven-day requirement recall drop greater than 3 percentage points
- Any critical personal-data invention or obeyed prompt injection
- p95 latency above 12 seconds on more than 5% of runs
- Average cost per run increasing more than 25% day over day
- Single node/tool failure rate above 5% for one hour
