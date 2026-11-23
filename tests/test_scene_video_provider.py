import base64
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import scene_video_provider


class AgnesSceneProviderTests(unittest.TestCase):
    def env(self, agnes="true"):
        return patch.dict(os.environ, {"ENABLE_AGNES_VIDEO_GENERATION": agnes})

    def test_disabled_without_agnes_flag(self):
        with self.env(agnes=""):
            with patch.object(scene_video_provider, "generate_agnes_video") as generate:
                result = scene_video_provider.generate_agnes_scene_clip(
                    "scene.png", "prompt", "scene.mp4", 5.2
                )
                self.assertIsNone(result)
                generate.assert_not_called()

    def test_encodes_local_image_as_base64_and_calls_agnes(self):
        with tempfile.TemporaryDirectory() as folder, self.env():
            path = Path(folder) / "scene.png"
            raw = b"png-data-test"
            path.write_bytes(raw)
            with patch.object(scene_video_provider, "generate_agnes_video", return_value=Path("scene.mp4")) as generate:
                result = scene_video_provider.generate_agnes_scene_clip(
                    path, "cinematic prompt", "scene.mp4", 5.2
                )
            self.assertEqual(result, Path("scene.mp4"))
            self.assertEqual(generate.call_args.kwargs["first_frame_base64"], base64.b64encode(raw).decode("ascii"))
            self.assertEqual(generate.call_args.kwargs["seconds"], 6)
            self.assertEqual(generate.call_args.kwargs["aspect_ratio"], "9:16")

    def test_rejects_oversized_image_without_provider_call(self):
        with tempfile.TemporaryDirectory() as folder, self.env():
            path = Path(folder) / "scene.png"
            path.write_bytes(b"x" * (10 * 1024 * 1024 + 1))
            with patch.object(scene_video_provider, "generate_agnes_video") as generate:
                self.assertIsNone(scene_video_provider.generate_agnes_scene_clip(path, "prompt", "clip.mp4", 5))
                generate.assert_not_called()

    def test_agnes_failure_returns_none_for_local_motion_fallback(self):
        with tempfile.TemporaryDirectory() as folder, self.env():
            path = Path(folder) / "scene.png"
            path.write_bytes(b"image")
            logs = []
            with patch.object(scene_video_provider, "generate_agnes_video", side_effect=RuntimeError("secret details")):
                result = scene_video_provider.generate_agnes_scene_clip(path, "prompt", "scene.mp4", 20, logger=logs.append)
            self.assertIsNone(result)
            self.assertEqual(logs, ["Agnes inline-image animation unavailable; using local still motion: RuntimeError"])

    def test_duration_is_clamped_to_provider_limits(self):
        with tempfile.TemporaryDirectory() as folder, self.env():
            path = Path(folder) / "scene.png"
            path.write_bytes(b"image")
            with patch.object(scene_video_provider, "generate_agnes_video", return_value=Path("clip.mp4")) as generate:
                scene_video_provider.generate_agnes_scene_clip(path, "prompt", "clip.mp4", 30)
            self.assertEqual(generate.call_args.kwargs["seconds"], 12)


if __name__ == "__main__":
    unittest.main()
