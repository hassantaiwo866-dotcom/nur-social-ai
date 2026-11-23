import unittest
from unittest.mock import patch

from nur_generator import run_qa


def valid_plan():
    return {
        "topic_slug": "focus",
        "video": {
            "scenes": [
                {"image_prompt": "Morning sunlight in a quiet room"},
                {"image_prompt": "A person walking outdoors"},
                {"image_prompt": "A notebook beside a cup"},
                {"image_prompt": "Evening reflection by a window"},
            ]
        },
    }


class ProductionQAGateIntegrationTests(unittest.TestCase):
    @patch("output_validation.validate_media_outputs")
    def test_qa_includes_validation_metadata_and_manual_review(self, validate):
        validate.return_value = {
            "checks": ["Media files validated"],
            "metadata": {"video_width": 1080, "duration_seconds": 25.0},
        }
        report = run_qa("poster.png", "reel.mp4", valid_plan())
        self.assertEqual(report["status"], "passed")
        self.assertEqual(report["media_metadata"]["video_width"], 1080)
        self.assertTrue(report["manual_review_required"])
        validate.assert_called_once_with("poster.png", "reel.mp4")

    @patch("output_validation.validate_media_outputs")
    def test_qa_stops_when_media_validation_fails(self, validate):
        validate.side_effect = RuntimeError("Media output validation failed")
        with self.assertRaisesRegex(RuntimeError, "Media output validation failed"):
            run_qa("poster.png", "reel.mp4", valid_plan())

    @patch("output_validation.validate_media_outputs")
    def test_qa_rejects_shaming_language(self, validate):
        validate.return_value = {"checks": [], "metadata": {}}
        plan = valid_plan()
        plan["video"]["scenes"][0]["voiceover"] = "You are worthless"
        with self.assertRaisesRegex(RuntimeError, "shaming language"):
            run_qa("poster.png", "reel.mp4", plan)


if __name__ == "__main__":
    unittest.main()
