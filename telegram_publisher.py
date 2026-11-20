import os
import requests

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "YOUR_TELEGRAM_CHAT_ID")
OUTPUT_DIR = "output"

def send_photo(photo_path: str, caption: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendPhoto"
    with open(photo_path, "rb") as photo:
        response = requests.post(
            url,
            data={"chat_id": TELEGRAM_CHAT_ID, "caption": caption[:1024]},
            files={"photo": photo},
            timeout=60
        )
    response.raise_for_status()
    print("Sent NŪR image post to Telegram.")

def send_video(video_path: str, caption: str):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendVideo"
    with open(video_path, "rb") as video:
        response = requests.post(
            url,
            data={
                "chat_id": TELEGRAM_CHAT_ID,
                "caption": caption[:1024],
                "supports_streaming": True
            },
            files={"video": video},
            timeout=120
        )
    response.raise_for_status()
    print("Sent NŪR vertical video to Telegram.")

def deliver_to_telegram():
    img_path = os.path.join(OUTPUT_DIR, "nur_image_post.png")
    img_cap_path = os.path.join(OUTPUT_DIR, "image_caption.txt")
    vid_path = os.path.join(OUTPUT_DIR, "nur_video_post.mp4")
    vid_cap_path = os.path.join(OUTPUT_DIR, "video_caption.txt")

    if os.path.exists(img_path) and os.path.exists(img_cap_path):
        with open(img_cap_path, "r", encoding="utf-8") as f:
            img_caption = f.read().strip()
        send_photo(img_path, f"NŪR — IMAGE POST\n\n{img_caption}")

    if os.path.exists(vid_path) and os.path.exists(vid_cap_path):
        with open(vid_cap_path, "r", encoding="utf-8") as f:
            vid_caption = f.read().strip()
        send_video(vid_path, f"NŪR — VERTICAL VIDEO\n\n{vid_caption}")

if __name__ == "__main__":
    deliver_to_telegram()
