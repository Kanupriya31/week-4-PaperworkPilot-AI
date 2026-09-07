from __future__ import annotations

import unittest

from agent.demo import DEMO_FORM_TEXT, demo_extraction
from agent.tools import assess_form_complexity, verify_extraction
from evaluation.benchmark import EXPECTED_MIX, load_cases, manifest
from evaluation.evaluators import checklist_actionability, evidence_faithfulness, no_personal_data_invention, requirement_recall


class Week4EvaluationTests(unittest.TestCase):
    def test_golden_dataset_has_required_distribution(self) -> None:
        summary = manifest(load_cases())
        self.assertEqual(summary["cases"], 40)
        self.assertEqual(summary["scenarioMix"], EXPECTED_MIX)
        self.assertGreaterEqual(summary["domainCount"], 20)

    def test_owner_approved_labels_can_be_uploaded_as_final_ground_truth(self) -> None:
        cases = load_cases(require_reviewed=True)
        self.assertEqual(len(cases), 40)
        self.assertTrue(all(case["metadata"]["label_status"] == "reviewed" for case in cases))

    def test_high_risk_form_routes_to_selective_audit(self) -> None:
        extraction, _coverage = verify_extraction(demo_extraction(), DEMO_FORM_TEXT)
        risky = "If applying by income, attach two pay stubs. Do not send originals. The notarized packet is due within 10 business days; see Page 3 of 4."
        audit = assess_form_complexity(risky, extraction)
        self.assertTrue(audit["auditRecommended"])
        self.assertGreaterEqual(audit["riskScore"], 3)

    def test_easy_form_stays_on_fast_path(self) -> None:
        extraction = {"fields": [], "documents": [], "warnings": []}
        audit = assess_form_complexity("Name: ____\nEmail: ____", extraction)
        self.assertFalse(audit["auditRecommended"])

    def test_code_evaluators_reward_complete_grounded_output(self) -> None:
        reference = {
            "fields": ["legal name"], "documents": ["photo ID"], "warnings": [],
            "must_leave_blank": ["legal name"], "min_checklist_items": 1,
        }
        outputs = {"analysis": {
            "requiredFields": [{"label": "Legal name", "status": "missing", "currentValue": "", "evidence": {"verified": True}}],
            "documents": [{"name": "Photo ID", "evidence": {"verified": True}}],
            "warnings": [], "checklist": [{"label": "Provide ID", "detail": "Attach a readable photo ID."}], "modelCalls": 1,
        }}
        self.assertEqual(requirement_recall({}, outputs, reference)["score"], 1)
        self.assertEqual(evidence_faithfulness({}, outputs, reference)["score"], 1)
        self.assertEqual(no_personal_data_invention({}, outputs, reference)["score"], 1)
        self.assertEqual(checklist_actionability({}, outputs, reference)["score"], 1)


if __name__ == "__main__":
    unittest.main()
