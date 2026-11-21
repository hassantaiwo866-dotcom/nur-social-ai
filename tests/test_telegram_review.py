import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

import telegram_review


class TelegramReviewTests(unittest.TestCase):
    def make_output(self, folder, qa_status="passed"):
        output = Path(folder)
        (output / "nur_post.png").write_bytes(b"fake image bytes")
        (output / "nur_reel.mp4").write_bytes(b"fake video bytes")
        (output / "latest_post.json").write_text(
            json.dumps({
                "image_caption": "Image caption",
                "video_caption": "Video caption",
                "qa": {"status": qa_status},
            }),
            encoding="utf-8",
        )
        return output

    def response(self, ok=True, description=""):
        result = Mock()
        result.raise_for_status.return_value = None
        result.json.return_value = {"ok": ok, "description": description}
        return result

    def test_missing_credentials_skip_review_delivery(self):
        with tempfile.TemporaryDirectory() as folder:
            self.make_output(folder)
            post = Mock()
            self.assertFalse(telegram_review.deliver_review(
                token="", chat_id="",
                output_dir=folder, request_post=post,
            ))
            post.assert_not_called()

    def test_sends_image_and_video_to_configured_chat(self):
        with tempfile.TemporaryDirectory() as folder:
            self.make_output(folder)
            post = Mock(return_value=self.response())
            self.assertTrue(telegram_review.deliver_review(
                token="test-token", chat_id="private-chat",
                output_dir=folder, request_post=post,
            ))
            self.assertEqual(post.call_count, 2)
            self.assertIn("/sendPhoto", post.call_args_list[0].args[0])
            self.assertIn("/sendVideo", post.call_args_list[1].args[0])
            self.assertEqual(post.call_args_list[0].kwargs["data"]["chat_id"], "private-chat")

    def test_qa_failure_blocks_review_delivery(self):
        with tempfile.TemporaryDirectory() as folder:
            self.make_output(folder, qa_status="failed")
            post = Mock()
            with self.assertRaisesRegex(RuntimeError, "QA"):
                telegram_review.deliver_review(
                    token="test-token", chat_id="private-chat",
                    output_dir=folder, request_post=post,
                )
            post.assert_not_called()

    def test_rejected_inline_video_falls_back_to_document(self):
        with tempfile.TemporaryDirectory() as folder:
            self.make_output(folder)
            post = Mock(side_effect=[
                self.response(),
                self.response(ok=False, description="video rejected"),
                self.response(),
            ])
            self.assertTrue(telegram_review.deliver_review(
                token="test-token", chat_id="private-chat",
                output_dir=folder, request_post=post,
            ))
            self.assertIn("/sendDocument", post.call_args_list[2].args[0])


if __name__ == "__main__":
    unittest.main()
