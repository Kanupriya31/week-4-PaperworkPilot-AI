# PaperworkPilot Week 4 Submission Runbook

## Deadline

The supplied project brief lists **Sunday, September 6, 2026** as the Builder of the Week deadline. Complete credential-backed experiments and link checks before recording the final Loom.

## Winning story

PaperworkPilot already looked strong in a demo. Week 4 asks the harder question: can it reliably find every submission requirement without inventing information—and can accuracy improve without making every run slower and more expensive?

The experiment compares:

- **Baseline:** one structured extraction call, deterministic evidence verification, and human approval.
- **Improved:** the same system plus a deterministic complexity gate that gives only high-risk forms one independent completeness-repair call.

This is a measurable agent-control improvement, not a cosmetic prompt rewrite.

## Finish in this order

1. Review all 40 dataset cases using `evaluation/DATASET_REVIEW.md`; correct labels and change every `label_status` to `reviewed`.
2. Add `OPENAI_API_KEY` and `LANGSMITH_API_KEY` to Replit Secrets or a local `.env`. Never commit them.
3. Install the updated requirements.
4. Validate and upload dataset version 1.0.0.
5. Run the baseline experiment.
6. Inspect and record the three largest baseline failure clusters before looking at the improved scores.
7. Run the improved experiment with the same model, dataset, evaluators, and concurrency.
8. Generate the measured report.
9. In LangSmith, open one trace for each dominant failure cluster and one improved trace for the same case.
10. Record the Loom only after every number and link is final.

```bash
pip install -r requirements.txt
python -m evaluation.run_week4 validate
python -m evaluation.run_week4 upload
python -m evaluation.run_week4 run --variant baseline --max-concurrency 2
python -m evaluation.run_week4 run --variant improved --max-concurrency 2
python -m evaluation.generate_report
```

## Required deliverables

- Golden dataset in LangSmith with 40 owner-reviewed cases
- Baseline experiment link and at least one verified trace
- Improved experiment link using the identical dataset version
- Generated measured report from `evaluation/results/MEASURED_REPORT.md`
- Case-level failure analysis with representative trace IDs
- GitHub repository link
- Loom video link
- Any spreadsheet or exported experiment table requested by the submission form

## 90-second Loom script

**0–12 seconds — Human problem**

“PaperworkPilot turns confusing forms into a submission plan. But a polished answer can still be dangerous if it silently misses one attachment or reverses one conditional rule.”

**12–25 seconds — Evaluation design**

“I built a 40-case golden dataset: 20 happy paths, 12 edge cases, six known failures, and two adversarial forms across 26 domains. I measure requirement recall, warning recall, evidence faithfulness, no-invention safety, checklist quality, latency, and cost.”

**25–38 seconds — Show the baseline**

Open the baseline experiment and one representative failure trace. Say exactly what it missed and show the source evidence. Do not generalize beyond the measured cases.

**38–55 seconds — Show the improvement**

“Instead of adding an expensive second model call everywhere, I added a deterministic complexity gate. Easy forms stay fast. Conditional, conflicting, negated, OCR-damaged, or incomplete forms receive one independent completeness audit.”

Open the completeness-gate child run and show its risk reasons and routing decision.

**55–73 seconds — Measured delta**

Show the generated metric table. State requirement recall, faithfulness, p95 latency, and cost before and after. Mention any metric that regressed or missed its pass bar.

**73–84 seconds — Safety evidence**

Open the prompt-injection or fabrication case. Show that missing SSN or identity values remain blank and the human checkpoint remains mandatory.

**84–90 seconds — Closing line**

“Week 3 proved that PaperworkPilot could act. Week 4 proves where it fails, how it improves, and what it costs. That is the difference between an impressive demo and an agent you can trust.”

## Final quality gate

- Exactly 40/40 examples completed in both experiments
- Zero secrets or real personal data in traces
- Dataset version identical across experiments
- Same model and evaluator code across experiments
- All numbers copied from generated evidence, not estimated
- Three failure clusters named with case IDs and traces
- Regressions and remaining limitations stated explicitly
- Every shared link opens in a private browser window
