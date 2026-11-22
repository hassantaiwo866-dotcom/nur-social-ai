"""Final Day 2 visual-quality regression checks.

These tests exercise local rendering/prompt helpers only. They do not call
external providers or claim that a generated video has passed human review.
"""
import tempfile
import unittest
from pathlib import Path

from PIL import Image

from media_quality import render_scene_frame, render_scene_overlay
from visual_continuity import scene_sequence_direction
from visual_prompting import compose_generation_prompt


class DayTwoVisualCloseoutTests(unittest.TestCase):
    def test_collage_frame_and_overlay_render_as_vertical_assets(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "source.jpg"
            frame = root / "frame.jpg"
            overlay = root / "overlay.png"
            Image.new("RGB", (720, 1280), (80, 100, 90)).save(source)
            scene = {
                "beat": "RE-HOOK",
                "on_screen_text": "A different response is possible.",
            }

            render_scene_frame(
                source, scene, frame, scene_index=2,
                visual_style="tactile_editorial_collage",
            )
            render_scene_overlay(
                scene, overlay, scene_index=2,
                visual_style="hybrid_documentary_collage",
            )

            with Image.open(frame) as rendered:
                self.assertEqual(rendered.size, (1080, 1920))
                self.assertEqual(rendered.format, "JPEG")
            with Image.open(overlay) as rendered:
                self.assertEqual(rendered.size, (1080, 1920))
                self.assertEqual(rendered.mode, "RGBA")
                self.assertEqual(rendered.getpixel((500, 151))[:3], (11, 93, 59))

    def test_overlay_rejects_caption_that_cannot_fit(self):
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "overlay.png"
            scene = {
                "beat": "HOOK",
                "on_screen_text": " ".join(["unusuallylongword"] * 30),
            }
            with self.assertRaisesRegex(ValueError, "three lines"):
                render_scene_overlay(scene, target)

    def test_four_scene_continuity_and_prompt_are_connected(self):
        directions = [scene_sequence_direction(index, 4) for index in range(4)]
        self.assertEqual(len(set(directions)), 4)
        prompt = compose_generation_prompt(
            "A person writes a practical plan in a notebook",
            beat="PAYOFF",
            movement="slow stable hold",
            sequence_direction=directions[3],
        )
        self.assertIn("A person writes a practical plan", prompt)
        self.assertIn("PAYOFF", prompt)
        self.assertIn("Story continuity direction:", prompt)
        self.assertIn("grounded action", prompt.lower())


if __name__ == "__main__":
    unittest.main()
