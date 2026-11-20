import os
import json
import random
import urllib.parse
import asyncio
import requests
import edge_tts
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    concatenate_videoclips,
)

# --- NŪR BRAND PALETTE (Media Production Standard v1.0) ---
DEEP_FOREST = "#064E3B"
LIVING_GREEN = "#0B5D3B"
NEAR_BLACK = "#080808"
WARM_IVORY = "#F5F0E1"
MUTED_GOLD = "#D4AF37"
EARTH_BRONZE = "#A68A64"
CHARCOAL = "#1C1C1C"

VIDEO_CATEGORIES = [
    "Awareness (identifying subtle digital habits people recognise in themselves without shame)",
    "Practical Education (actionable, calm techniques to protect attention and focus)",
    "Recovery and Growth (responding to setbacks with self-compassion rather than guilt)",
    "Intentional Living (aligning daily digital choices with long-term personal development)",
    "Philosophy & Craft (why building quiet discipline matters more than quick dopamine)"
]


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return default
    return default


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def get_font(size, bold=False, serif=False):
    candidates = []
    if serif:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
    for path in candidates:
        if os.path.exists(path):
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def wrap_text(text, font, max_width, draw):
    words = text.split()
    lines = []
    current = ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = draw.textbbox((0, 0), test, font=font)
        if (bbox[2] - bbox[0]) <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def apply_subtle_grain(img, intensity=8):
    width, height = img.size
    noise = Image.effect_noise((width, height), intensity).convert("RGB")
    return Image.blend(img, noise, alpha=0.04)


def fetch_cinematic_photo(prompt, width, height, filename):
    full_prompt = (
        f"{prompt}, realistic editorial photography, natural window lighting, "
        "35mm film aesthetic, muted deep forest green and warm neutral shadows, "
        "shallow depth of field, calm atmosphere, NO text, NO words, NO letters, NO watermarks"
    )
    encoded = urllib.parse.quote(full_prompt)
    seed = random.randint(1000, 999999)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&seed={seed}&nologo=true"

    try:
        res = requests.get(url, timeout=35)
        if res.status_code == 200 and len(res.content) > 2500:
            with open(filename, "wb") as f:
                f.write(res.content)
            # Verify valid image and resize cleanly
            with Image.open(filename) as im:
                im = im.convert("RGB").resize((width, height), Image.Resampling.LANCZOS)
                im = apply_subtle_grain(im, intensity=10)
                im.save(filename, quality=95)
            return filename
    except Exception as e:
        print(f"Photo API fallback triggered ({e}) — crafting studio editorial backdrop...")

    # Fallback: Layered Deep Forest & Near Black Editorial Canvas with subtle grain
    img = Image.new("RGB", (width, height), NEAR_BLACK)
    draw = ImageDraw.Draw(img)
    for y in range(height):
        ratio = y / height
        r = int(8 + (6 - 8) * ratio)
        g = int(8 + (78 - 8) * ratio)
        b = int(8 + (59 - 8) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    img = apply_subtle_grain(img, intensity=12)
    img.save(filename, quality=95)
    return filename


def generate_editorial_plan(brand, history):
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise ValueError("Missing OPENROUTER_API_KEY")

    pillar = random.choice(brand.get("pillars", ["Digital Self-Control"]))
    category = random.choice(VIDEO_CATEGORIES)
    recent_topics = ", ".join(history[-15:]) if history else "None yet"

    system_prompt = (
        "You are the Creative Director for Nūr (spelled strictly 'Nūr' with a macron ū, NEVER 'NŪR'). "
        "Nūr is a serious, thoughtfully designed technology and personal-development company. "
        "Tagline: 'Build the person you want to become.' "
        "Tone: Calm, intelligent, premium, human, empowering. British English spelling (e.g., realisation, behaviour, focus). "
        "NEVER sound like a generic motivational page, religious guilt platform, or cheap screen-time blocker. "
        "Output ONLY valid raw JSON with no markdown backticks."
    )

    user_prompt = f"""
Create one cohesive Nūr media package for Pillar: "{pillar}" and Video Category: "{category}".
Avoid repeating these recent topics: {recent_topics}.

Return a JSON object with this exact structure:
{{
  "topic_slug": "short-unique-topic-id",
  "pillar_label": "SHORT UPPERCASE EDITORIAL LABEL (e.g. DIGITAL SELF-CONTROL)",
  "graphic": {{
    "theme": "dark_forest or warm_ivory",
    "headline": "Calm, powerful editorial statement (6 to 11 words, sentence case, ends with a period)",
    "subtext": "Thoughtful, grounded reflection expanding on the headline (16 to 24 words)",
    "photo_prompt": "Realistic, quiet photograph scene (e.g. closed leather notebook and brass pen on a wooden desk in soft morning light)"
  }},
  "caption_image": "Thoughtful British English social caption (3 short paragraphs) + 4 understated hashtags including #Nur",
  "video": {{
    "title": "Short internal title",
    "scenes": [
      {{
        "beat": "01 · THE HOOK",
        "voiceover": "Immediate relatable opening line (8-12 words)",
        "on_screen_text": "Short 4-6 word caption",
        "image_prompt": "Wide/medium realistic cinematic shot: person glancing at smartphone screen in dimly lit quiet room"
      }},
      {{
        "beat": "02 · THE PROBLEM",
        "voiceover": "Quiet consequence of distraction without shame (10-14 words)",
        "on_screen_text": "Short 4-6 word caption",
        "image_prompt": "Close-up realistic cinematic shot: open unfinished notebook and cold cup of tea beside a phone on wooden desk"
      }},
      {{
        "beat": "03 · THE REALISATION",
        "voiceover": "Grounded insight about environment and attention (11-15 words)",
        "on_screen_text": "Short 4-6 word caption",
        "image_prompt": "Over-the-shoulder realistic shot: person looking out a window onto green trees in soft natural daylight"
      }},
      {{
        "beat": "04 · THE RESPONSE",
        "voiceover": "Intentional, calm action to reclaim focus (10-14 words)",
        "on_screen_text": "Short 4-6 word caption",
        "image_prompt": "Close-up realistic shot: hand gently placing smartphone face-down on a dark wooden table and opening a book"
      }}
    ]
  }},
  "caption_video": "Calm, reflective British English reel caption + 4 understated hashtags including #Nur"
}}
"""

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://github.com/nur-social-ai",
        "X-Title": "Nur Editorial Pipeline",
    }

    payload = {
        "model": "google/gemini-2.0-flash-001",
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "temperature": 0.7,
    }

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers=headers,
        json=payload,
        timeout=45,
    )
    response.raise_for_status()
    data = response.json()
    raw = data["choices"][0]["message"]["content"].strip()
    if raw.startswith("```"):
        raw = raw.split("\n", 1)[1]
    if raw.endswith("```"):
        raw = raw.rsplit("```", 1)[0]
    return json.loads(raw.strip())


def build_editorial_graphic(plan, output_path="nur_post.png"):
    """Builds a 1080x1350 layered editorial Instagram feed card following Nūr v1.0 standards."""
    W, H = 1080, 1350
    g = plan["graphic"]
    use_ivory = g.get("theme") == "warm_ivory"

    bg_color = WARM_IVORY if use_ivory else DEEP_FOREST
    text_primary = CHARCOAL if use_ivory else WARM_IVORY
    text_secondary = "#4A4A4A" if use_ivory else "#D6D1C4"
    accent = EARTH_BRONZE if use_ivory else MUTED_GOLD

    canvas = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(canvas)

    # 1. Outer & Inner Geometric Framing
    outer_pad = 48
    inner_pad = 64
    draw.rectangle([outer_pad, outer_pad, W - outer_pad, H - outer_pad], outline=accent, width=1)
    draw.rectangle([inner_pad, inner_pad, W - inner_pad, H - inner_pad], outline=accent, width=1)

    # 2. Top Editorial Header Bar (Wordmark left, Pillar label right)
    logo_font = get_font(34, bold=True, serif=True)
    label_font = get_font(18, bold=False, serif=False)

    draw.text((104, 96), "Nūr", fill=text_primary, font=logo_font)
    pillar_text = plan.get("pillar_label", "INTENTIONAL LIVING").upper()
    p_bbox = draw.textbbox((0, 0), pillar_text, font=label_font)
    draw.text((W - 104 - (p_bbox[2] - p_bbox[0]), 106), pillar_text, fill=accent, font=label_font)

    # Thin horizontal rule under header
    draw.line  # Save topic to history so it never repeats
    history.append(content["topic_summary"])
    save_json("history.json", history)

    # --- PART A: SINGLE IMAGE POST ---
    print("2. Creating NŪR minimalist image post...")
    raw_img = os.path.join(OUTPUT_DIR, "temp_card_bg.jpg")
    final_img = os.path.join(OUTPUT_DIR, "nur_image_post.png")
    fetch_brand_image(content["single_image_post"]["visual_prompt"], 1080, 1350, raw_img)
    create_editorial_graphic(
        raw_img,
        content["single_image_post"]["headline"],
        content["single_image_post"]["subtext"],
        final_img
    )
    with open(os.path.join(OUTPUT_DIR, "image_caption.txt"), "w", encoding="utf-8") as f:
        f.write(content["single_image_post"]["caption"])
    if os.path.exists(raw_img):
        os.remove(raw_img)

    # --- PART B: VERTICAL VIDEO POST ---
    print("3. Creating NŪR vertical video post...")
    clips = []
    temp_files = []

    for i, scene in enumerate(content["video_post"]["scenes"]):
        s_img = os.path.join(OUTPUT_DIR, f"temp_scene_{i}.jpg")
        s_aud = os.path.join(OUTPUT_DIR, f"temp_scene_{i}.mp3")
        s_sub = os.path.join(OUTPUT_DIR, f"temp_sub_{i}.png")
        temp_files.extend([s_img, s_aud, s_sub])

        fetch_brand_image(scene["image_prompt"], 1080, 1920, s_img)
        await make_voiceover(scene["narration"], s_aud)
        make_subtitle_banner(scene["subtitle"], s_sub)

        audio = AudioFileClip(s_aud)
        duration = audio.duration + 0.3

        # Smooth subtle slow-zoom (Ken Burns effect) for calm premium feel
        bg_clip = (
            ImageClip(s_img)
            .with_duration(duration)
            .resized(lambda t: 1 + 0.04 * (t / duration))
            .with_position(("center", "center"))
        )
        sub_clip = ImageClip(s_sub).with_duration(duration).with_position(("center", 1420))

        scene_clip = CompositeVideoClip([bg_clip, sub_clip], size=(1080, 1920)).with_audio(audio)
        clips.append(scene_clip)

    final_video = concatenate_videoclips(clips, method="compose")
    final_video.write_videofile(
        os.path.join(OUTPUT_DIR, "nur_video_post.mp4"),
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )
    with open(os.path.join(OUTPUT_DIR, "video_caption.txt"), "w", encoding="utf-8") as f:
        f.write(content["video_post"]["caption"])

    for f in temp_files:
        if os.path.exists(f):
            os.remove(f)

    print("Completed! Generated NŪR image post and vertical video in /output.")

if __name__ == "__main__":
    asyncio.run(run_pipeline())
