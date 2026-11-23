import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock

from PIL import Image

from output_validation import validate_media_outputs


def payload(width=1080, height=1920, duration="25.0", fps="24/1", audio=True):
    streams = [{
        "codec_type": "video",
        "codec_name": "h264",
        "width": width,
        "height": height,
        "avg_frame_rate": fps,
    }]
    if audio:
        streams.append({"codec_type": "audio", "codec_name": "aac"})
    return {"streams": streams, "format": {"duration": duration}}


class OutputValidationTests(unittest.TestCase):
    def make_image(self, folder, size=(1080, 1350)):
        path = Path(folder) / "poster.png"
        Image.new("RGB", size, "white").save(path)
        return path

    def make_video(self, folder):
        path = Path(folder) / "reel.mp4"
        path.write_bytes(b"x" * 60000)
        return path

    def runner(self, data):
        runner = Mock()
        runner.return_value.returncode = 0
        runner.return_value.stdout = json.dumps(data)
        runner.return_value.stderr = ""
        return runner

    def test_valid_outputs_pass_and_metadata_is_returned(self):
        with tempfile.TemporaryDirectory() as folder:
            result = validate_media_outputs(
                self.make_image(folder), self.make_video(folder),
                self.runner(payload()),
            )
            self.assertEqual(result["status"], "passed")
            self.assertEqual(result["metadata"]["video_width"], 1080)
            self.assertEqual(result["metadata"]["duration_seconds"], 25.0)
            self.assertEqual(result["metadata"]["audio_codec"], "aac")

    def test_wrong_image_dimensions_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(RuntimeError, "1080x1350"):
                validate_media_outputs(
                    self.make_image(folder, (720, 1280)), self.make_video(folder),
                    self.runner(payload()),
                )

    def test_wrong_video_dimensions_fail(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(RuntimeError, "720x1280"):
                validate_media_outputs(
                    self.make_image(folder), self.make_video(folder),
                    self.runner(payload(720, 1280)),
                )

    def test_missing_audio_stream_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(RuntimeError, "no audio stream"):
                validate_media_outputs(
                    self.make_image(folder), self.make_video(folder),
                    self.runner(payload(audio=False)),
                )

    def test_duration_outside_range_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(RuntimeError, "duration"):
                validate_media_outputs(
                    self.make_image(folder), self.make_video(folder),
                    self.runner(payload(duration="8")),
                )

    def test_invalid_ffprobe_json_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            runner = self.runner({})
            runner.return_value.stdout = "not-json"
            with self.assertRaisesRegex(RuntimeError, "metadata"):
                validate_media_outputs(
                    self.make_image(folder), self.make_video(folder), runner,
                )

    def test_missing_video_file_fails_without_probe(self):
        with tempfile.TemporaryDirectory() as folder:
            runner = Mock()
            with self.assertRaisesRegex(RuntimeError, "missing"):
                validate_media_outputs(
                    self.make_image(folder), Path(folder) / "absent.mp4", runner,
                )
            runner.assert_not_called()

    def test_invalid_frame_rate_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesRegex(RuntimeError, "frame rate"):
                validate_media_outputs(
                    self.make_image(folder), self.make_video(folder),
                    self.runner(payload(fps="0/0")),
                )

    def test_ffprobe_nonzero_exit_fails(self):
        with tempfile.TemporaryDirectory() as folder:
            runner = self.runner(payload())
            runner.return_value.returncode = 1
            with self.assertRaisesRegex(RuntimeError, "ffprobe"):
                validate_media_outputs(
                    self.make_image(folder), self.make_video(folder), runner,
                )


if __name__ == "__main__":
    unittest.main()
