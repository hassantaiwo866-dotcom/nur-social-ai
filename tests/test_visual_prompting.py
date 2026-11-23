import unittest

from visual_prompting import compose_generation_prompt, build_stock_search_query


class VisualPromptingTests(unittest.TestCase):
    def test_generation_prompt_preserves_subject_and_adds_vertical_constraints(self):
        prompt = compose_generation_prompt(
            "A woman calmly writes in a notebook beside a window",
            camera_direction="close detail shot",
            movement="slow push in",
            beat="RE-HOOK",
            sequence_direction="Keep the same visual world and reveal a new detail.",
        )
        self.assertIn("woman calmly writes in a notebook", prompt)
        self.assertIn("vertical 9:16", prompt)
        self.assertIn("No text", prompt)
        self.assertIn("close detail shot", prompt)
        self.assertIn("RE-HOOK", prompt)
        self.assertIn("Story continuity direction:", prompt)
        self.assertIn("same visual world", prompt)

    def test_generation_prompt_rejects_empty_subject(self):
        with self.assertRaisesRegex(ValueError, "visual subject"):
            compose_generation_prompt("  ")

    def test_stock_query_removes_style_filler_and_limits_length(self):
        query = build_stock_search_query(
            "Premium cinematic documentary photograph of a person writing in a notebook, "
            "natural light, vertical portrait composition, realistic texture"
        )
        self.assertEqual(query, "writing notebook")
        self.assertLessEqual(len(query.split()), 12)

    def test_stock_query_uses_narration_to_add_action_context(self):
        query = build_stock_search_query(
            "A person beside a window",
            narration="They write a short plan before returning to focused work.",
        )
        self.assertIn("window", query)
        self.assertIn("write", query)
        self.assertIn("plan", query)

    def test_stock_query_has_fallback(self):
        self.assertEqual(build_stock_search_query("cinematic realistic natural light"), "wellbeing personal growth everyday life")


if __name__ == "__main__":
    unittest.main()
