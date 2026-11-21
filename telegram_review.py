"""Send generated Nūr assets to a private Telegram review chat.

This is a preview-only path. It does not publish to public channels and does
not use or bypass the NUR_APPROVED gate in telegram_publisher.py.
"""
import json
import os
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"
TELEGRAM_API = "https://api.telegram.org"


def deliver_review(
    token=None,
    chat_id=None,
    output_dir=None,
    request_post=None,
):
    """Deliver QA-passed media to the explicitly configured review chat.

    Missing credentials are treated as an intentional skip so generation and
    its GitHub artifact remain successful until Telegram secrets are configured.
    """
    token = (token if token is not None else os.environ.get("TELEGRAM_BOT_TOKEN", "")).strip()
    chat_id = (
        chat_id if chat_id is not None
        else (
            os.environ.get("TELEGRAM_REVIEW_CHAT_ID", "")
            or os.environ.get("TELEGRAM_CHAT_ID", "")
        )
    ).strip()
    output_dir = Path(output_dir) if output_dir else Path(os.environ.get("NUR_REVIEW_OUTPUT_DIR", "")).expanduser() if os.environ.get("NUR_REVIEW_OUTPUT_DIR", "").strip() else OUTPUT
    request_post = request_post or requests.post

    if not token or not chat_id:
        print(
            "Telegram review skipped: configure TELEGRAM_BOT_TOKEN and "
            "TELEGRAM_REVIEW_CHAT_ID or TELEGRAM_CHAT_ID in GitHub Actions secrets."
        )
        return False

    metadata_path = output_dir / "latest_post.json"
    image_path = output_dir / "nur_post.png"
    video_path = output_dir / "nur_reel.mp4"

    for path in (metadata_path, image_path, video_path):
        if not path.is_file():
            raise FileNotFoundError(f"Required review asset is missing: {path.name}")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    if metadata.get("qa", {}).get("status") != "passed":
        raise RuntimeError("Telegram review blocked: automated QA has not passed.")

    image_caption = f"Nūr — PRIVATE MEDIA REVIEW\n\n{metadata.get('image_caption', '')}"
    video_caption = f"Nūr — PRIVATE MEDIA REVIEW\n\n{metadata.get('video_caption', '')}"

    _upload(
        token, chat_id, "sendPhoto", "photo", image_path,
        image_caption, request_post,
    )
    try:
        _upload(
            token, chat_id, "sendVideo", "video", video_path,
            video_caption, request_post,
        )
    except RuntimeError as error:
        # Telegram may reject an MP4 for inline playback/size. Preserve delivery
        # by sending it as a downloadable document, and make that limitation clear.
        if "failed" not in str(error).lower():
            raise
        print("Telegram could not preview the MP4; retrying as a document.")
        _upload(
            token, chat_id, "sendDocument", "document", video_path,
            video_caption, request_post,
        )

    print("Nūr media delivered to the configured private Telegram review chat.")
    return True


def _upload(token, chat_id, endpoint, field_name, file_path, caption, request_post):
    url = f"{TELEGRAM_API}/bot{token}/{endpoint}"
    with open(file_path, "rb") as media:
        response = request_post(
            url,
            data={"chat_id": chat_id, "caption": caption[:1024]},
            files={field_name: media},
            timeout=180,
        )
    response.raise_for_status()
    result = response.json()
    if not result.get("ok"):
        raise RuntimeError(
            f"Telegram {endpoint} failed: {result.get('description', 'unknown error')}"
        )
    return result


if __name__ == "__main__":
    deliver_review()
