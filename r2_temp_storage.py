"""Short-lived private R2 storage for generated image references.

R2 objects stay private. Agnes receives only a short-lived presigned GET URL.
This module is not wired into production generation and is disabled by default.
"""
from __future__ import annotations

import mimetypes
import os
import uuid
from contextlib import contextmanager
from pathlib import Path
from urllib.parse import urlparse

try:
    import boto3
    from botocore.config import Config
except ImportError:  # pragma: no cover - dependency is declared in requirements
    boto3 = None
    Config = None

MAX_IMAGE_BYTES = 10 * 1024 * 1024
DEFAULT_URL_TTL_SECONDS = 600
MAX_URL_TTL_SECONDS = 900
ALLOWED_IMAGE_TYPES = {"image/png", "image/jpeg", "image/webp"}


def _settings():
    enabled = os.getenv("ENABLE_R2_TEMP_STORAGE", "").strip().lower()
    if enabled not in {"1", "true", "yes"}:
        raise RuntimeError("Temporary R2 storage is disabled.")
    if os.getenv("R2_FREE_TIER_CONFIRMED", "").strip().lower() != "yes":
        raise RuntimeError("Confirm the R2 free-tier limits before enabling storage.")
    values = {
        "account_id": os.getenv("R2_ACCOUNT_ID", "").strip(),
        "access_key": os.getenv("R2_ACCESS_KEY_ID", "").strip(),
        "secret_key": os.getenv("R2_SECRET_ACCESS_KEY", "").strip(),
        "bucket": os.getenv("R2_BUCKET_NAME", "").strip(),
    }
    missing = [key for key, value in values.items() if not value]
    if missing:
        raise RuntimeError("Missing R2 configuration: " + ", ".join(missing))
    if boto3 is None:
        raise RuntimeError("boto3 is required for temporary R2 storage.")
    return values


def _client(settings, session_factory=None):
    factory = session_factory or boto3.client
    return factory(
        "s3",
        endpoint_url=f"https://{settings['account_id']}.r2.cloudflarestorage.com",
        aws_access_key_id=settings["access_key"],
        aws_secret_access_key=settings["secret_key"],
        region_name="auto",
        config=Config(signature_version="s3v4"),
    )


@contextmanager
def temporary_image_url(
    image_path: str | Path,
    *,
    ttl_seconds: int = DEFAULT_URL_TTL_SECONDS,
    client_factory=None,
):
    """Upload one generated image, yield a short-lived GET URL, then delete it."""
    if not isinstance(ttl_seconds, int) or not 60 <= ttl_seconds <= MAX_URL_TTL_SECONDS:
        raise ValueError("R2 URL lifetime must be between 60 and 900 seconds.")

    settings = _settings()
    path = Path(image_path)
    if not path.is_file():
        raise FileNotFoundError("Generated image file does not exist.")
    size = path.stat().st_size
    if size <= 0 or size > MAX_IMAGE_BYTES:
        raise ValueError("Temporary image must be between 1 byte and 10 MB.")

    content_type, _ = mimetypes.guess_type(path.name)
    if content_type not in ALLOWED_IMAGE_TYPES:
        raise ValueError("Only PNG, JPEG and WebP images can be temporarily hosted.")

    client = _client(settings, client_factory)
    object_key = f"nur-media-temp/{uuid.uuid4().hex}{path.suffix.lower()}"
    uploaded = False
    try:
        client.upload_file(
            str(path),
            settings["bucket"],
            object_key,
            ExtraArgs={
                "ContentType": content_type,
                "CacheControl": "private, no-store, max-age=0",
                "Metadata": {"purpose": "agnes-reference", "temporary": "true"},
            },
        )
        uploaded = True
        url = client.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings["bucket"], "Key": object_key},
            ExpiresIn=ttl_seconds,
        )
        parsed = urlparse(url)
        if parsed.scheme != "https" or not parsed.hostname:
            raise RuntimeError("R2 did not return a secure HTTPS presigned URL.")
        yield url
    finally:
        if uploaded:
            # R2 DeleteObject is free. Cleanup is attempted even if Agnes fails.
            client.delete_object(Bucket=settings["bucket"], Key=object_key)
