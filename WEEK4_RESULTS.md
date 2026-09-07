# Week 4 measured results — PaperworkPilot

This snapshot records the completed public-model benchmark used for the submission candidate. The benchmark used the fixed owner-approved LangSmith dataset v1.0.0 (40 privacy-safe cases: 20 happy, 12 edge, six known failures, and two adversarial cases).

## Final optimized run

- Model: `gpt-5.6-luna`
- Cases: `40/40`
- Errors: `0`
- Requirement recall: `0.9473`
- Warning recall: `0.8438`
- Evidence faithfulness: `0.9796`
- Checklist actionability: `1.0000`
- Model-call efficiency: `0.9563`
- No personal-data invention: `0.9750`
- p95 latency: `31,384 ms`
- Total estimated cost: `$0.094899`
- Average estimated cost: `$0.002372` per case
- Usage coverage: `40/40`
- Cost coverage: `40/40`
- Pricing version: `openai-official-standard-short-context-v1`
- Evidence status: complete, valid JSON, measured, 40 recorded cases
- Experiment: [LangSmith optimized run](https://smith.langchain.com/o/783b2846-51e9-4de5-8672-f46b791650b0/datasets/3c88ba95-fef4-46df-bcf7-622f99547ad0/compare?selectedSessions=e2233031-c064-4276-b26a-4cadf029634f)

## Measured control-flow delta

The latency optimization changed the deterministic audit gate from `score >= 3` to `score >= 4` and used low reasoning effort for the selective audit. The run used 47 model calls across 40 cases: 33 cases used one call and seven high-risk cases used two calls. No case used more than two calls.

Compared with the prior public candidate, model-call efficiency improved from `0.9187` to `0.9563`, warning recall from `0.8104` to `0.8438`, evidence faithfulness from `0.9781` to `0.9796`, and total estimated cost from `$0.104542` to `$0.094899`. Requirement recall changed from `0.9528` to `0.9473`; this regression is retained here rather than hidden.

## Safety and provenance

The dataset is owner-approved, privacy-safe, and contains no production paperwork. The app keeps unknown personal fields blank, treats uploaded instructions as document content, and requires human approval before a submission plan is finalized. API keys belong in Replit Secrets only; they are not included in this repository.
