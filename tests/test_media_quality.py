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

    def test_scene_overlay_uses_primary_emerald_brand_rule(self):
        from media_quality import render_scene_overlay
        with tempfile.TemporaryDirectory() as folder:
            target = Path(folder) / "overlay.png"
            render_scene_overlay({"beat": "HOOK", "on_screen_text": "Pause before reacting."}, target)
            with Image.open(target) as image:
                self.assertEqual(image.getpixel((500, 151))[:3], (11, 93, 59))

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

    @patch("media_quality._duration", side_effect=[4.0, 5.0, 6.0])
    @patch("media_quality.subprocess.run")
    def test_video_assembly_uses_video_and_audio_crossfades(self, run, duration):
        from media_quality import join_video_segments
        run.return_value.returncode = 0
        with tempfile.TemporaryDirectory() as folder:
            paths = []
            for name in ("one.mp4", "two.mp4", "three.mp4"):
                path = Path(folder) / name
                path.write_bytes(b"placeholder")
                paths.append(path)
            output = Path(folder) / "joined.mp4"
            join_video_segments(paths, output, transitions=["wipeleft", "smoothright"])
        command = run.call_args.args[0]
        filter_graph = command[command.index("-filter_complex") + 1]
        self.assertEqual(filter_graph.count("xfade="), 2)
        self.assertIn("transition=wipeleft", filter_graph)
        self.assertIn("transition=smoothright", filter_graph)
        self.assertIn("concat=n=3:v=0:a=1", filter_graph)
        self.assertIn("loudnorm=I=-16:TP=-1.5:LRA=11", filter_graph)
        self.assertIn("offset=3.650", filter_graph)

    def test_motion_accent_filter_is_emerald_and_time_limited(self):
        from media_quality import motion_accent_filter
        filter_a = motion_accent_filter(0, 5, "cinematic_documentary")
        filter_b = motion_accent_filter(1, 5, "tactile_editorial_collage")
        self.assertIn("0B5D3B", filter_a)
        self.assertIn("between(t", filter_a)
        self.assertIn("y=1435", filter_b)
        self.assertNotEqual(filter_a, filter_b)

    def test_voice_audio_filter_has_polish_and_fades(self):
        from media_quality import voice_audio_filter
        filters = voice_audio_filter(5.0)
        self.assertIn("highpass=f=75", filters)
        self.assertIn("acompressor=", filters)
        self.assertIn("loudnorm=I=-16", filters)
        self.assertIn("afade=t=in", filters)
        self.assertIn("afade=t=out:st=4.840", filters)

    @patch("media_quality.subprocess.run")
    def test_stock_clip_vertical_reframe_preserves_full_shot(self, run):
        from media_quality import render_scene_overlay
        from pathlib import Path
        from PIL import Image
        import tempfile
        run.return_value.returncode = 0
        with tempfile.TemporaryDirectory() as folder:
            overlay = Path(folder) / "overlay.png"
            render_scene_overlay(
                {"beat": "THE PAUSE", "on_screen_text": "Notice the moment."},
                overlay,
            )
            with Image.open(overlay) as image:
                self.assertEqual(image.size, (1080, 1920))
                self.assertEqual(image.mode, "RGBA")
            generator_path = Path(folder) / "clip.mp4"
            audio = Path(folder) / "voice.mp3"
            output = Path(folder) / "output.mp4"
            generator_path.write_bytes(b"clip")
            audio.write_bytes(b"audio")
            import nur_generator
            nur_generator.make_video_segment_from_clip(
                generator_path, overlay, audio, output, 4.0
            )
        command = run.call_args.args[0]
        graph = command[command.index("-filter_complex") + 1]
        self.assertIn("boxblur", graph)
        self.assertIn("force_original_aspect_ratio=decrease", graph)
        self.assertIn("overlay=(W-w)/2:(H-h)/2", graph)


if __name__ == "__main__":
    unittest.main()

    def test_collage_style_adds_tactile_paper_caption(self):
        from media_quality import render_scene_frame, render_scene_overlay
        with tempfile.TemporaryDirectory() as folder:
            source = Path(folder) / "source.jpg"
            frame = Path(folder) / "collage.jpg"
            overlay = Path(folder) / "collage.png"
            Image.new("RGB", (720, 1280), (80, 100, 90)).save(source)
            scene = {"beat": "RE-HOOK", "on_screen_text": "A different response is possible."}
            render_scene_frame(source, scene, frame, 2, "tactile_editorial_collage")
            render_scene_overlay(scene, overlay, 2, "hybrid_documentary_collage")
            with Image.open(frame) as image:
                self.assertEqual(image.size, (1080, 1920))
            with Image.open(overlay) as image:
                self.assertEqual(image.mode, "RGBA")
                self.assertEqual(image.size, (1080, 1920))
