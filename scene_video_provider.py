"""Optional Agnes scene animation through private temporary R2 references."""
from __future__ import annotations

import math
import os
from pathlib import Path

from agnes_video import generate_video as generate_agnes_video
from r2_temp_storage import temporary_image_url


def generate_agnes_scene_clip(
    image_path: str | Path,
    prompt: str,
    destination: str | Path,
    narration_duration: float,
    *,
    logger=print,
):
    """Animate a generated still; return None for safe local-motion fallback."""
    enabled = os.getenv("ENABLE_AGNES_VIDEO_GENERATION", "").strip().lower() in {
        "1", "true", "yes"
    }
    storage_enabled = os.getenv("ENABLE_R2_TEMP_STORAGE", "").strip().lower() in {
        "1", "true", "yes"
    }
    if not (enabled and storage_enabled):
        return None

    seconds = min(12, max(4, math.ceil(float(narration_duration))))
    try:
        with temporary_image_url(image_path) as reference_url:
            return generate_agnes_video(
                prompt,
                destination,
                seconds=seconds,
                aspect_ratio="9:16",
                reference_images=[reference_url],
            )
    except Exception as exc:
        # Never log the signed URL, API key, or provider response body.
        logger(
            "Agnes/R2 animation unavailable; using local still motion: "
            f"{type(exc).__name__}"
        )
        return None
