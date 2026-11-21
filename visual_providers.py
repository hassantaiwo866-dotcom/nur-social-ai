"""Optional, auditable visual asset providers for Nūr Social AI.

This module does not publish content. It retrieves licensed Pixabay assets and
requests Gemini-generated images only when explicitly enabled by configuration.
"""
from __future__ import annotations

import os
import subprocess
from pathlib import Path
from typing import Any

import requests
from PIL import Image, ImageOps

GEMINI_IMAGE_MODEL = "gemini-3.1-flash-lite-image"
PIXABAY_API = "https://pixabay.com/api/"
PIXABAY_VIDEO_API = "https://pixabay.com/api/videos/"


def _record_asset(registry: list[dict[str, Any]] | None, record: dict[str, Any]) -> None:
    if registry is not None:
        registry.append(record)


def _save_image_response(content: bytes, destination: str | Path,
                         width: int, height: int) -> Path:
    path = Path(destination)
    if len(content) < 5_000:
        raise RuntimeError("Image response is empty or unexpectedly small.")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            if image.width < 640 or image.height < 480:
                raise RuntimeError("Image dimensions are below the quality threshold.")
            fitted = ImageOps.fit(
                ImageOps.exif_transpose(image).convert("RGB"),
                (width, height),
                method=Image.Resampling.LANCZOS,
            )
            fitted.save(path, "JPEG", quality=94, optimize=True, progressive=True)
    except Exception as exc:
        path.unlink(missing_ok=True)
        raise RuntimeError("Downloaded image failed validation.") from exc
    return path


def generate_gemini_image(prompt: str, destination: str | Path,
                          width: int, height: int, *,
                          api_key: str | None = None,
                          model: str | None = None,
                          registry: list[dict[str, Any]] | None = None,
                          session=requests) -> Path:
    """Generate one image through Gemini; caller must explicitly enable it."""
    key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()
    if not key:
        raise RuntimeError("GEMINI_API_KEY is not configured.")
    selected_model = (model or os.getenv("GEMINI_IMAGE_MODEL") or GEMINI_IMAGE_MODEL).strip()
    response = session.post(
        f"https://generativelanguage.googleapis.com/v1beta/models/{selected_model}:generateContent",
        headers={"x-goog-api-key": key, "Content-Type": "application/json"},
        json={
            "contents": [{"role": "user", "parts": [{
                "text": (
                    "Create a photorealistic, premium editorial photograph for a "
                    "wellbeing and personal-growth brand. No text, logos, watermark, "
                    "collage, poster layout or graphic typography. Use believable "
                    "human anatomy, natural lighting, coherent physical details, "
                    "thoughtful composition and a realistic camera perspective. "
                    f"Scene: {prompt}"
                )
            }]}],
            "generationConfig": {"responseModalities": ["IMAGE"]},
        },
        timeout=120,
    )
    response.raise_for_status()
    payload = response.json()
    parts = payload.get("candidates", [{}])[0].get("content", {}).get("parts", [])
    image_part = next((part.get("inlineData") for part in parts if part.get("inlineData")), None)
    if not image_part or not image_part.get("data"):
        raise RuntimeError("Gemini returned no image data.")
    import base64
    content = base64.b64decode(image_part["data"], validate=True)
    path = _save_image_response(content, destination, width, height)
    _record_asset(registry, {
        "provider": "Google Gemini",
        "model": selected_model,
        "asset_id": path.name,
        "creator": "AI-generated",
        "source_page": None,
        "license": "Generated under the applicable Google AI terms",
        "license_url": "https://ai.google.dev/gemini-api/terms",
        "media_type": "ai_generated_image",
        "review_required": True,
    })
    return path


def _pixabay_request(endpoint: str, params: dict[str, Any], *,
                     api_key: str | None = None, session=requests) -> dict[str, Any]:
    key = (api_key or os.getenv("PIXABAY_API_KEY", "")).strip()
    if not key:
        raise RuntimeError("PIXABAY_API_KEY is not configured.")
    response = session.get(endpoint, params={**params, "key": key}, timeout=45)
    response.raise_for_status()
    return response.json()


def search_pixabay_photo(query: str, destination: str | Path,
                         width: int, height: int, *,
                         api_key: str | None = None,
                         registry: list[dict[str, Any]] | None = None,
                         session=requests) -> Path:
    """Retrieve a high-resolution Pixabay photograph and preserve attribution."""
    payload = _pixabay_request(
        PIXABAY_API,
        {"q": query[:100], "image_type": "photo",
         "orientation": "horizontal" if width >= height else "vertical",
         "min_width": 1280 if width >= height else 720,
         "min_height": 720 if width >= height else 1280,
         "per_page": 20, "safesearch": "true"},
        api_key=api_key, session=session,
    )
    hits = payload.get("hits", [])
    hits.sort(key=lambda item: (item.get("imageWidth", 0) * item.get("imageHeight", 0)), reverse=True)
    for item in hits:
        url = item.get("largeImageURL") or item.get("webformatURL")
        if not url:
            continue
        try:
            image_response = session.get(url, timeout=60)
            image_response.raise_for_status()
            path = _save_image_response(image_response.content, destination, width, height)
            _record_asset(registry, {
                "provider": "Pixabay",
                "asset_id": item.get("id"),
                "title": item.get("tags", ""),
                "creator": item.get("user", ""),
                "source_page": item.get("pageURL"),
                "license": "Pixabay Content License",
                "license_url": "https://pixabay.com/service/license-summary/",
                "media_type": "stock_photograph",
                "review_required": True,
            })
            return path
        except Exception:
            continue
    raise RuntimeError("Pixabay returned no usable photograph at the required resolution.")


def search_pixabay_video(query: str, destination: str | Path, *,
                         api_key: str | None = None,
                         min_width: int = 1280, min_height: int = 720,
                         registry: list[dict[str, Any]] | None = None,
                         session=requests) -> Path:
    """Download a portrait stock-video clip and verify it with ffprobe."""
    payload = _pixabay_request(
        PIXABAY_VIDEO_API,
        {"q": query[:100], "video_type": "film",
         "min_width": min_width, "min_height": min_height,
         "per_page": 20, "safesearch": "true"},
        api_key=api_key, session=session,
    )
    hits = payload.get("hits", [])
    # Pixabay's video search endpoint does not expose an orientation filter.
    # Accept high-resolution landscape clips; the renderer reframes them vertically.
    hits.sort(key=lambda item: item.get("duration", 0) > 0, reverse=True)
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    for item in hits:
        variants = item.get("videos", {})
        candidates = sorted(
            variants.values(),
            key=lambda value: value.get("width", 0) * value.get("height", 0),
            reverse=True,
        )
        for variant in candidates:
            url = variant.get("url")
            if not url or variant.get("width", 0) < min_width or variant.get("height", 0) < min_height:
                continue
            try:
                video_response = session.get(url, timeout=120)
                video_response.raise_for_status()
                if len(video_response.content) < 100_000:
                    continue
                path.write_bytes(video_response.content)
                probe = subprocess.run(
                    ["ffprobe", "-v", "error", "-select_streams", "v:0",
                     "-show_entries", "stream=width,height", "-of", "json", str(path)],
                    capture_output=True, text=True, check=True, timeout=30,
                )
                streams = __import__("json").loads(probe.stdout).get("streams", [])
                if not streams:
                    path.unlink(missing_ok=True)
                    continue
                stream = streams[0]
                if stream.get("width", 0) < min_width or stream.get("height", 0) < min_height:
                    path.unlink(missing_ok=True)
                    continue
                _record_asset(registry, {
                    "provider": "Pixabay",
                    "asset_id": item.get("id"),
                    "title": item.get("tags", ""),
                    "creator": item.get("user", ""),
                    "source_page": item.get("pageURL"),
                    "license": "Pixabay Content License",
                    "license_url": "https://pixabay.com/service/license-summary/",
                    "media_type": "stock_video",
                    "duration_seconds": item.get("duration"),
                    "review_required": True,
                })
                return path
            except Exception:
                path.unlink(missing_ok=True)
    raise RuntimeError("Pixabay returned no usable portrait video at the required resolution.")
