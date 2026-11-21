import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from media_quality import enhance_photo, render_scene_frame, render_editorial_poster


class MediaQualityTests(unittest.TestCase):
    def test_photo_finishing_preserves_dimensions_and_jpeg(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "source.jpg"
            Image.new("RGB", (640, 480), (90, 110, 100)).save(path)
            result = enhance_photo(path)
            with Image.open(result) as image:
                self.assertEqual(image.size, (640, 480))
                self.assertEqual(image.format, "JPEG")

    def test_scene_frame_is_vertical_and_uses_consistent_layout(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.jpg"
            target = Path(folder) / "frame.jpg"
            Image.new("RGB", (720, 1280), (50, 90, 70)).save(source)
            render_scene_frame(
                source,
                {"beat": "THE RESPONSE", "on_screen_text": "Choose one useful next step."},
                target,
                scene_index=3,
            )
            with Image.open(target) as image:
                self.assertEqual(image.size, (1080, 1920))
                self.assertEqual(image.format, "JPEG")

    def test_scene_frame_rejects_overlong_caption(self):
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.jpg"
            target = Path(folder) / "frame.jpg"
            Image.new("RGB", (720, 1280), (50, 90, 70)).save(source)
            with self.assertRaisesRegex(ValueError, "three lines"):
                render_scene_frame(
                    source,
                    {"beat": "HOOK", "on_screen_text": " ".join(["unusuallylongword"] * 30)},
                    target,
                )

    def test_editorial_poster_is_photo_led_4_by_5(self):
        with tempfile.TemporaryDirectory() as folder:
            photo = Path(folder) / "photo.jpg"
            target = Path(folder) / "poster.png"
            Image.new("RGB", (1000, 700), (75, 105, 85)).save(photo)
            plan = {
                "pillar_label": "INTENTIONAL LIVING",
                "graphic": {
                    "headline": "Make room for a better choice",
                    "subtext": "Pause, notice what you need, and take one useful step.",
                },
            }
            render_editorial_poster(plan, target, photo)
            with Image.open(target) as image:
                self.assertEqual(image.size, (1080, 1350))
                self.assertEqual(image.format, "PNG")


if __name__ == "__main__":
    unittest.main()
