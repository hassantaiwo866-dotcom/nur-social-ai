import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch

import agnes_video


class AgnesVideoTests(unittest.TestCase):
    def setUp(self):
        agnes_video.reset_usage_for_tests()

    def env(self):
        return patch.dict(os.environ, {
            "ENABLE_AGNES_VIDEO_GENERATION": "true",
            "AGNES_VIDEO_FREE_PRICE_CONFIRMED": "yes",
            "AGNES_API_KEY": "test-secret",
            "AGNES_BASE_URL": "https://apihub.agnes-ai.com/v1",
        })

    def responses(self):
        created = Mock()
        created.raise_for_status.return_value = None
        created.json.return_value = {"video_id": "video-test"}
        polled = Mock()
        polled.status_code = 200
        polled.raise_for_status.return_value = None
        polled.json.return_value = {
            "status": "completed",
            "url": "https://cdn.example.test/video.mp4",
        }
        download = Mock()
        download.raise_for_status.return_value = None
        download.content = b"0000ftyp" + (b"\x00" * 2048)
        return created, polled, download

    def test_creates_flash_720p_video_and_polls_with_model_name(self):
        with tempfile.TemporaryDirectory() as folder, self.env():
            session = Mock()
            created, polled, download = self.responses()
            session.post.return_value = created
            session.get.side_effect = [polled, download]
            with patch("agnes_video.time.sleep"):
                path = agnes_video.generate_video(
                    "A cinematic scene", Path(folder) / "scene.mp4",
                    session=session,
                )
            self.assertTrue(path.exists())
            payload = session.post.call_args.kwargs["json"]
            self.assertEqual(payload["model"], "agnes-video-2.5-flash")
            self.assertEqual(payload["size"], "720P")
            self.assertEqual(payload["seconds"], "4")
            self.assertEqual(payload["aspect_ratio"], "9:16")
            self.assertEqual(
                session.get.call_args_list[0].kwargs["params"],
                {"video_id": "video-test", "model_name": "agnes-video-2.5-flash"},
            )

    def test_reference_images_use_reference_mode(self):
        with tempfile.TemporaryDirectory() as folder, self.env():
            session = Mock()
            created, polled, download = self.responses()
            session.post.return_value = created
            session.get.side_effect = [polled, download]
            with patch("agnes_video.time.sleep"):
                agnes_video.generate_video(
                    "Animate the person naturally",
                    Path(folder) / "reference.mp4",
                    reference_images=["https://assets.example.test/portrait.png"],
                    session=session,
                )
            payload = session.post.call_args.kwargs["json"]
            self.assertEqual(payload["mode"], "reference")
            self.assertEqual(payload["images"], ["https://assets.example.test/portrait.png"])
            self.assertIn("<Picture 1>", payload["prompt"])

    def test_rejects_non_https_reference_before_request(self):
        with self.env():
            session = Mock()
            with self.assertRaisesRegex(ValueError, "public HTTPS"):
                agnes_video.generate_video(
                    "Animate this", "unused.mp4",
                    reference_images=["http://example.test/image.png"],
                    session=session,
                )
            session.post.assert_not_called()

    def test_rejects_more_than_five_reference_images(self):
        with self.env():
            session = Mock()
            refs = [f"https://assets.example.test/{index}.png" for index in range(6)]
            with self.assertRaisesRegex(ValueError, "at most five"):
                agnes_video.generate_video(
                    "Animate these", "unused.mp4",
                    reference_images=refs, session=session,
                )
            session.post.assert_not_called()

    def test_disabled_by_default_sends_no_request(self):
        with patch.dict(os.environ, {
            "ENABLE_AGNES_VIDEO_GENERATION": "",
            "AGNES_VIDEO_FREE_PRICE_CONFIRMED": "yes",
            "AGNES_API_KEY": "test-secret",
        }):
            session = Mock()
            with self.assertRaisesRegex(RuntimeError, "disabled"):
                agnes_video.generate_video("scene", "unused.mp4", session=session)
            session.post.assert_not_called()

    def test_requires_explicit_free_price_confirmation(self):
        with patch.dict(os.environ, {
            "ENABLE_AGNES_VIDEO_GENERATION": "true",
            "AGNES_VIDEO_FREE_PRICE_CONFIRMED": "",
            "AGNES_API_KEY": "test-secret",
        }):
            session = Mock()
            with self.assertRaisesRegex(RuntimeError, "Confirm the current"):
                agnes_video.generate_video("scene", "unused.mp4", session=session)
            session.post.assert_not_called()

    def test_requires_api_key(self):
        with patch.dict(os.environ, {
            "ENABLE_AGNES_VIDEO_GENERATION": "true",
            "AGNES_VIDEO_FREE_PRICE_CONFIRMED": "yes",
            "AGNES_API_KEY": "",
        }):
            with self.assertRaisesRegex(RuntimeError, "AGNES_API_KEY"):
                agnes_video.generate_video("scene", "unused.mp4")

    def test_rejects_invalid_duration_before_request(self):
        with self.env():
            session = Mock()
            with self.assertRaisesRegex(ValueError, "between 4 and 12"):
                agnes_video.generate_video("scene", "unused.mp4", seconds=13, session=session)
            session.post.assert_not_called()

    def test_hard_cap_blocks_second_video(self):
        with tempfile.TemporaryDirectory() as folder, self.env():
            session = Mock()
            created, polled, download = self.responses()
            session.post.return_value = created
            session.get.side_effect = [polled, download]
            with patch("agnes_video.time.sleep"):
                agnes_video.generate_video("first", Path(folder) / "first.mp4", session=session)
            with self.assertRaisesRegex(RuntimeError, "cap reached"):
                agnes_video.generate_video("second", Path(folder) / "second.mp4", session=session)
            self.assertEqual(session.post.call_count, 1)

    def test_failed_task_does_not_download_video(self):
        with self.env():
            session = Mock()
            created, polled, _ = self.responses()
            polled.json.return_value = {"status": "failed"}
            session.post.return_value = created
            session.get.return_value = polled
            with self.assertRaisesRegex(RuntimeError, "task failed"):
                agnes_video.generate_video("scene", "unused.mp4", session=session)
            self.assertEqual(session.get.call_count, 1)

    def test_rejects_non_mp4_download(self):
        with self.env():
            session = Mock()
            created, polled, download = self.responses()
            download.content = b"not an mp4 file" * 100
            session.post.return_value = created
            session.get.side_effect = [polled, download]
            with self.assertRaisesRegex(RuntimeError, "invalid"):
                agnes_video.generate_video("scene", "unused.mp4", session=session)


if __name__ == "__main__":
    unittest.main()
