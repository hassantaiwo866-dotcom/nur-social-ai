import json
import os
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()
APPROVED = os.environ.get("NUR_APPROVED", "").strip().lower() == "yes"


def send_file(endpoint, field_name, file_path, caption):
    url = f"https://api.telegram.org/bot{TOKEN}/{endpoint}"

    with open(file_path, "rb") as media:
        response = requests.post(
            url,
            data={
                "chat_id": CHAT_ID,
                "caption": caption[:1024],
            },
            files={field_name: media},
            timeout=180,
        )

    response.raise_for_status()
    result = response.json()

    if not result.get("ok"):
        raise RuntimeError(f"Telegram rejected the upload: {result}")


def deliver_to_telegram():
    if not APPROVED:
        raise RuntimeError(
            "Publishing blocked. Set NUR_APPROVED=yes only after "
            "personally reviewing and approving the assets."
        )

    if not TOKEN or not CHAT_ID:
        raise RuntimeError(
            "Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID."
        )

    metadata_path = OUTPUT / "latest_post.json"
    image_path = OUTPUT / "nur_post.png"
    video_path = OUTPUT / "nur_reel.mp4"

    if not metadata_path.exists():
        raise FileNotFoundError("No latest_post.json was found.")

    if not image_path.exists() or not video_path.exists():
        raise FileNotFoundError("Both approved media files must exist.")

    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))

    qa = metadata.get("qa", {})
    if qa.get("status") != "passed":
        raise RuntimeError("Automated QA has not passed.")

    image_caption = (
        f"Nūr — EDITORIAL\n\n{metadata['image_caption']}"
    )
    video_caption = (
        f"Nūr — CINEMATIC FILM\n\n{metadata['video_caption']}"
    )

    send_file(
        "sendPhoto",
        "photo",
        image_path,
        image_caption,
    )

    send_file(
        "sendVideo",
        "video",
        video_path,
        video_caption,
    )

    print("Approved Nūr assets delivered to Telegram.")


if __name__ == "__main__":
    deliver_to_telegram()
