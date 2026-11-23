import unittest

from editorial_quality import evaluate_editorial_plan


class EditorialQualityTests(unittest.TestCase):
    def good_plan(self):
        beats = ("HOOK / OPEN LOOP", "DEVELOPMENT", "RE-HOOK", "PAYOFF")
        return {
            "caption_video": "Take one step. #Nūr",
            "video": {"scenes": [
                {"beat": beat, "voiceover": narration, "image_prompt": prompt}
                for beat, narration, prompt in zip(
                    beats,
                    ("Notice what is happening.", "It can be hard to begin.", "You can start smaller.", "Choose one helpful step."),
                    ("window", "desk", "notebook", "walking path"),
                )],
            },
        }

    def test_complete_plan_scores_full_points(self):
        report = evaluate_editorial_plan(self.good_plan())
        self.assertEqual(report["score"], 100)
        self.assertEqual(report["status"], "advisory")
        self.assertEqual(report["warnings"], [])

    def test_missing_payoff_action_is_advisory_warning(self):
        plan = self.good_plan()
        plan["video"]["scenes"][-1]["voiceover"] = "Things can become easier."
        report = evaluate_editorial_plan(plan)
        self.assertLess(report["score"], 100)
        self.assertTrue(any("action" in warning.lower() for warning in report["warnings"]))
        self.assertEqual(report["status"], "advisory")

    def test_repeated_visual_prompts_are_flagged(self):
        plan = self.good_plan()
        plan["video"]["scenes"][1]["image_prompt"] = "window"
        report = evaluate_editorial_plan(plan)
        self.assertTrue(any("visual prompts" in warning.lower() for warning in report["warnings"]))

    def test_wrong_scene_arc_is_flagged(self):
        plan = self.good_plan()
        plan["video"]["scenes"][2]["beat"] = "DEVELOPMENT"
        report = evaluate_editorial_plan(plan)
        self.assertTrue(any("beat labels" in warning.lower() for warning in report["warnings"]))

    def test_malformed_plan_returns_diagnostics_not_exception(self):
        report = evaluate_editorial_plan({})
        self.assertEqual(report["score"], 0)
        self.assertEqual(report["checks_total"], 6)
        self.assertTrue(report["warnings"])


if __name__ == "__main__":
    unittest.main()
