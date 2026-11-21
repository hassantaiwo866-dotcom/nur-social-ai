"""Free-tier visual model adapters for Nūr Social AI.

Paid providers are intentionally not included in this adapter. Video free access
is promotional and requires a user-confirmed zero-cost account setting before
the API is called. This is not a guarantee from the provider that promotions
will remain available.
"""
from __future__ import annotations

import base64
import os
import time
from pathlib import Path

import requests
from PIL import Image

BASE = "https://apihub.agnes-ai.com"
IMAGE_MODEL = "agnes-image-2.5-flash"
VIDEO_MODEL = "agnes-video-2.5-flash"
# Third planned model is not integrated because Replicate trial usage is not
# guaranteed free. Never call it from this free-only production pipeline.
THIRD_MODEL = "minimax/video-01"
THIRD_MODEL_ENABLED = False


def free_only_enabled() -> bool:
    return os.getenv("NUR_FREE_ONLY", "true").strip().lower() not in ("0", "false", "no")


def _key() -> str:
    key = os.getenv("AGNES_API_KEY", "").strip()
    if not key:
        raise RuntimeError("AGNES_API_KEY is not configured.")
    return key


def _assert_free_image(model: str) -> None:
    if os.getenv("AGNES_FREE_IMAGE_CONFIRMED", "").strip().lower() != "yes":
        raise RuntimeError("Image API blocked: confirm the model is currently $0 in your Agnes account, then set AGNES_FREE_IMAGE_CONFIRMED=yes.")
    if not free_only_enabled():
        raise RuntimeError("Free-only policy disabled; this adapter is not a paid-provider adapter.")
    if model != IMAGE_MODEL:
        raise RuntimeError("Model not allowlisted under Nūr's free-only policy.")


def _assert_free_video(model: str) -> None:
    if not free_only_enabled():
        raise RuntimeError("Free-only policy disabled; this adapter is not a paid-provider adapter.")
    if model != VIDEO_MODEL:
        raise RuntimeError("Paid or unknown video model blocked by free-only policy.")
    if os.getenv("AGNES_FREE_VIDEO_CONFIRMED", "").strip().lower() != "yes":
        raise RuntimeError(
            "Video API blocked: confirm the model is currently $0 in your Agnes account, "
            "then set AGNES_FREE_VIDEO_CONFIRMED=yes."
        )


def generate_image(prompt: str, destination: str | Path, *,
                   model: str = IMAGE_MODEL, session=requests) -> Path:
    """Generate one 1K portrait image; only allowlisted model can be requested."""
    _assert_free_image(model)
    response = session.post(
        f"{BASE}/v1/images/generations",
        headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"},
        json={"model": model, "prompt": prompt, "size": "1K", "ratio": "9:16",
              "extra_body": {"response_format": "b64_json"}},
        timeout=120,
    )
    response.raise_for_status()
    data = response.json().get("data", [])
    if not data:
        raise RuntimeError("Agnes image response contained no data.")
    item = data[0]
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    if item.get("b64_json"):
        path.write_bytes(base64.b64decode(item["b64_json"], validate=True))
    elif item.get("url"):
        download = session.get(item["url"], timeout=90)
        download.raise_for_status()
        path.write_bytes(download.content)
    else:
        raise RuntimeError("Agnes image response had neither b64_json nor URL.")
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            if image.width < 512 or image.height < 512:
                raise RuntimeError("Generated image is below minimum resolution.")
    except Exception as exc:
        path.unlink(missing_ok=True)
        raise RuntimeError("Agnes image failed validation.") from exc
    return path


def generate_video(prompt: str, destination: str | Path, *,
                   seconds: int = 4, model: str = VIDEO_MODEL,
                   session=requests, poll_interval: float = 10,
                   max_wait: float = 360) -> Path:
    """Generate a short 720P clip, polling only within a bounded timeout."""
    _assert_free_video(model)
    if seconds < 4 or seconds > 12:
        raise ValueError("Agnes video duration must be 4–12 seconds.")
    response = session.post(
        f"{BASE}/v1/videos",
        headers={"Authorization": f"Bearer {_key()}", "Content-Type": "application/json"},
        json={"model": model, "prompt": prompt, "mode": "text", "seconds": str(seconds),
              "size": "720P", "aspect_ratio": "9:16", "n": 1},
        timeout=90,
    )
    response.raise_for_status()
    payload = response.json()
    video_id = payload.get("video_id") or payload.get("id") or payload.get("task_id")
    if not video_id:
        raise RuntimeError("Agnes video response did not provide a task/video ID.")
    deadline = time.monotonic() + max_wait
    result = None
    while time.monotonic() < deadline:
        poll = session.get(
            f"{BASE}/agnesapi",
            params={"video_id": video_id, "model_name": model},
            headers={"Authorization": f"Bearer {_key()}"},
            timeout=60,
        )
        poll.raise_for_status()
        result = poll.json()
        status = str(result.get("status", "")).lower()
        if status in ("completed", "success", "succeeded"):
            break
        if status in ("failed", "error", "cancelled"):
            raise RuntimeError(f"Agnes video task failed: {result.get('error', status)}")
        time.sleep(max(1, poll_interval))
    else:
        raise TimeoutError("Agnes video generation exceeded the configured wait limit.")
    url = result.get("url") or result.get("video_url")
    if not url:
        raise RuntimeError("Completed Agnes video response contained no download URL.")
    download = session.get(url, timeout=180)
    download.raise_for_status()
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(download.content)
    if path.stat().st_size < 100_000:
        path.unlink(missing_ok=True)
        raise RuntimeError("Generated video file is unexpectedly small.")
    return path
