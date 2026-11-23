"""Optional Agnes scene animation using an inline Base64 first frame."""
from __future__ import annotations

import base64
import math
import mimetypes
import os
from pathlib import Path

from agnes_video import generate_video as generate_agnes_video

ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}
MAX_IMAGE_BYTES = 10 * 1024 * 1024


def generate_agnes_scene_clip(
    image_path: str | Path,
    prompt: str,
    destination: str | Path,
    narration_duration: float,
    *,
    logger=print,
):
    """Animate a local generated still; return None for safe local-motion fallback."""
    enabled = os.getenv("ENABLE_AGNES_VIDEO_GENERATION", "").strip().lower() in {
        "1", "true", "yes"
    }
    if not enabled:
        return None

    seconds = min(12, max(4, math.ceil(float(narration_duration))))
    try:
        path = Path(image_path)
        if not path.is_file():
            raise FileNotFoundError("Generated scene image does not exist.")
        if path.stat().st_size <= 0 or path.stat().st_size > MAX_IMAGE_BYTES:
            raise ValueError("Image must be between 1 byte and 10 MiB.")
        content_type, _ = mimetypes.guess_type(path.name)
        if content_type not in ALLOWED_IMAGE_TYPES:
            raise ValueError("Only PNG, JPEG and WebP images are accepted.")
        first_frame = base64.b64encode(path.read_bytes()).decode("ascii")
        return generate_agnes_video(
            prompt,
            destination,
            seconds=seconds,
            aspect_ratio="9:16",
            first_frame_base64=first_frame,
        )
    except Exception as exc:
        logger(
            "Agnes inline-image animation unavailable; using local still motion: "
            f"{type(exc).__name__}"
        )
        return None
