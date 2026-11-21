import base64
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

from PIL import Image
import visual_providers as providers


class VisualProviderTests(unittest.TestCase):
    def test_gemini_image_is_saved_and_attributed(self):
        with tempfile.TemporaryDirectory() as folder:
            image_path = Path(folder) / "generated.png"
            import io
            buffer = io.BytesIO()
            Image.new("RGB", (1024, 1024), "#345678").save(buffer, "PNG")
            response = Mock()
            response.raise_for_status.return_value = None
            response.json.return_value = {"candidates": [{"content": {"parts": [
                {"inlineData": {"mimeType": "image/png",
                                "data": base64.b64encode(buffer.getvalue()).decode()}}
            ]}}]}
            session = Mock()
            session.post.return_value = response
            registry = []
            result = providers.generate_gemini_image(
                "Person reading by a window", image_path, 720, 1280,
                api_key="test-key", session=session, registry=registry,
            )
            self.assertTrue(result.exists())
            self.assertEqual(registry[0]["media_type"], "ai_generated_image")
            self.assertEqual(registry[0]["provider"], "Google Gemini")

    def test_gemini_requires_key(self):
        with patch.dict("os.environ", {"GEMINI_API_KEY": ""}):
            with self.assertRaisesRegex(RuntimeError, "GEMINI_API_KEY"):
                providers.generate_gemini_image("scene", "x.jpg", 720, 1280)

    def test_pixabay_requires_key(self):
        with patch.dict("os.environ", {"PIXABAY_API_KEY": ""}):
            with self.assertRaisesRegex(RuntimeError, "PIXABAY_API_KEY"):
                providers.search_pixabay_video("walking outdoors", "x.mp4")

    def test_pixabay_photo_uses_high_resolution_and_records_source(self):
        with tempfile.TemporaryDirectory() as folder:
            import io
            buffer = io.BytesIO()
            Image.new("RGB", (1600, 1200), "#456789").save(buffer, "JPEG")
            search = Mock()
            search.raise_for_status.return_value = None
            search.json.return_value = {"hits": [{
                "id": 12, "largeImageURL": "https://cdn.example/photo.jpg",
                "imageWidth": 1600, "imageHeight": 1200,
                "user": "creator", "pageURL": "https://pixabay.com/photos/12/",
                "tags": "calm room",
            }]}
            download = Mock()
            download.raise_for_status.return_value = None
            download.content = buffer.getvalue()
            session = Mock()
            session.get.side_effect = [search, download]
            registry = []
            result = providers.search_pixabay_photo(
                "calm room", Path(folder) / "photo.jpg", 720, 1280,
                api_key="test-key", session=session, registry=registry,
            )
            self.assertTrue(result.exists())
            self.assertEqual(registry[0]["asset_id"], 12)
            self.assertEqual(registry[0]["license"], "Pixabay Content License")


if __name__ == "__main__":
    unittest.main()
