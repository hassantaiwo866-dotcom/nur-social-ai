import base64
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image
import free_visual_models as models


class FreeVisualModelTests(unittest.TestCase):
    def test_image_model_is_allowlisted_and_saves_valid_image(self):
        with tempfile.TemporaryDirectory() as folder:
            buffer = io.BytesIO()
            Image.new("RGB", (640, 960), "#0B5D3B").save(buffer, "PNG")
            response = Mock()
            response.raise_for_status.return_value = None
            response.json.return_value = {"data": [{"b64_json": base64.b64encode(buffer.getvalue()).decode()}]}
            session = Mock()
            session.post.return_value = response
            result = models.generate_image("emerald editorial", Path(folder) / "image.png", session=session)
            self.assertTrue(result.exists())
            self.assertEqual(session.post.call_args.kwargs["json"]["model"], models.IMAGE_MODEL)

    def test_image_requires_free_confirmation(self):
        with patch.dict("os.environ", {"AGNES_API_KEY": "test", "AGNES_FREE_IMAGE_CONFIRMED": ""}):
            with self.assertRaisesRegex(RuntimeError, "confirm"):
                models.generate_image("scene", "x.png")

    def test_unknown_image_model_blocked(self):
        with self.assertRaisesRegex(RuntimeError, "allowlisted"):
            models.generate_image("x", "x.png", model="paid-model")

    def test_video_requires_explicit_free_confirmation(self):
        with patch.dict("os.environ", {"AGNES_API_KEY": "test", "AGNES_FREE_VIDEO_CONFIRMED": ""}):
            with self.assertRaisesRegex(RuntimeError, "confirm"):
                models.generate_video("scene", "x.mp4")

    def test_video_blocks_non_allowlisted_model(self):
        with patch.dict("os.environ", {"AGNES_API_KEY": "test", "AGNES_FREE_VIDEO_CONFIRMED": "yes"}):
            with self.assertRaisesRegex(RuntimeError, "allowlisted"):
                models.generate_video("scene", "x.mp4", model="agnes-video-2.5")

    def test_replicate_model_remains_disabled(self):
        self.assertFalse(models.THIRD_MODEL_ENABLED)
        self.assertEqual(models.THIRD_MODEL, "minimax/video-01")


if __name__ == "__main__":
    unittest.main()
