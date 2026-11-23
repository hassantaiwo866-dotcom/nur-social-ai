import unittest

from human_review import REVIEW_DECISIONS, REVIEW_ITEMS, build_human_review_checklist


class HumanReviewChecklistTests(unittest.TestCase):
    def test_checklist_starts_pending_and_requires_approval(self):
        checklist = build_human_review_checklist()
        self.assertEqual(checklist["status"], "pending")
        self.assertEqual(checklist["decision"], "pending")
        self.assertTrue(checklist["approval_required_before_publishing"])
        self.assertEqual(len(checklist["items"]), len(REVIEW_ITEMS))
        self.assertTrue(all(item["status"] == "pending" for item in checklist["items"]))

    def test_required_review_areas_are_present(self):
        ids = {item["id"] for item in REVIEW_ITEMS}
        self.assertTrue({
            "visual_relevance", "mobile_legibility", "audio_clarity",
            "audience_sensitivity", "factual_accuracy", "practical_value",
            "rights_attribution", "brand_consistency",
        }.issubset(ids))

    def test_checklist_instances_are_independent(self):
        first = build_human_review_checklist()
        second = build_human_review_checklist()
        first["items"][0]["status"] = "approved"
        self.assertEqual(second["items"][0]["status"], "pending")

    def test_decision_states_are_explicit(self):
        self.assertEqual(REVIEW_DECISIONS, ("pending", "approved", "needs_revision", "rejected"))


if __name__ == "__main__":
    unittest.main()
