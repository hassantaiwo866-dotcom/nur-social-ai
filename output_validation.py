"""Validate generated Nūr media files before packaging or review."""
from __future__ import annotations

import json
import math
import subprocess
from pathlib import Path
from PIL import Image


def _parse_rate(value: str) -> float:
    numerator, denominator = str(value or "0/1").split("/", 1)
    denominator = float(denominator)
    return float(numerator) / denominator if denominator else 0.0


def validate_media_outputs(image_path, video_path, runner=subprocess.run):
    image_path = Path(image_path)
    video_path = Path(video_path)
    failures = []

    if not image_path.is_file() or image_path.stat().st_size <= 0:
        failures.append("Editorial image is missing or empty.")
    else:
        try:
            with Image.open(image_path) as image:
                image.verify()
            with Image.open(image_path) as image:
                if image.size != (1080, 1350):
                    failures.append(f"Editorial image dimensions are {image.width}x{image.height}; expected 1080x1350.")
        except (OSError, ValueError) as exc:
            failures.append(f"Editorial image is invalid: {type(exc).__name__}.")

    metadata = {}
    if not video_path.is_file() or video_path.stat().st_size < 50_000:
        failures.append("Video is missing, empty, or unusually small.")
    else:
        try:
            result = runner(
                ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", str(video_path)],
                capture_output=True, text=True, check=False,
            )
            if result.returncode != 0:
                failures.append("ffprobe could not inspect the rendered video.")
            else:
                metadata = json.loads(result.stdout)
        except (OSError, json.JSONDecodeError, TypeError) as exc:
            failures.append(f"Video metadata could not be read: {type(exc).__name__}.")

    streams = metadata.get("streams", []) if isinstance(metadata, dict) else []
    video_streams = [stream for stream in streams if stream.get("codec_type") == "video"]
    audio_streams = [stream for stream in streams if stream.get("codec_type") == "audio"]

    video_info = {}
    if not video_streams:
        failures.append("Video has no readable video stream.")
    else:
        video_info = video_streams[0]
        width, height = video_info.get("width"), video_info.get("height")
        if (width, height) != (1080, 1920):
            failures.append(f"Video dimensions are {width}x{height}; expected 1080x1920.")
        try:
            fps = _parse_rate(video_info.get("avg_frame_rate"))
            if not math.isfinite(fps) or fps <= 0:
                failures.append("Video frame rate is invalid.")
        except (ValueError, TypeError, ZeroDivisionError):
            failures.append("Video frame rate is invalid.")

    if not audio_streams:
        failures.append("Video has no audio stream.")

    try:
        duration = float(metadata.get("format", {}).get("duration", 0))
        if not math.isfinite(duration) or not 12 <= duration <= 60:
            failures.append(f"Video duration is outside the expected 12–60 second range: {duration:.2f}s.")
    except (TypeError, ValueError, AttributeError):
        duration = 0.0
        failures.append("Video duration metadata is invalid.")

    if failures:
        raise RuntimeError("Media output validation failed:\\n- " + "\\n- ".join(failures))

    return {
        "status": "passed",
        "checks": [
            "Editorial image readable and 1080x1350",
            "Video metadata readable",
            "Video frame 1080x1920",
            "Video frame rate valid",
            "Video duration within 12–60 seconds",
            "Audio stream present",
        ],
        "metadata": {
            "image_width": 1080, "image_height": 1350,
            "video_width": video_info["width"], "video_height": video_info["height"],
            "video_codec": video_info.get("codec_name"),
            "audio_codec": audio_streams[0].get("codec_name"),
            "duration_seconds": round(duration, 3),
            "frame_rate": round(_parse_rate(video_info.get("avg_frame_rate")), 3),
            "video_size_bytes": video_path.stat().st_size,
            "image_size_bytes": image_path.stat().st_size,
        },
    }
