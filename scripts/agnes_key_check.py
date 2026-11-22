"""Credential-only Agnes API check. Never calls model generation endpoints."""
import os
import sys
import requests

BASE_URL = os.getenv("AGNES_BASE_URL", "https://apihub.agnes-ai.com/v1").rstrip("/")
TARGET_MODELS = {
    "agnes-2.5-flash",
    "agnes-3.0-flash",
    "agnes-image-2.5-flash",
    "agnes-video-2.5-flash",
}

def check_models(session=requests):
    key = os.getenv("AGNES_API_KEY", "").strip()
    if not key:
        print("Agnes check: AGNES_API_KEY is not configured.")
        return 2
    try:
        response = session.get(
            f"{BASE_URL}/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=30,
        )
    except requests.RequestException as exc:
        print(f"Agnes check: network error ({type(exc).__name__}); no generation request made.")
        return 3

    if response.status_code in (401, 403):
        print(f"Agnes check: authentication rejected (HTTP {response.status_code}).")
        return 2
    if response.status_code != 200:
        print(f"Agnes check: model catalogue unavailable (HTTP {response.status_code}).")
        return 3

    try:
        payload = response.json()
        models = payload.get("data", [])
        names = sorted({
            str(item.get("id", "")).strip()
            for item in models if isinstance(item, dict)
        } - {""})
    except (ValueError, AttributeError, TypeError):
        print("Agnes check: catalogue response was not in the expected format.")
        return 3

    print("Agnes check: API key authenticated successfully.")
    print(f"Catalogue returned {len(names)} model IDs.")
    for model in sorted(TARGET_MODELS):
        print(f"{model}: {'available' if model in names else 'not listed'}")
    print("This check does NOT verify pricing, free quota, or generation capability.")
    print("No image, video, or text generation endpoint was called.")
    return 0

if __name__ == "__main__":
    sys.exit(check_models())
