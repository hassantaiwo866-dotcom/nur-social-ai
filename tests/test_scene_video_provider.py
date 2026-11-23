import os
import unittest
from pathlib import Path
from unittest.mock import patch

import scene_video_provider


class AgnesSceneProviderTests(unittest.TestCase):
    def env(self, agnes="true", r2="true"):
        return patch.dict(os.environ, {
            "ENABLE_AGNES_VIDEO_GENERATION": agnes,
            "ENABLE_R2_TEMP_STORAGE": r2,
        })

    def test_disabled_when_agnes_switch_is_off(self):
        with self.env(agnes=""):
            with patch.object(scene_video_provider, "temporary_image_url") as upload:
                result = scene_video_provider.generate_agnes_scene_clip(
                    "scene.png", "prompt", "scene.mp4", 5.2
                )
                self.assertIsNone(result)
                upload.assert_not_called()

    def test_disabled_when_r2_switch_is_off(self):
        with self.env(r2=""):
            with patch.object(scene_video_provider, "temporary_image_url") as upload:
                result = scene_video_provider.generate_agnes_scene_clip(
                    "scene.png", "prompt", "scene.mp4", 5.2
                )
                self.assertIsNone(result)
                upload.assert_not_called()

    def test_holds_signed_url_context_until_agnes_returns(self):
        class URLContext:
            def __enter__(self):
                return "https://signed.example.test/image.png?token=secret"
            def __exit__(self, exc_type, exc, tb):
                events.append("cleanup")

        events = []
        with self.env(), patch.object(
            scene_video_provider, "temporary_image_url",
            side_effect=lambda path: URLContext()
        ) as upload, patch.object(
            scene_video_provider, "generate_agnes_video",
            side_effect=lambda *args, **kwargs: events.append("agnes") or Path("scene.mp4")
        ) as generate:
            result = scene_video_provider.generate_agnes_scene_clip(
                "scene.png", "cinematic prompt", "scene.mp4", 5.2
            )
        self.assertEqual(result, Path("scene.mp4"))
        self.assertEqual(events, ["agnes", "cleanup"])
        upload.assert_called_once_with("scene.png")
        self.assertEqual(generate.call_args.kwargs["seconds"], 6)
        self.assertEqual(generate.call_args.kwargs["aspect_ratio"], "9:16")
        self.assertEqual(
            generate.call_args.kwargs["reference_images"],
            ["https://signed.example.test/image.png?token=secret"],
        )

    def test_agnes_failure_returns_none_for_local_motion_fallback(self):
        class URLContext:
            def __enter__(self):
                return "https://signed.example.test/image.png?token=secret"
            def __exit__(self, exc_type, exc, tb):
                events.append("cleanup")

        events = []
        logs = []
        with self.env(), patch.object(
            scene_video_provider, "temporary_image_url", return_value=URLContext()
        ), patch.object(
            scene_video_provider, "generate_agnes_video", side_effect=RuntimeError("secret details")
        ):
            result = scene_video_provider.generate_agnes_scene_clip(
                "scene.png", "prompt", "scene.mp4", 20,
                logger=logs.append,
            )
        self.assertIsNone(result)
        self.assertEqual(events, ["cleanup"])
        self.assertEqual(logs, [
            "Agnes/R2 animation unavailable; using local still motion: RuntimeError"
        ])

    def test_duration_is_clamped_to_provider_limits(self):
        class URLContext:
            def __enter__(self): return "https://signed.example.test/image.png"
            def __exit__(self, *args): pass
        with self.env(), patch.object(
            scene_video_provider, "temporary_image_url", return_value=URLContext()
        ), patch.object(
            scene_video_provider, "generate_agnes_video", return_value=Path("clip.mp4")
        ) as generate:
            scene_video_provider.generate_agnes_scene_clip(
                "scene.png", "prompt", "clip.mp4", 30
            )
        self.assertEqual(generate.call_args.kwargs["seconds"], 12)


if __name__ == "__main__":
    unittest.main()
