"""Free-promotion-gated Agnes Video 2.5 Flash adapter.

No request is sent unless generation is explicitly enabled and the operator
has confirmed the current $0/sec promotion in the authenticated Agnes console.
This adapter never selects the paid Agnes Video 2.5 model or falls back to it.
"""
from __future__ import annotations

import os
import time
from pathlib import Path
from urllib.parse import urlparse

import requests

MODEL = "agnes-video-2.5-flash"
DEFAULT_BASE_URL = "https://apihub.agnes-ai.com/v1"
DEFAULT_SECONDS = 4
MAX_SECONDS = 12
MAX_VIDEOS_PER_PROCESS = 1
_videos_generated = 0


def _settings() -> tuple[str, str, str]:
    enabled = os.getenv("ENABLE_AGNES_VIDEO_GENERATION", "").strip().lower()
    if enabled not in ("1", "true", "yes"):
        raise RuntimeError("Agnes video generation is disabled.")
    confirmed = os.getenv("AGNES_VIDEO_FREE_PRICE_CONFIRMED", "").strip().lower()
    if confirmed != "yes":
        raise RuntimeError(
            "Confirm the current Agnes Video 2.5 Flash $0 price in the platform console."
        )
    key = os.getenv("AGNES_API_KEY", "").strip()
    if not key:
        raise RuntimeError("AGNES_API_KEY is not configured.")
    base_url = os.getenv("AGNES_BASE_URL", DEFAULT_BASE_URL).strip().rstrip("/")
    if not base_url.startswith("https://"):
        raise ValueError("Agnes API base URL must use HTTPS.")
    if not base_url.endswith("/v1"):
        raise ValueError("Agnes API base URL must end in /v1.")
    return key, base_url, base_url[:-3]


def generate_video(
    prompt: str,
    destination: str | Path,
    *,
    seconds: int = DEFAULT_SECONDS,
    aspect_ratio: str = "9:16",
    session=requests,
    poll_interval: float = 5,
    max_polls: int = 36,
) -> Path:
    """Create and download one 720P Flash video; never submits a paid model."""
    global _videos_generated
    if _videos_generated >= MAX_VIDEOS_PER_PROCESS:
        raise RuntimeError("Agnes per-process video cap reached (1).")
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("Video prompt must not be empty.")
    if not isinstance(seconds, int) or not 4 <= seconds <= MAX_SECONDS:
        raise ValueError("Agnes Flash duration must be between 4 and 12 seconds.")
    if aspect_ratio not in {"9:16", "16:9", "1:1", "4:3", "3:4", "21:9"}:
        raise ValueError("Unsupported Agnes video aspect ratio.")
    if poll_interval < 1 or max_polls < 1 or max_polls > 60:
        raise ValueError("Polling must use an interval >=1s and 1–60 attempts.")

    key, base_url, host_root = _settings()
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": MODEL,
        "prompt": prompt.strip()[:2000],
        "mode": "text",
        "seconds": str(seconds),
        "size": "720P",
        "aspect_ratio": aspect_ratio,
        "n": 1,
    }

    created = session.post(
        f"{base_url}/videos", headers=headers, json=payload, timeout=60
    )
    created.raise_for_status()
    task = created.json()
    video_id = task.get("video_id")
    if not video_id:
        raise RuntimeError("Agnes create response did not contain video_id.")

    result = None
    for attempt in range(max_polls):
        response = session.get(
            f"{host_root}/agnesapi",
            headers={"Authorization": f"Bearer {key}"},
            params={"video_id": video_id, "model_name": MODEL},
            timeout=60,
        )
        if response.status_code == 429:
            if attempt + 1 >= max_polls:
                response.raise_for_status()
            time.sleep(max(poll_interval, 10))
            continue
        response.raise_for_status()
        result = response.json()
        status = str(result.get("status", "")).strip().lower()
        if status in {"completed", "succeeded", "success", "done"}:
            break
        if status in {"failed", "error", "cancelled"}:
            raise RuntimeError("Agnes video task failed; inspect the sanitized provider error.")
        time.sleep(poll_interval)
    else:
        raise TimeoutError("Agnes video generation did not finish within the polling limit.")

    video_url = result.get("url") if isinstance(result, dict) else None
    if not isinstance(video_url, str) or urlparse(video_url).scheme != "https" or not urlparse(video_url).hostname:
        raise RuntimeError("Agnes completed response did not contain a secure video URL.")

    download = session.get(video_url, timeout=120)
    download.raise_for_status()
    content = download.content
    if len(content) < 1024 or len(content) < 8 or content[4:8] != b"ftyp":
        raise RuntimeError("Agnes returned an invalid or unexpectedly small MP4 file.")

    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    _videos_generated += 1
    return path


def reset_usage_for_tests() -> None:
    """Reset the in-process cap for isolated unit tests only."""
    global _videos_generated
    _videos_generated = 0
