"""Free-plan guarded Cloudflare Workers AI image generation for Nūr.

Only FLUX.1 Schnell is enabled. The caller must explicitly confirm a Workers
Free account (not Workers Paid), and a local per-process cap prevents runaway
requests. Cloudflare Free rejects inference after its shared daily 10,000-Neuron
allowance is exhausted. This module never retries through a paid provider.
"""
from __future__ import annotations
import base64
import os
from pathlib import Path
import requests
from PIL import Image

MODEL = "@cf/black-forest-labs/flux-1-schnell"
API_ROOT = "https://api.cloudflare.com/client/v4/accounts"
DEFAULT_MAX_IMAGES = 5
_images_generated = 0

def _enabled() -> bool:
    return os.getenv("ENABLE_CLOUDFLARE_IMAGE_GENERATION", "").strip().lower() in ("1", "true", "yes")

def _credentials() -> tuple[str, str]:
    if not _enabled():
        raise RuntimeError("Cloudflare image generation is disabled.")
    if os.getenv("CLOUDFLARE_FREE_PLAN_CONFIRMED", "").strip().lower() != "yes":
        raise RuntimeError("Confirm the account is on Cloudflare Workers Free (not Workers Paid) before enabling image generation.")
    account_id = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
    if not account_id or not token:
        raise RuntimeError("CLOUDFLARE_ACCOUNT_ID and CLOUDFLARE_API_TOKEN are required.")
    return account_id, token

def generate_image(prompt: str, destination: str | Path, *, session=requests, max_images: int | None = None, steps: int = 4) -> Path:
    """Generate and validate one FLUX.1 Schnell image within a strict batch cap."""
    global _images_generated
    account_id, token = _credentials()
    cap = max_images if max_images is not None else int(os.getenv("CLOUDFLARE_MAX_IMAGES_PER_RUN", str(DEFAULT_MAX_IMAGES)))
    if cap < 1 or cap > 5:
        raise ValueError("CLOUDFLARE_MAX_IMAGES_PER_RUN must be between 1 and 5.")
    if _images_generated >= cap:
        raise RuntimeError(f"Cloudflare per-run image cap reached ({cap}).")
    if not prompt or not prompt.strip():
        raise ValueError("Image prompt must not be empty.")
    if steps < 1 or steps > 4:
        raise ValueError("FLUX.1 Schnell steps must be between 1 and 4 in Nūr free-only configuration.")
    response = session.post(
        f"{API_ROOT}/{account_id}/ai/run/{MODEL}",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        json={"prompt": prompt.strip()[:2048], "steps": steps}, timeout=180,
    )
    response.raise_for_status()
    content_type = response.headers.get("Content-Type", "") if hasattr(response, "headers") else ""
    if isinstance(content_type, str) and content_type.startswith("image/"):
        image_bytes = response.content
    else:
        payload = response.json()
        if isinstance(payload, dict) and isinstance(payload.get("result"), dict):
            payload = payload["result"]
        encoded = payload.get("image") if isinstance(payload, dict) else None
        if not encoded:
            raise RuntimeError("Cloudflare response did not contain a base64 image.")
        image_bytes = base64.b64decode(encoded, validate=True)
    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(image_bytes)
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            if image.width < 512 or image.height < 512:
                raise RuntimeError("Cloudflare generated image is below 512px minimum.")
    except Exception as exc:
        path.unlink(missing_ok=True)
        raise RuntimeError("Cloudflare generated image failed validation.") from exc
    _images_generated += 1
    return path

def reset_usage_for_tests() -> None:
    """Reset the in-process cap for isolated unit tests only."""
    global _images_generated
    _images_generated = 0


KLEIN_MODEL = "@cf/black-forest-labs/flux-2-klein-4b"
KLEIN_API_URL_SUFFIX = "/ai/run/" + KLEIN_MODEL


def generate_klein_image(
    prompt: str,
    destination: str | Path,
    *,
    width: int = 1024,
    height: int = 1024,
    reference_images: list[str | Path] | None = None,
    session=requests,
    max_images: int | None = None,
) -> Path:
    """Generate one FLUX.2 Klein 4B image using Cloudflare's multipart REST API.

    Reference images are optional and limited to four. Cloudflare requires each
    reference image to be smaller than 512x512. This function never falls back
    to a paid model and shares the existing per-process request cap.
    """
    global _images_generated
    account_id, token = _credentials()
    cap = max_images if max_images is not None else int(
        os.getenv("CLOUDFLARE_MAX_IMAGES_PER_RUN", str(DEFAULT_MAX_IMAGES))
    )
    if cap < 1 or cap > 5:
        raise ValueError("CLOUDFLARE_MAX_IMAGES_PER_RUN must be between 1 and 5.")
    if _images_generated >= cap:
        raise RuntimeError(f"Cloudflare per-run image cap reached ({cap}).")
    if not prompt or not prompt.strip():
        raise ValueError("Image prompt must not be empty.")
    if not (256 <= int(width) <= 1920 and 256 <= int(height) <= 1920):
        raise ValueError("FLUX.2 Klein width and height must be between 256 and 1920.")
    references = list(reference_images or [])
    if len(references) > 4:
        raise ValueError("FLUX.2 Klein accepts at most four reference images.")

    data = {"prompt": prompt.strip()[:2048], "width": str(int(width)), "height": str(int(height))}
    opened = []
    files = {}
    try:
        for index, reference in enumerate(references):
            handle = open(reference, "rb")
            opened.append(handle)
            with Image.open(reference) as image:
                if image.width >= 512 or image.height >= 512:
                    raise ValueError("Each FLUX.2 Klein reference image must be smaller than 512x512.")
                image_format = (image.format or "PNG").lower()
            mime = "image/jpeg" if image_format in ("jpeg", "jpg") else f"image/{image_format}"
            files[f"input_image_{index}"] = (Path(reference).name, handle, mime)

        response = session.post(
            f"{API_ROOT}/{account_id}{KLEIN_API_URL_SUFFIX}",
            headers={"Authorization": f"Bearer {token}"},
            data=data,
            files=files or None,
            timeout=180,
        )
        response.raise_for_status()
        content_type = response.headers.get("Content-Type", "") if hasattr(response, "headers") else ""
        if isinstance(content_type, str) and content_type.startswith("image/"):
            image_bytes = response.content
        else:
            payload = response.json()
            if isinstance(payload, dict) and isinstance(payload.get("result"), dict):
                payload = payload["result"]
            encoded = payload.get("image") if isinstance(payload, dict) else None
            if not encoded:
                raise RuntimeError("Cloudflare FLUX.2 Klein response did not contain an image.")
            image_bytes = base64.b64decode(encoded, validate=True)
    finally:
        for handle in opened:
            handle.close()

    path = Path(destination)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(image_bytes)
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            if image.width < 512 or image.height < 512:
                raise RuntimeError("Cloudflare FLUX.2 Klein image is below 512px minimum.")
    except Exception as exc:
        path.unlink(missing_ok=True)
        raise RuntimeError("Cloudflare FLUX.2 Klein image failed validation.") from exc
    _images_generated += 1
    return path
