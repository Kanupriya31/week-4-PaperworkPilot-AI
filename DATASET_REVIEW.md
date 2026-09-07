# Golden Dataset Owner Review

The 40 supplied cases began as expert-authored draft labels. The owner returned the final-approval workbook with all 40 cases marked `Approve` on September 6, 2026. Every dataset case is now marked `reviewed`.

## AI pre-review revisions

An AI pre-review on September 6, 2026 corrected nine draft cases before owner approval: `happy-01-parking`, `happy-02-field-trip`, `happy-03-warranty`, `happy-04-pet-license`, `happy-11-daycare-pickup`, `happy-12-recreation`, `edge-05-notary`, `edge-06-copies-originals`, and `edge-11-continuation`. These changes improve submission-route specificity, field completeness, conditional wording, fee handling, and do-not-invent safeguards. The owner subsequently approved the revised labels through the final-approval workbook.

## Required review process

For each line in `golden_dataset.jsonl` and `golden_dataset_extra.jsonl`:

1. Read the complete `form_text` without looking at the reference labels.
2. Write down every required or conditional field, document, timing rule, signature, fee, submission route, and safety warning.
3. Compare your list with `reference`.
4. Correct omissions, duplicates, or wording that changes conditionality.
5. Confirm every `must_leave_blank` item really lacks a supplied profile value.
6. Set `label_status` to `reviewed` only after completing the check.

The upload command refuses draft labels by default. `--allow-unreviewed` exists only for plumbing tests and must never be used for the submitted experiment.

## Calibration set for the optional LLM judge

Human-score these eight outputs on the 1–5 rubric before enabling `--with-llm-judge`:

- `happy-01-parking`
- `happy-10-tuition`
- `edge-01-conditional-income`
- `edge-05-notary`
- `edge-10-bilingual`
- `failure-03-conflicting-deadlines`
- `failure-05-missing-page`
- `adversarial-02-fabrication`

Accept the judge only if it agrees exactly or within one point on at least 7/8 cases and never misses a human-labeled critical error. Report the calibration outcome, including disagreements. If it fails, omit the LLM judge and rely on deterministic evaluators plus human review.

## Provenance statement

Use this honest wording after review:

> The benchmark contains 40 manually reviewed, privacy-safe form scenarios modeled on common administrative workflows. No production user paperwork or personal data is included. The owner independently verified all expected requirements and risk labels before uploading dataset version 1.0.0 to LangSmith.
