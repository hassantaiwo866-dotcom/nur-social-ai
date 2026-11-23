"""Regression tests for audience-connection story direction."""
import unittest

from storytelling import (
    AUDIENCE_CONNECTION_RULES,
    SCENE_AUDIENCE_DIRECTIONS,
    build_audience_connection_direction,
)


class StorytellingDirectionTests(unittest.TestCase):
    def test_direction_contains_four_distinct_emotional_beats(self):
        self.assertEqual(len(SCENE_AUDIENCE_DIRECTIONS), 4)
        self.assertEqual(len(set(SCENE_AUDIENCE_DIRECTIONS)), 4)
        direction = build_audience_connection_direction()
        for label in ("RECOGNITION", "TENSION", "REFRAME", "ACTION"):
            self.assertIn(label, direction)

    def test_direction_preserves_non_shaming_user_agency(self):
        direction = build_audience_connection_direction().lower()
        for phrase in ("dignity", "agency", "concrete", "small", "immediately"):
            self.assertIn(phrase, direction)
        self.assertTrue(any("shame" in rule.lower() for rule in AUDIENCE_CONNECTION_RULES))
        self.assertTrue(any("fabricated statistics" in rule.lower() for rule in AUDIENCE_CONNECTION_RULES))

    def test_direction_rejects_generic_disconnected_storytelling_by_guidance(self):
        direction = build_audience_connection_direction()
        self.assertIn("one coherent human story", direction)
        self.assertIn("recognition, tension, reframe, then practical action", direction)


if __name__ == "__main__":
    unittest.main()
