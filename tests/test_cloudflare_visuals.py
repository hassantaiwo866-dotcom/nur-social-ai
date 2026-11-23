import base64
import io
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch
from PIL import Image
import cloudflare_visuals as visuals

class CloudflareVisualTests(unittest.TestCase):
    def setUp(self):
        visuals.reset_usage_for_tests()

    def _image_response(self):
        buffer = io.BytesIO()
        Image.new("RGB", (768, 768), "#0B5D3B").save(buffer, "PNG")
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {"image": base64.b64encode(buffer.getvalue()).decode("ascii")}
        return response

    def _env(self):
        return patch.dict(os.environ, {
            "ENABLE_CLOUDFLARE_IMAGE_GENERATION": "true",
            "CLOUDFLARE_FREE_PLAN_CONFIRMED": "yes",
            "CLOUDFLARE_ACCOUNT_ID": "account-test",
            "CLOUDFLARE_API_TOKEN": "token-test",
        })

    def test_generates_valid_image_using_allowlisted_model(self):
        with tempfile.TemporaryDirectory() as folder, self._env():
            session = Mock()
            session.post.return_value = self._image_response()
            path = visuals.generate_image("cinematic emerald scene", Path(folder) / "image.png", session=session)
            self.assertTrue(path.exists())
            self.assertEqual(session.post.call_args.args[0], f"{visuals.API_ROOT}/account-test/ai/run/{visuals.MODEL}")
            self.assertEqual(session.post.call_args.kwargs["json"]["steps"], 4)

    def test_requires_explicit_free_plan_confirmation(self):
        with patch.dict(os.environ, {"ENABLE_CLOUDFLARE_IMAGE_GENERATION":"true", "CLOUDFLARE_FREE_PLAN_CONFIRMED":"", "CLOUDFLARE_ACCOUNT_ID":"account", "CLOUDFLARE_API_TOKEN":"token"}):
            with self.assertRaisesRegex(RuntimeError, "Workers Free"):
                visuals.generate_image("scene", "unused.png")

    def test_disabled_by_default(self):
        with patch.dict(os.environ, {"ENABLE_CLOUDFLARE_IMAGE_GENERATION":"", "CLOUDFLARE_FREE_PLAN_CONFIRMED":"yes", "CLOUDFLARE_ACCOUNT_ID":"account", "CLOUDFLARE_API_TOKEN":"token"}):
            with self.assertRaisesRegex(RuntimeError, "disabled"):
                visuals.generate_image("scene", "unused.png")

    def test_hard_cap_blocks_sixth_request(self):
        with tempfile.TemporaryDirectory() as folder, self._env():
            session = Mock()
            session.post.return_value = self._image_response()
            for index in range(5):
                visuals.generate_image("scene", Path(folder) / f"{index}.png", session=session)
            with self.assertRaisesRegex(RuntimeError, "cap reached"):
                visuals.generate_image("sixth", Path(folder) / "sixth.png", session=session)
            self.assertEqual(session.post.call_count, 5)

    def test_invalid_image_is_removed(self):
        with tempfile.TemporaryDirectory() as folder, self._env():
            session = Mock()
            response = Mock()
            response.raise_for_status.return_value = None
            response.json.return_value = {"image": base64.b64encode(b"not-an-image").decode("ascii")}
            session.post.return_value = response
            target = Path(folder) / "bad.png"
            with self.assertRaisesRegex(RuntimeError, "failed validation"):
                visuals.generate_image("scene", target, session=session)
            self.assertFalse(target.exists())

    def test_model_steps_are_bounded(self):
        with self._env():
            with self.assertRaisesRegex(ValueError, "between 1 and 4"):
                visuals.generate_image("scene", "unused.png", steps=8)



    def test_klein_uses_multipart_model_endpoint_and_dimensions(self):
        with tempfile.TemporaryDirectory() as folder, self._env():
            session = Mock()
            session.post.return_value = self._image_response()
            path = visuals.generate_klein_image(
                "cinematic portrait scene", Path(folder) / "klein.png",
                width=768, height=1280, session=session,
            )
            self.assertTrue(path.exists())
            args = session.post.call_args
            self.assertTrue(args.args[0].endswith(visuals.KLEIN_MODEL))
            self.assertEqual(args.kwargs["data"], {"width": "768", "height": "1280"})
            self.assertEqual(args.kwargs["files"][0][0], "prompt")
            self.assertEqual(args.kwargs["files"][0][1][1], "cinematic portrait scene")
            self.assertNotIn("Content-Type", args.kwargs["headers"])

    def test_klein_requires_free_plan_confirmation(self):
        with patch.dict(os.environ, {
            "ENABLE_CLOUDFLARE_IMAGE_GENERATION": "true",
            "CLOUDFLARE_FREE_PLAN_CONFIRMED": "",
            "CLOUDFLARE_ACCOUNT_ID": "account",
            "CLOUDFLARE_API_TOKEN": "token",
        }):
            with self.assertRaisesRegex(RuntimeError, "Workers Free"):
                visuals.generate_klein_image("scene", "unused.png")

    def test_klein_reference_images_must_be_under_512_pixels(self):
        with tempfile.TemporaryDirectory() as folder, self._env():
            reference = Path(folder) / "reference.png"
            Image.new("RGB", (512, 256)).save(reference)
            session = Mock()
            with self.assertRaisesRegex(ValueError, "smaller than 512x512"):
                visuals.generate_klein_image(
                    "use reference", Path(folder) / "out.png",
                    reference_images=[reference], session=session,
                )
            session.post.assert_not_called()

    def test_klein_rejects_more_than_four_references(self):
        with self._env():
            with self.assertRaisesRegex(ValueError, "at most four"):
                visuals.generate_klein_image(
                    "scene", "unused.png",
                    reference_images=["a", "b", "c", "d", "e"],
                )

    def test_klein_does_not_send_request_when_disabled(self):
        with patch.dict(os.environ, {
            "ENABLE_CLOUDFLARE_IMAGE_GENERATION": "",
            "CLOUDFLARE_FREE_PLAN_CONFIRMED": "yes",
            "CLOUDFLARE_ACCOUNT_ID": "account",
            "CLOUDFLARE_API_TOKEN": "token",
        }):
            session = Mock()
            with self.assertRaisesRegex(RuntimeError, "disabled"):
                visuals.generate_klein_image("scene", "unused.png", session=session)
            session.post.assert_not_called()

if __name__ == "__main__":
    unittest.main()

if __name__ == "__main__":
    unittest.main()
