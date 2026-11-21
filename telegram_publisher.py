import os
import json
import requests

TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()


def send_photo(photo_path, caption):
    url = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){TOKEN}/sendPhoto"
    with open(photo_path, "rb") as photo:
        response = requests.post(
            url,
            data={"chat_id": CHAT_ID, "caption": caption[:1024]},
            files={"photo": photo},
            timeout=60,
        )
    response.raise_for_status()


def send_video(video_path, caption):
    url = f"[https://api.telegram.org/bot](https://api.telegram.org/bot){TOKEN}/sendVideo"
    with open(video_path, "rb") as video:
        response = requests.post(
            url,
            data={"chat_id": CHAT_ID, "caption": caption[:1024], "supports_streaming": True},
            files={"video": video},
            timeout=120,
        )
    response.raise_for_status()


def deliver_to_telegram():
    if not TOKEN or not CHAT_ID:
        raise ValueError("Missing TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID")

    with open("latest_post.json", "r", encoding="utf-8") as f:
        meta = json.load(f)

    img_path = "nur_post.png"
    vid_path = "nur_reel.mp4"
    qa_report = meta.get("qa_report", "")

    if os.path.exists(img_path):
        send_photo(img_path, f"Nūr — EDITORIAL GRAPHIC\n\n{meta['image_caption']}")
    if os.path.exists(vid_path):
        video_msg = f"Nūr — CINEMATIC FILM\n\n{meta['video_caption']}"
        if qa_report:
            video_msg += f"\n\n---\n{qa_report}"
        send_video(vid_path, video_msg)

    print("Successfully delivered Nūr assets to Telegram.")


if __name__ == "__main__":
    deliver_to_telegram()
