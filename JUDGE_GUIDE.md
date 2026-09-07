# PaperworkPilot Judge Guide

## The 20-second case

PaperworkPilot is an evidence-first paperwork agent that turns a form and optional profile into a verified, human-approved submission plan. It is intentionally built as a stateful LangGraph workflow with tools, retries, checkpoints, conditional routing, and executable evaluations—not as a one-shot model wrapper.

## Rubric-to-proof map

| Week 3 expectation | Visible proof | Code proof |
|---|---|---|
| Decides what to do next | Approval builds the plan; change requests pause for revision; stop ends safely | `agent/graph.py` conditional edges and route functions |
| Calls tools | Extraction, evidence verification, profile matching, ambiguity detection | `agent/tools.py` and graph nodes |
| Holds state | A paused run reopens and resumes with the same run ID | LangGraph `InMemorySaver`, `interrupt()`, and `GET /api/runs/{run_id}` |
| Recovers from errors | Verifier retry and dependency fallback both show **Recovered** | `RetryPolicy`, `dependency_check`, and fallback extractor |
| Hands off to a human | Every run pauses before final checklist creation | `human_checkpoint` node and approval screen |
| Does not invent | Account, SSN, vehicle, and student values remain blank when unknown | Allow-listed profile matcher plus non-invention tests |
| Has measurable success | 22 tests, five demo flows, 12 adversarial cases | `test/` and `evaluation/run_evals.py` |
| Complete implementation | Frontend, API, graph, fixtures, tests, evaluation, and docs are present | Repository tree and README |

## Best live path

1. Select **Parking permit** and click **Run selected demo**.
2. Narrate the seven visible pre-plan graph stages.
3. At review, show the recovered verifier and ambiguous deadline evidence.
4. Approve and resume the saved graph.
5. Show 100% evidence coverage, blank vehicle details, supporting documents, and the ordered checklist.
6. If asked about generality, switch to **Utility hardship** and point out the sensitive-data checkpoint.

To demonstrate the two behaviors most reviewers probe, run **Dependency outage recovery** and show the orange fallback trace, then run **Reject, revise, resume**, request changes, edit the instruction, and resume the same run.

## Hard questions and concise answers

### “Is this just a prompt wrapped in a UI?”

No. The workflow has explicit nodes, typed state, checkpoint persistence, retry policy, an interrupt, and conditional routing. The deterministic demos work without an API key because they test orchestration separately from model variability.

### “What happens when a tool fails?”

The verifier retries a transient error with backoff. The outage demo independently marks the primary extractor unavailable and routes through a conservative local extractor. Both paths are exposed in the trace; the outage path uses zero model calls.

### “Could it make up personal information?”

Profile matching can read only five allow-listed keys. Missing values stay empty and are labeled **Needs your answer**. Tests assert this for vehicle and Social Security fields.

### “Why does every run require approval?”

Paperwork mistakes can have legal, financial, or access consequences. The human checkpoint guards the transition from analysis to actionable plan creation, and the product never submits, signs, pays, or changes an external record.

### “How do you know extraction is grounded?”

Each field, document, and warning carries an exact quote and location. A verifier matches normalized quotes against the source and reports evidence coverage. All five deterministic scenarios reach 100%.

### “Is this production ready for sensitive forms?”

It is a defensible prototype, not a claim of universal production readiness. The UI and documentation explicitly identify the remaining controls: authentication, encrypted durable storage, retention policy, malware scanning, rate limiting, privacy review, and larger human-labeled evaluations.

## Verified release evidence

- 22 automated tests passed with zero failures.
- Prompt-injection routing: 12/12.
- Sensitive-field routing: 12/12.
- Evidence coverage: 100% for all five demos.
- Dependency outage: recovered with zero model calls.
- Reject/revise/resume: same run ID across both checkpoints.
- Invented values for missing fields: 0.
- Desktop and mobile browser checks: no horizontal overflow.
- Browser console warnings/errors: 0.
- Public-source secret scan: no API keys detected.

## Honest limitations

- Session checkpoints are intentionally in memory and expire on restart.
- Real OCR/model accuracy depends on scan quality and the configured model.
- The included synthetic evaluation is a control-flow and safety benchmark, not a universal form-accuracy claim.
- Image and scanned-PDF analysis requires `OPENAI_API_KEY`; deterministic demos and pasted-text fallback remain available without it.
