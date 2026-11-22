import unittest

from visual_continuity import scene_sequence_direction


class VisualContinuityTests(unittest.TestCase):
    def test_four_scene_arc_has_distinct_ordered_directions(self):
        directions = [scene_sequence_direction(i) for i in range(4)]
        self.assertEqual(len(set(directions)), 4)
        self.assertIn("OPEN", directions[0])
        self.assertIn("DEVELOP", directions[1])
        self.assertIn("RE-HOOK", directions[2])
        self.assertIn("PAYOFF", directions[3])

    def test_nonstandard_scene_count_has_safe_open_and_close(self):
        self.assertIn("Establish", scene_sequence_direction(0, 3))
        self.assertIn("concluding", scene_sequence_direction(2, 3))

    def test_invalid_scene_position_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "scene_index"):
            scene_sequence_direction(4, 4)

    def test_negative_scene_position_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "scene_index"):
            scene_sequence_direction(-1, 4)


if __name__ == "__main__":
    unittest.main()
