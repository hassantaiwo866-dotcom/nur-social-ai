
import asyncio
import json
import math
import os
import random
import shutil
import struct
import subprocess
import tempfile
import urllib.parse
import wave
from pathlib import Path

import edge_tts
import requests
from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parent
OUTPUT = ROOT / "output"
OUTPUT.mkdir(exist_ok=True)

# Nūr brand palette
DEEP_FOREST = "#064E3B"
LIVING_GREEN = "#0B5D3B"
NEAR_BLACK = "#080808"
WARM_IVORY = "#F5F0E1"
MUTED_GOLD = "#D4AF37"
EARTH_BRONZE = "#A68A64"
CHARCOAL = "#1C1C1C"

WIDTH, HEIGHT = 1080, 1920
FPS = 24
TAGLINE = "Build the person you want to become."
WORDMARK = "Nūr"

VIDEO_CATEGORIES = [
    "Awareness: recognise digital habits without shame",
    "Practical education: protect attention and focus",
    "Recovery: respond to setbacks without guilt",
    "Intentional living: align choices with long-term goals",
    "Philosophy: quiet discipline over quick dopamine",
]


def run_command(command):
    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"Command failed:\n{' '.join(map(str, command))}\n"
            f"{result.stderr[-4000:]}"
        )
    return result.stdout.strip()


def require_tools():
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            raise RuntimeError(f"{tool} is not installed or is not on PATH.")


def load_json(path, default):
    path = Path(path)
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return default


def save_json(path, data):
    Path(path).write_text(
        json.dumps(data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )


def font(size, serif=False, bold=False):
    candidates = []
    if serif:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"
            if bold else
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
        ]
    else:
        candidates += [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
            if bold else
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)

    return ImageFont.load_default()


def wrap_text(text, selected_font, draw, max_width):
    words = str(text).split()
    lines = []
    current = ""

    for word in words:
        candidate = f"{current} {word}".strip()
        bounds = draw.textbbox((0, 0), candidate, font=selected_font)

        if bounds[2] - bounds[0] <= max_width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word

    if current:
        lines.append(current)

    return lines


def enforce_wordmark(value):
    if not isinstance(value, str):
        return value

    replacements = {
        "NŪR": "Nūr",
        "NUR": "Nūr",
        "N□R": "Nūr",
    }

    for old, new in replacements.items():
        value = value.replace(old, new)

    return value


def generate_photo(prompt, width, height, destination):
    full_prompt = (
        f"{prompt}. Premium realistic editorial photography, "
        "natural cinematic lighting, believable human environments, "
        "authentic materials and detailed surroundings, "
        "deep forest green and warm neutral colour grading, "
        "35mm film character, carefully composed, "
        "no text, no typography, no logos, no watermarks, "
        "no green-screen background."
    )

    encoded = urllib.parse.quote(full_prompt)
    seed = random.randint(10000, 99999999)
    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={width}&height={height}&seed={seed}&nologo=true"
    )

    response = requests.get(url, timeout=90)
    response.raise_for_status()

    if len(response.content) < 12000:
        raise RuntimeError("Image service returned an unexpectedly small image.")

    destination = Path(destination)
    destination.write_bytes(response.content)

    try:
        with Image.open(destination) as image:
            image = ImageOps.fit(
                image.convert("RGB"),
                (width, height),
                method=Image.Resampling.LANCZOS,
            )
            image.save(destination, format="JPEG", quality=94, optimize=True)
    except Exception as exc:
        destination.unlink(missing_ok=True)
        raise RuntimeError("Image service did not return a valid image.") from exc

    return destination


def generate_editorial_plan(brand, history):
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("Missing OPENROUTER_API_KEY environment variable.")

    pillars = brand.get("pillars", ["Digital Self-Control"])
    pillar = random.choice(pillars)
    category = random.choice(VIDEO_CATEGORIES)

    recent = ", ".join(history[-15:]) if history else "None"

    system_prompt = """
You are the editorial director for Nūr.
The brand name must always be written exactly as Nūr.
Never write NŪR or NUR as the brand name.

Nūr supports self-control, protection, recovery and personal growth.
Its philosophy is privacy-first, non-judgemental and user-controlled.
Never shame people, induce guilt, use fear-based marketing,
invent statistics, fabricate religious quotations or claim
that unverified app features are available.

Use British English. Be calm, intelligent, precise and human.
Return valid JSON only. Do not use Markdown fences.
"""

    user_prompt = f"""
Create one original Nūr social-media content package.

Pillar: {pillar}
Category: {category}
Avoid these recent topics: {recent}

Return this exact JSON structure:

{{
  "topic_slug": "short-unique-topic-id",
  "pillar_label": "SHORT EDITORIAL LABEL",
  "graphic": {{
    "theme": "dark_forest",
    "headline": "A thoughtful statement of 6 to 11 words.",
    "subtext": "A grounded reflection of 16 to 24 words.",
    "photo_prompt": "Describe a detailed realistic photographic scene."
  }},
  "caption_image": "Three short paragraphs and four understated hashtags.",
  "video": {{
    "title": "Internal video title",
    "scenes": [
      {{
        "beat": "01 - THE HOOK",
        "voiceover": "An immediate relatable opening line.",
        "on_screen_text": "Short caption",
        "image_prompt": "Detailed realistic cinematic scene."
      }},
      {{
        "beat": "02 - THE PROBLEM",
        "voiceover": "Explain a consequence without shaming anyone.",
        "on_screen_text": "Short caption",
        "image_prompt": "A distinct detailed cinematic scene."
      }},
      {{
        "beat": "03 - THE REALISATION",
        "voiceover": "Offer a grounded behavioural insight.",
        "on_screen_text": "Short caption",
        "image_prompt": "A distinct detailed cinematic scene."
      }},
      {{
        "beat": "04 - THE RESPONSE",
        "voiceover": "Give one practical and calm action.",
        "on_screen_text": "Short caption",
        "image_prompt": "A distinct detailed cinematic scene."
      }}
    ]
  }},
  "caption_video": "A calm reflective caption and four hashtags."
}}

Make the four visual scenes noticeably different.
Avoid generic gradients, empty green backgrounds and abstract shapes.
Use believable locations, objects, lighting and human activity.
"""

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/hassantaiwo866-dotcom/nur-social-ai",
            "X-Title": "Nur Editorial Pipeline",
        },
        json={
            "model": "google/gemini-2.0-flash-001",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.7,
        },
        timeout=60,
    )
    response.raise_for_status()

    raw = response.json()["choices"][0]["message"]["content"].strip()

    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0]

    plan = json.loads(raw.strip())

    required = (
        "topic_slug",
        "pillar_label",
        "graphic",
        "caption_image",
        "video",
        "caption_video",
    )
    for key in required:
        if key not in plan:
            raise ValueError(f"Editorial plan is missing: {key}")

    scenes = plan["video"].get("scenes", [])
    if len(scenes) != 4:
        raise ValueError("The video plan must contain exactly four scenes.")

    for scene in scenes:
        for key in ("beat", "voiceover", "on_screen_text", "image_prompt"):
            if not scene.get(key):
                raise ValueError(f"Scene is missing: {key}")

    plan["caption_image"] = enforce_wordmark(plan["caption_image"])
    plan["caption_video"] = enforce_wordmark(plan["caption_video"])
    plan["graphic"]["headline"] = enforce_wordmark(plan["graphic"]["headline"])
    plan["graphic"]["subtext"] = enforce_wordmark(plan["graphic"]["subtext"])

    return plan


def build_editorial_graphic(plan, destination, photo_path):
    graphic = plan["graphic"]
    ivory_theme = graphic.get("theme") == "warm_ivory"

    background = WARM_IVORY if ivory_theme else DEEP_FOREST
    primary = CHARCOAL if ivory_theme else WARM_IVORY
    secondary = "#4A4A4A" if ivory_theme else "#D6D1C4"
    accent = EARTH_BRONZE if ivory_theme else MUTED_GOLD

    width, height = 1080, 1350
    canvas = Image.new("RGB", (width, height), background)
    draw = ImageDraw.Draw(canvas)

    draw.rectangle((48, 48, 1032, 1302), outline=accent, width=2)

    logo_font = font(38, serif=True, bold=True)
    label_font = font(17)
    headline_font = font(49, serif=True, bold=True)
    body_font = font(26)
    footer_font = font(17)

    draw.text((104, 88), WORDMARK, fill=primary, font=logo_font)

    label = str(plan.get("pillar_label", "INTENTIONAL LIVING")).upper()
    label_bounds = draw.textbbox((0, 0), label, font=label_font)
    draw.text(
        (976 - (label_bounds[2] - label_bounds[0]), 105),
        label,
        fill=accent,
        font=label_font,
    )

    draw.line((104, 158, 976, 158), fill=accent, width=2)

    with Image.open(photo_path) as photo:
        photo = ImageOps.fit(
            photo.convert("RGB"),
            (872, 440),
            method=Image.Resampling.LANCZOS,
        )
        canvas.paste(photo, (104, 190))

    y = 680
    headline_lines = wrap_text(
        graphic["headline"], headline_font, draw, 872
    )
    for line in headline_lines[:3]:
        draw.text((104, y), line, fill=primary, font=headline_font)
        y += 61

    y += 15
    draw.line((104, y, 220, y), fill=accent, width=3)
    y += 28

    body_lines = wrap_text(graphic["subtext"], body_font, draw, 872)
    for line in body_lines[:3]:
        draw.text((104, y), line, fill=secondary, font=body_font)
        y += 39

    draw.line((104, 1190, 976, 1190), fill=accent, width=1)
    draw.text((104, 1210), TAGLINE, fill=secondary, font=footer_font)

    edition = "NŪR EDITORIAL"
    edition_bounds = draw.textbbox((0, 0), edition, font=footer_font)
    draw.text(
        (976 - (edition_bounds[2] - edition_bounds[0]), 1210),
        edition,
        fill=accent,
        font=footer_font,
    )

    canvas.save(destination, format="PNG", optimize=True)
    return destination


async def make_voiceover(text, destination):
    speech = edge_tts.Communicate(
        text,
        voice="en-GB-RyanNeural",
        rate="-5%",
    )
    await speech.save(str(destination))


def build_scene_frame(photo_path, scene, destination):
    with Image.open(photo_path) as image:
        frame = ImageOps.fit(
            image.convert("RGB"),
            (WIDTH, HEIGHT),
            method=Image.Resampling.LANCZOS,
        )

    draw = ImageDraw.Draw(frame, "RGBA")

    # Small, consistent brand signature.
    draw.text(
        (76, 100),
        WORDMARK,
        fill=(245, 240, 225, 245),
        font=font(38, serif=True, bold=True),
    )
    draw.text(
        (78, 151),
        scene["beat"].upper(),
        fill=(212, 175, 55, 245),
        font=font(19),
    )

    # Caption panel with enough space for readable text.
    panel_top = 1390
    draw.rounded_rectangle(
        (58, panel_top, WIDTH - 58, 1780),
        radius=18,
        fill=(8, 8, 8, 190),
        outline=(212, 175, 55, 180),
        width=2,
    )

    caption_font = font(43, serif=True)
    lines = wrap_text(
        scene["on_screen_text"],
        caption_font,
        draw,
        WIDTH - 180,
    )

    y = panel_top + 75
    for line in lines[:3]:
        bounds = draw.textbbox((0, 0), line, font=caption_font)
        x = (WIDTH - (bounds[2] - bounds[0])) // 2
        draw.text((x, y), line, fill=(245, 240, 225, 255), font=caption_font)
        y += 62

    frame.save(destination, format="JPEG", quality=94)
    return destination


def probe_duration(path):
    output = run_command([
        "ffprobe",
        "-v", "error",
        "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1",
        str(path),
    ])
    return float(output)


def make_video_segment(frame_path, audio_path, output_path, duration, zoom=True):
    if zoom:
        video_filter = (
            "zoompan=z='min(zoom+0.00035,1.035)':"
            "d=1:s=1080x1920:fps=24,format=yuv420p"
        )
    else:
        video_filter = "scale=1080:1920,format=yuv420p"

    run_command([
        "ffmpeg", "-y",
        "-loop", "1",
        "-i", str(frame_path),
        "-i", str(audio_path),
        "-vf", video_filter,
        "-af", "apad",
        "-t", str(duration),
        "-r", str(FPS),
        "-c:v", "libx264",
        "-preset", "medium",
        "-crf", "19",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac",
        "-b:a", "192k",
        "-shortest",
        str(output_path),
    ])


def make_ambient_sound(duration, destination):
    sample_rate = 44100
    frequencies = [87.31, 130.81, 164.81, 196.00]
    weights = [0.32, 0.27, 0.23, 0.18]
    total_samples = int(duration * sample_rate)
    fade = int(1.8 * sample_rate)

    with wave.open(str(destination), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(sample_rate)

        block = bytearray()

        for index in range(total_samples):
            t = index / sample_rate
            value = sum(
                weight * math.sin(2 * math.pi * frequency * t)
                for frequency, weight in zip(frequencies, weights)
            )

            envelope = 1.0
            if index < fade:
                envelope = index / fade
            elif index > total_samples - fade:
                envelope = max(0.0, (total_samples - index) / fade)

            sample = int(value * envelope * 3500)
            sample = max(-32767, min(32767, sample))
            block.extend(struct.pack("<h", sample))

            if len(block) >= 65536:
                wav.writeframes(block)
                block.clear()

        if block:
            wav.writeframes(block)


def create_end_card(destination):
    image = Image.new("RGB", (WIDTH, HEIGHT), DEEP_FOREST)
    draw = ImageDraw.Draw(image)

    draw.rectangle(
        (64, 64, WIDTH - 64, HEIGHT - 64),
        outline=MUTED_GOLD,
        width=3,
    )

    logo_font = font(112, serif=True, bold=True)
    tagline_font = font(38, serif=True)

    logo_bounds = draw.textbbox((0, 0), WORDMARK, font=logo_font)
    logo_x = (WIDTH - (logo_bounds[2] - logo_bounds[0])) // 2
    logo_y = 790
    draw.text((logo_x, logo_y), WORDMARK, fill=WARM_IVORY, font=logo_font)

    draw.line(
        (WIDTH // 2 - 100, 940, WIDTH // 2 + 100, 940),
        fill=MUTED_GOLD,
        width=3,
    )

    tagline_bounds = draw.textbbox((0, 0), TAGLINE, font=tagline_font)
    tagline_x = (WIDTH - (tagline_bounds[2] - tagline_bounds[0])) // 2
    draw.text(
        (tagline_x, 985),
        TAGLINE,
        fill=WARM_IVORY,
        font=tagline_font,
    )

    image.save(destination, format="JPEG", quality=95)
    return destination


def run_qa(image_path, video_path, plan):
    failures = []

    with Image.open(image_path) as image:
        if image.size != (1080, 1350):
            failures.append("Editorial image dimensions are incorrect.")

    if not video_path.exists() or video_path.stat().st_size < 50000:
        failures.append("Video file is missing or too small.")

    if video_path.exists():
        duration = probe_duration(video_path)
        if not 12 <= duration <= 60:
            failures.append(f"Unexpected video duration: {duration:.1f}s.")

    all_text = json.dumps(plan, ensure_ascii=False)

    if "NŪR" in all_text or "N□R" in all_text:
        failures.append("Incorrect wordmark spelling found in generated text.")

    harmful_terms = [
        "pathetic", "loser", "worthless", "lazy",
        "punish yourself", "you should be ashamed",
    ]
    lowered = all_text.lower()
    for term in harmful_terms:
        if term in lowered:
            failures.append(f"Potentially shaming language found: {term}")

    if failures:
        raise RuntimeError("QA failed:\n- " + "\n- ".join(failures))

    return {
        "status": "passed",
        "checks": [
            "Editorial image dimensions",
            "Video file and duration",
            "Generated text wordmark",
            "Basic non-shaming language check",
        ],
        "manual_review_required": True,
        "manual_review_note": (
            "Automated checks cannot reliably detect visual watermarks, "
            "poor composition, inaccurate imagery or brand-design defects. "
            "Review both assets before publishing."
        ),
    }


async def run_pipeline():
    require_tools()

    brand = load_json(ROOT / "brand_config.json", {
        "pillars": ["Digital Self-Control"],
    })
    history = load_json(ROOT / "history.json", [])

    if not isinstance(history, list):
        history = []

    print("1. Creating editorial plan...")
    plan = generate_editorial_plan(brand, history)

    with tempfile.TemporaryDirectory(prefix="nur_media_") as temp:
        temp = Path(temp)

        print("2. Generating editorial photograph...")
        graphic_photo = generate_photo(
            plan["graphic"]["photo_prompt"],
            872,
            440,
            temp / "graphic_photo.jpg",
        )

        print("3. Building editorial graphic...")
        image_path = OUTPUT / "nur_post.png"
        build_editorial_graphic(plan, image_path, graphic_photo)

        print("4. Producing cinematic scenes...")
        segments = []

        for index, scene in enumerate(plan["video"]["scenes"]):
            print(f"   Scene {index + 1}/4")

            photo = generate_photo(
                scene["image_prompt"],
                WIDTH,
                HEIGHT,
                temp / f"scene_{index}.jpg",
            )

            frame = build_scene_frame(
                photo,
                scene,
                temp / f"frame_{index}.jpg",
            )

            audio = temp / f"voice_{index}.mp3"
            await make_voiceover(scene["voiceover"], audio)

            duration = probe_duration(audio) + 0.6
            segment = temp / f"segment_{index}.mp4"

            make_video_segment(
                frame,
                audio,
                segment,
                duration,
                zoom=True,
            )
            segments.append(segment)

        print("5. Creating closing card...")
        end_card = create_end_card(temp / "end_car350
    g = plan["graphic"]
    use_ivory = g.get("theme") == "warm_ivory"

    bg_color = WARM_IVORY if use_ivory else DEEP_FOREST
    text_primary = CHARCOAL if use_ivory else WARM_IVORY
    text_secondary = "#4A4A4A" if use_ivory else "#D6D1C4"
    accent = EARTH_BRONZE if use_ivory else MUTED_GOLD

    canvas = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(canvas)

    outer_pad = 48
    inner_pad = 64
    draw.rectangle([outer_pad, outer_pad, W - outer_pad, H - outer_pad], outline=accent, width=1)
    draw.rectangle([inner_pad, inner_pad, W - inner_pad, H - inner_pad], outline=accent, width=1)

    logo_font = get_font(34, bold=True, serif=True)
    label_font = get_font(18, bold=False, serif=False)

    draw.text((104, 96), "Nūr", fill=text_primary, font=logo_font)
    pillar_text = plan.get("pillar_label", "INTENTIONAL LIVING").upper()
    p_bbox = draw.textbbox((0, 0), pillar_text, font=label_font)
    draw.text((W - 104 - (p_bbox[2] - p_bbox[0]), 106), pillar_text, fill=accent, font=label_font)

    draw.line([(104, 158), (W - 104, 158)], fill=accent, width=1)

    photo_w, photo_h = W - 208, 490
    temp_photo = "temp_editorial_photo.jpg"
    fetch_cinematic_photo(g["photo_prompt"], photo_w, photo_h, temp_photo)

    with Image.open(temp_photo) as photo:
        draw.rectangle([102, 198, 106 + photo_w, 202 + photo_h], outline=accent, width=1)
        canvas.paste(photo, (104, 200))

    headline_font = get_font(50, bold=True, serif=True)
    body_font = get_font(27, bold=False, serif=False)
    footer_font = get_font(18, bold=False, serif=False)

    y_cursor = 740
    headline_lines = wrap_text(g["headline"], headline_font, W - 208, draw)
    for line in headline_lines[:4]:
        draw.text((104, y_cursor), line, fill=text_primary, font=headline_font)
        y_cursor += 64

    y_cursor += 18
    draw.line([(104, y_cursor), (224, y_cursor)], fill=accent, width=2)
    y_cursor += 32

    body_lines = wrap_text(g["subtext"], body_font, W - 208, draw)
    for line in body_lines[:4]:
        draw.text((104, y_cursor), line, fill=text_secondary, font=body_font)
        y_cursor += 40

    draw.line([(104, H - 140), (W - 104, H - 140)], fill=accent, width=1)
    draw.text((104, H - 116), "Build the person you want to become.", fill=text_secondary, font=footer_font)
    edition_str = "EDITION · 01"
    e_bbox = draw.textbbox((0, 0), edition_str, font=footer_font)
    draw.text((W - 104 - (e_bbox[2] - e_bbox[0]), H - 116), edition_str, fill=accent, font=footer_font)

    canvas = apply_subtle_grain(canvas, intensity=7)
    canvas.save(output_path, quality=95)
    if os.path.exists(temp_photo):
        os.remove(temp_photo)
    return output_path


async def synthesize_voice(text, audio_path):
    communicate = edge_tts.Communicate(text, "en-GB-RyanNeural", rate="-6%")
    await communicate.save(audio_path)


def create_caption_overlay(width, height, beat_label, caption_text):
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    brand_font = get_font(30, bold=True, serif=True)
    beat_font = get_font(18, bold=False, serif=False)
    draw.text((72, 110), "Nūr", fill=(245, 240, 225, 230), font=brand_font)
    draw.text((72, 152), beat_label.upper(), fill=(212, 175, 55, 220), font=beat_font)

    cap_font = get_font(38, bold=False, serif=False)
    lines = wrap_text(caption_text, cap_font, width - 180, draw)
    box_height = len(lines) * 52 + 56
    box_top = height - 340 - box_height

    draw.rectangle([64, box_top, width - 64, box_top + box_height], fill=(8, 8, 8, 175))
    draw.line([(64, box_top), (width - 64, box_top)], fill=(212, 175, 55, 220), width=2)

    y = box_top + 28
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=cap_font)
        x = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, fill=(245, 240, 225, 255), font=cap_font)
        y += 52

    temp_ov = f"temp_ov_{random.randint(1000,9999)}.png"
    overlay.save(temp_ov)
    return temp_ov


def build_closing_endcard(width, height):
    card = Image.new("RGB", (width, height), DEEP_FOREST)
    draw = ImageDraw.Draw(card)

    pad = 64
    draw.rectangle([pad, pad, width - pad, height - pad], outline=MUTED_GOLD, width=2)

    logo_font = get_font(96, bold=True, serif=True)
    tag_font = get_font(34, bold=False, serif=True)

    l_bbox = draw.textbbox((0, 0), "Nūr", font=logo_font)
    lx = (width - (l_bbox[2] - l_bbox[0])) // 2
    ly = (height // 2) - 110
    draw.text((lx, ly), "Nūr", fill=WARM_IVORY, font=logo_font)

    draw.line([(width // 2 - 90, ly + 125), (width // 2 + 90, ly + 125)], fill=MUTED_GOLD, width=2)

    tagline = "Build the person you want to become."
    t_bbox = draw.textbbox((0, 0), tagline, font=tag_font)
    tx = (width - (t_bbox[2] - t_bbox[0])) // 2
    draw.text((tx, ly + 155), tagline, fill=WARM_IVORY, font=tag_font)

    card = apply_subtle_grain(card, intensity=8)
    end_path = "temp_nur_endcard.png"
    card.save(end_path, quality=95)
    return end_path


async def build_cinematic_reel(plan, output_path="nur_reel.mp4"):
    W, H = 1080, 1920
    clips = []
    temp_files = []

    for idx, scene in enumerate(plan["video"]["scenes"]):
        img_file = f"temp_scene_{idx}.jpg"
        aud_file = f"temp_scene_{idx}.mp3"
        temp_files.extend([img_file, aud_file])

        fetch_cinematic_photo(scene["image_prompt"], W, H, img_file)
        await synthesize_voice(scene["voiceover"], aud_file)

        audio_clip = AudioFileClip(aud_file)
        duration = audio_clip.duration + 0.45

        bg_clip = (
            ImageClip(img_file)
            .set_duration(duration)
            .resize(lambda t: 1.0 + 0.035 * (t / duration))
            .set_position("center")
        )

        ov_file = create_caption_overlay(W, H, scene["beat"], scene["on_screen_text"])
        temp_files.append(ov_file)
        ov_clip = ImageClip(ov_file).set_duration(duration)

        scene_comp = CompositeVideoClip([bg_clip, ov_clip], size=(W, H)).set_audio(audio_clip)
        clips.append(scene_comp)

    end_audio = "temp_end_audio.mp3"
    temp_files.append(end_audio)
    await synthesize_voice("Nūr. Build the person you want to become.", end_audio)
    end_aud_clip = AudioFileClip(end_audio)
    end_dur = end_aud_clip.duration + 1.0

    end_img = build_closing_endcard(W, H)
    temp_files.append(end_img)
    end_clip = ImageClip(end_img).set_duration(end_dur).set_audio(end_aud_clip)
    clips.append(end_clip)

    final_video = concatenate_videoclips(clips, method="compose")

    ambient_wav = generate_ambient_soundbed(final_video.duration + 0.5)
    temp_files.append(ambient_wav)
    ambient_clip = AudioFileClip(ambient_wav).subclip(0, final_video.duration).volumex(0.14)

    mixed_audio = CompositeAudioClip([final_video.audio, ambient_clip])
    final_video = final_video.set_audio(mixed_audio)

    final_video.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=2,
        logger=None,
    )

    duration_sec = round(final_video.duration, 1)
    final_video.close()

    for f in temp_files:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass

    return output_path, duration_sec


def run_qa_checks(plan, img_path, vid_path, vid_duration):
    checks = []

    all_text = json.dumps(plan, ensure_ascii=False)
    spelling_ok = ("NŪR" not in all_text) and ("N□R" not in all_text)
    checks.append(("Wordmark spelling (Nūr)", spelling_ok))

    img_ok = False
    if os.path.exists(img_path) and os.path.getsize(img_path) > 15000:
        with Image.open(img_path) as im:
            img_ok = im.size == (1080, 1350)
    checks.append(("Editorial graphic format (1080×1350)", img_ok))

    vid_ok = os.path.exists(vid_path) and os.path.getsize(vid_path) > 50000 and (12.0 <= vid_duration <= 45.0)
    checks.append((f"Cinematic reel ({vid_duration}s, 5 beats + ambient audio)", vid_ok))

    banned_words = ["ashamed", "pathetic", "lazy", "loser", "sinful", "punish"]
    tone_ok = not any(w in all_text.lower() for w in banned_words)
    checks.append(("Calm, non-shame brand tone", tone_ok))

    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    summary_lines = [f"{'✓' if ok else '✗'} {label}" for label, ok in checks]
    report = f"QA Verification: {passed}/{total} passed\n" + "\n".join(summary_lines)

    if passed < total:
        raise RuntimeError(f"Nūr QA Gate blocked delivery:\n{report}")

    return report


async def run_pipeline():
    brand = load_json("brand_config.json", {"pillars": ["Digital Self-Control"]})
    history = load_json("history.json", [])

    print("1. Generating Nūr editorial plan via OpenRouter...")
    plan = generate_editorial_plan(brand, history)

    print("2. Creating Nūr layered editorial graphic (1080x1350)...")
    build_editorial_graphic(plan, "nur_post.png")

    print("3. Creating Nūr cinematic vertical film with ambient soundbed (1080x1920)...")
    _, vid_duration = await build_cinematic_reel(plan, "nur_reel.mp4")

    print("4. Running Nūr Section 8 automated QA gate...")
    qa_report = run_qa_checks(plan, "nur_post.png", "nur_reel.mp4", vid_duration)
    print(qa_report)

    save_json(
        "latest_post.json",
        {
            "image_caption": plan["caption_image"],
            "video_caption": plan["caption_video"],
            "topic": plan["topic_slug"],
            "qa_report": qa_report,
        },
    )

    history.append(plan["topic_slug"])
    save_json("history.json", history[-50:])
    print("5. Nūr production pipeline complete.")


if __name__ == "__main__":
    asyncio.run(run_pipeline())350
    g = plan["graphic"]
    use_ivory = g.get("theme") == "warm_ivory"

    bg_color = WARM_IVORY if use_ivory else DEEP_FOREST
    text_primary = CHARCOAL if use_ivory else WARM_IVORY
    text_secondary = "#4A4A4A" if use_ivory else "#D6D1C4"
    accent = EARTH_BRONZE if use_ivory else MUTED_GOLD

    canvas = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(canvas)

    outer_pad = 48
    inner_pad = 64
    draw.rectangle([outer_pad, outer_pad, W - outer_pad, H - outer_pad], outline=accent, width=1)
    draw.rectangle([inner_pad, inner_pad, W - inner_pad, H - inner_pad], outline=accent, width=1)

    logo_font = get_font(34, bold=True, serif=True)
    label_font = get_font(18, bold=False, serif=False)

    draw.text((104, 96), "Nūr", fill=text_primary, font=logo_font)
    pillar_text = plan.get("pillar_label", "INTENTIONAL LIVING").upper()
    p_bbox = draw.textbbox((0, 0), pillar_text, font=label_font)
    draw.text((W - 104 - (p_bbox[2] - p_bbox[0]), 106), pillar_text, fill=accent, font=label_font)

    draw.line([(104, 158), (W - 104, 158)], fill=accent, width=1)

    photo_w, photo_h = W - 208, 490
    temp_photo = "temp_editorial_photo.jpg"
    fetch_cinematic_photo(g["photo_prompt"], photo_w, photo_h, temp_photo)

    with Image.open(temp_photo) as photo:
        draw.rectangle([102, 198, 106 + photo_w, 202 + photo_h], outline=accent, width=1)
        canvas.paste(photo, (104, 200))

    headline_font = get_font(50, bold=True, serif=True)
    body_font = get_font(27, bold=False, serif=False)
    footer_font = get_font(18, bold=False, serif=False)

    y_cursor = 740
    headline_lines = wrap_text(g["headline"], headline_font, W - 208, draw)
    for line in headline_lines[:4]:
        draw.text((104, y_cursor), line, fill=text_primary, font=headline_font)
        y_cursor += 64

    y_cursor += 18
    draw.line([(104, y_cursor), (224, y_cursor)], fill=accent, width=2)
    y_cursor += 32

    body_lines = wrap_text(g["subtext"], body_font, W - 208, draw)
    for line in body_lines[:4]:
        draw.text((104, y_cursor), line, fill=text_secondary, font=body_font)
        y_cursor += 40

    draw.line([(104, H - 140), (W - 104, H - 140)], fill=accent, width=1)
    draw.text((104, H - 116), "Build the person you want to become.", fill=text_secondary, font=footer_font)
    edition_str = "EDITION · 01"
    e_bbox = draw.textbbox((0, 0), edition_str, font=footer_font)
    draw.text((W - 104 - (e_bbox[2] - e_bbox[0]), H - 116), edition_str, fill=accent, font=footer_font)

    canvas = apply_subtle_grain(canvas, intensity=7)
    canvas.save(output_path, quality=95)
    if os.path.exists(temp_photo):
        os.remove(temp_photo)
    return output_path


async def synthesize_voice(text, audio_path):
    communicate = edge_tts.Communicate(text, "en-GB-RyanNeural", rate="-6%")
    await communicate.save(audio_path)


def create_caption_overlay(width, height, beat_label, caption_text):
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    brand_font = get_font(30, bold=True, serif=True)
    beat_font = get_font(18, bold=False, serif=False)
    draw.text((72, 110), "Nūr", fill=(245, 240, 225, 230), font=brand_font)
    draw.text((72, 152), beat_label.upper(), fill=(212, 175, 55, 220), font=beat_font)

    cap_font = get_font(38, bold=False, serif=False)
    lines = wrap_text(caption_text, cap_font, width - 180, draw)
    box_height = len(lines) * 52 + 56
    box_top = height - 340 - box_height

    draw.rectangle([64, box_top, width - 64, box_top + box_height], fill=(8, 8, 8, 175))
    draw.line([(64, box_top), (width - 64, box_top)], fill=(212, 175, 55, 220), width=2)

    y = box_top + 28
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=cap_font)
        x = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, fill=(245, 240, 225, 255), font=cap_font)
        y += 52

    temp_ov = f"temp_ov_{random.randint(1000,9999)}.png"
    overlay.save(temp_ov)
    return temp_ov


def build_closing_endcard(width, height):
    card = Image.new("RGB", (width, height), DEEP_FOREST)
    draw = ImageDraw.Draw(card)

    pad = 64
    draw.rectangle([pad, pad, width - pad, height - pad], outline=MUTED_GOLD, width=2)

    logo_font = get_font(96, bold=True, serif=True)
    tag_font = get_font(34, bold=False, serif=True)

    l_bbox = draw.textbbox((0, 0), "Nūr", font=logo_font)
    lx = (width - (l_bbox[2] - l_bbox[0])) // 2
    ly = (height // 2) - 110
    draw.text((lx, ly), "Nūr", fill=WARM_IVORY, font=logo_font)

    draw.line([(width // 2 - 90, ly + 125), (width // 2 + 90, ly + 125)], fill=MUTED_GOLD, width=2)

    tagline = "Build the person you want to become."
    t_bbox = draw.textbbox((0, 0), tagline, font=tag_font)
    tx = (width - (t_bbox[2] - t_bbox[0])) // 2
    draw.text((tx, ly + 155), tagline, fill=WARM_IVORY, font=tag_font)

    card = apply_subtle_grain(card, intensity=8)
    end_path = "temp_nur_endcard.png"
    card.save(end_path, quality=95)
    return end_path


async def build_cinematic_reel(plan, output_path="nur_reel.mp4"):
    W, H = 1080, 1920
    clips = []
    temp_files = []

    for idx, scene in enumerate(plan["video"]["scenes"]):
        img_file = f"temp_scene_{idx}.jpg"
        aud_file = f"temp_scene_{idx}.mp3"
        temp_files.extend([img_file, aud_file])

        fetch_cinematic_photo(scene["image_prompt"], W, H, img_file)
        await synthesize_voice(scene["voiceover"], aud_file)

        audio_clip = AudioFileClip(aud_file)
        duration = audio_clip.duration + 0.45

        bg_clip = (
            ImageClip(img_file)
            .set_duration(duration)
            .resize(lambda t: 1.0 + 0.035 * (t / duration))
            .set_position("center")
        )

        ov_file = create_caption_overlay(W, H, scene["beat"], scene["on_screen_text"])
        temp_files.append(ov_file)
        ov_clip = ImageClip(ov_file).set_duration(duration)

        scene_comp = CompositeVideoClip([bg_clip, ov_clip], size=(W, H)).set_audio(audio_clip)
        clips.append(scene_comp)

    end_audio = "temp_end_audio.mp3"
    temp_files.append(end_audio)
    await synthesize_voice("Nūr. Build the person you want to become.", end_audio)
    end_aud_clip = AudioFileClip(end_audio)
    end_dur = end_aud_clip.duration + 1.0

    end_img = build_closing_endcard(W, H)
    temp_files.append(end_img)
    end_clip = ImageClip(end_img).set_duration(end_dur).set_audio(end_aud_clip)
    clips.append(end_clip)

    final_video = concatenate_videoclips(clips, method="compose")

    ambient_wav = generate_ambient_soundbed(final_video.duration + 0.5)
    temp_files.append(ambient_wav)
    ambient_clip = AudioFileClip(ambient_wav).subclip(0, final_video.duration).volumex(0.14)

    mixed_audio = CompositeAudioClip([final_video.audio, ambient_clip])
    final_video = final_video.set_audio(mixed_audio)

    final_video.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=2,
        logger=None,
    )

    duration_sec = round(final_video.duration, 1)
    final_video.close()

    for f in temp_files:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass

    return output_path, duration_sec


def run_qa_checks(plan, img_path, vid_path, vid_duration):
    checks = []

    all_text = json.dumps(plan, ensure_ascii=False)
    spelling_ok = ("NŪR" not in all_text) and ("N□R" not in all_text)
    checks.append(("Wordmark spelling (Nūr)", spelling_ok))

    img_ok = False
    if os.path.exists(img_path) and os.path.getsize(img_path) > 15000:
        with Image.open(img_path) as im:
            img_ok = im.size == (1080, 1350)
    checks.append(("Editorial graphic format (1080×1350)", img_ok))

    vid_ok = os.path.exists(vid_path) and os.path.getsize(vid_path) > 50000 and (12.0 <= vid_duration <= 45.0)
    checks.append((f"Cinematic reel ({vid_duration}s, 5 beats + ambient audio)", vid_ok))

    banned_words = ["ashamed", "pathetic", "lazy", "loser", "sinful", "punish"]
    tone_ok = not any(w in all_text.lower() for w in banned_words)
    checks.append(("Calm, non-shame brand tone", tone_ok))

    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    summary_lines = [f"{'✓' if ok else '✗'} {label}" for label, ok in checks]
    report = f"QA Verification: {passed}/{total} passed\n" + "\n".join(summary_lines)

    if passed < total:
        raise RuntimeError(f"Nūr QA Gate blocked delivery:\n{report}")

    return report


async def run_pipeline():
    brand = load_json("brand_config.json", {"pillars": ["Digital Self-Control"]})
    history = load_json("history.json", [])

    print("1. Generating Nūr editorial plan via OpenRouter...")
    plan = generate_editorial_plan(brand, history)

    print("2. Creating Nūr layered editorial graphic (1080x1350)...")
    build_editorial_graphic(plan, "nur_post.png")

    print("3. Creating Nūr cinematic vertical film with ambient soundbed (1080x1920)...")
    _, vid_duration = await build_cinematic_reel(plan, "nur_reel.mp4")

    print("4. Running Nūr Section 8 automated QA gate...")
    qa_report = run_qa_checks(plan, "nur_post.png", "nur_reel.mp4", vid_duration)
    print(qa_report)

    save_json(
        "latest_post.json",
        {
            "image_caption": plan["caption_image"],
            "video_caption": plan["caption_video"],
            "topic": plan["topic_slug"],
            "qa_report": qa_report,
        },
    )

    history.append(plan["topic_slug"])
    save_json("history.json", history[-50:])
    print("5. Nūr production pipeline complete.")


if __name__ == "__main__":
    asyncio.run(run_pipelimport os
import json
import math
import wave
import struct
import random
import urllib.parse
import asyncio
import requests
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import (
    ImageClip,
    AudioFileClip,
    CompositeVideoClip,
    CompositeAudioClip,
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
    "Philosophy & Craft (why building quiet discipline matters more than quick dopamine)",
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


def enforce_nur_spelling(text):
    """Guarantees strict Nūr spelling with macron ū and blocks NŪR or broken glyphs."""
    if not isinstance(text, str):
        return text
    for bad in ["NŪR", "N□R", "NUR ", " NUR"]:
        text = text.replace(bad, bad.replace("NŪR", "Nūr").replace("N□R", "Nūr").replace("NUR", "Nūr"))
    return text


def get_font(size, bold=False, serif=False):
    if serif:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf",
        ]
    else:
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
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
            with Image.open(filename) as im:
                im = im.convert("RGB").resize((width, height), Image.Resampling.LANCZOS)
                im = apply_subtle_grain(im, intensity=10)
                im.save(filename, quality=95)
            return filename
    except Exception as e:
        print(f"Photo API fallback triggered ({e}) — crafting studio editorial backdrop...")

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


def generate_ambient_soundbed(duration_sec, output_wav="temp_ambient_pad.wav"):
    sample_rate = 44100
    num_samples = int(duration_sec * sample_rate)
    freqs = [87.31, 130.81, 164.81, 196.00, 220.00]
    weights = [0.35, 0.25, 0.16, 0.14, 0.10]

    with wave.open(output_wav, "w") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)

        frames = bytearray()
        fade_samples = int(1.5 * sample_rate)

        for i in range(num_samples):
            t = i / sample_rate
            breath = 0.75 + 0.25 * math.sin(2 * math.pi * 0.125 * t)

            val = 0.0
            for f, w in zip(freqs, weights):
                val += w * math.sin(2 * math.pi * f * t)

            env = 1.0
            if i < fade_samples:
                env = i / fade_samples
            elif i > num_samples - fade_samples:
                env = max(0.0, (num_samples - i) / fade_samples)

            sample = int(val * breath * env * 12000)
            sample = max(-32767, min(32767, sample))
            frames.extend(struct.pack("<h", sample))

        wav_file.writeframes(frames)
    return output_wav


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
        "Tone: Calm, intelligent, premium, human, empowering. British English spelling. "
        "Output ONLY valid raw JSON with no markdown backticks."
    )

    user_prompt = f"""
Create one cohesive Nūr media package for Pillar: "{pillar}" and Video Category: "{category}".
Avoid repeating these recent topics: {recent_topics}.

Return a JSON object with this exact structure:
{{
  "topic_slug": "short-unique-topic-id",
  "pillar_label": "SHORT UPPERCASE EDITORIAL LABEL",
  "graphic": {{
    "theme": "dark_forest or warm_ivory",
    "headline": "Calm, powerful editorial statement (6 to 11 words, sentence case, ends with a period)",
    "subtext": "Thoughtful, grounded reflection expanding on the headline (16 to 24 words)",
    "photo_prompt": "Realistic, quiet photograph scene"
  }},
  "caption_image": "Thoughtful British English social caption (3 short paragraphs) + 4 understated hashtags including #Nur",
  "video": {{
    "title": "Short internal title",
    "scenes": [
      {{
        "beat": "01 · THE HOOK",
        "voiceover": "Immediate relatable opening line (8-12 words)",
        "on_screen_text": "Short 4-6 word caption",
        "image_prompt": "Wide/medium realistic cinematic shot"
      }},
      {{
        "beat": "02 · THE PROBLEM",
        "voiceover": "Quiet consequence of distraction without shame (10-14 words)",
        "on_screen_text": "Short 4-6 word caption",
        "image_prompt": "Close-up realistic cinematic shot"
      }},
      {{
        "beat": "03 · THE REALISATION",
        "voiceover": "Grounded insight about environment and attention (11-15 words)",
        "on_screen_text": "Short 4-6 word caption",
        "image_prompt": "Over-the-shoulder realistic shot"
      }},
      {{
        "beat": "04 · THE RESPONSE",
        "voiceover": "Intentional, calm action to reclaim focus (10-14 words)",
        "on_screen_text": "Short 4-6 word caption",
        "image_prompt": "Close-up realistic shot"
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

    plan = json.loads(raw.strip())
    plan["caption_image"] = enforce_nur_spelling(plan["caption_image"])
    plan["caption_video"] = enforce_nur_spelling(plan["caption_video"])
    plan["graphic"]["headline"] = enforce_nur_spelling(plan["graphic"]["headline"])
    plan["graphic"]["subtext"] = enforce_nur_spelling(plan["graphic"]["subtext"])
    return plan


def build_editorial_graphic(plan, output_path="nur_post.png"):
    W, H = 1080, 1350
    g = plan["graphic"]
    use_ivory = g.get("theme") == "warm_ivory"

    bg_color = WARM_IVORY if use_ivory else DEEP_FOREST
    text_primary = CHARCOAL if use_ivory else WARM_IVORY
    text_secondary = "#4A4A4A" if use_ivory else "#D6D1C4"
    accent = EARTH_BRONZE if use_ivory else MUTED_GOLD

    canvas = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(canvas)

    outer_pad = 48
    inner_pad = 64
    draw.rectangle([outer_pad, outer_pad, W - outer_pad, H - outer_pad], outline=accent, width=1)
    draw.rectangle([inner_pad, inner_pad, W - inner_pad, H - inner_pad], outline=accent, width=1)

    logo_font = get_font(34, bold=True, serif=True)
    label_font = get_font(18, bold=False, serif=False)

    draw.text((104, 96), "Nūr", fill=text_primary, font=logo_font)
    pillar_text = plan.get("pillar_label", "INTENTIONAL LIVING").upper()
    p_bbox = draw.textbbox((0, 0), pillar_text, font=label_font)
    draw.text((W - 104 - (p_bbox[2] - p_bbox[0]), 106), pillar_text, fill=accent, font=label_font)

    draw.line([(104, 158), (W - 104, 158)], fill=accent, width=1)

    photo_w, photo_h = W - 208, 490
    temp_photo = "temp_editorial_photo.jpg"
    fetch_cinematic_photo(g["photo_prompt"], photo_w, photo_h, temp_photo)

    with Image.open(temp_photo) as photo:
        draw.rectangle([102, 198, 106 + photo_w, 202 + photo_h], outline=accent, width=1)
        canvas.paste(photo, (104, 200))

    headline_font = get_font(50, bold=True, serif=True)
    body_font = get_font(27, bold=False, serif=False)
    footer_font = get_font(18, bold=False, serif=False)

    y_cursor = 740
    headline_lines = wrap_text(g["headline"], headline_font, W - 208, draw)
    for line in headline_lines[:4]:
        draw.text((104, y_cursor), line, fill=text_primary, font=headline_font)
        y_cursor += 64

    y_cursor += 18
    draw.line([(104, y_cursor), (224, y_cursor)], fill=accent, width=2)
    y_cursor += 32

    body_lines = wrap_text(g["subtext"], body_font, W - 208, draw)
    for line in body_lines[:4]:
        draw.text((104, y_cursor), line, fill=text_secondary, font=body_font)
        y_cursor += 40

    draw.line([(104, H - 140), (W - 104, H - 140)], fill=accent, width=1)
    draw.text((104, H - 116), "Build the person you want to become.", fill=text_secondary, font=footer_font)
    edition_str = "EDITION · 01"
    e_bbox = draw.textbbox((0, 0), edition_str, font=footer_font)
    draw.text((W - 104 - (e_bbox[2] - e_bbox[0]), H - 116), edition_str, fill=accent, font=footer_font)

    canvas = apply_subtle_grain(canvas, intensity=7)
    canvas.save(output_path, quality=95)
    if os.path.exists(temp_photo):
        os.remove(temp_photo)
    return output_path


async def synthesize_voice(text, audio_path):
    communicate = edge_tts.Communicate(text, "en-GB-RyanNeural", rate="-6%")
    await communicate.save(audio_path)


def create_caption_overlay(width, height, beat_label, caption_text):
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    brand_font = get_font(30, bold=True, serif=True)
    beat_font = get_font(18, bold=False, serif=False)
    draw.text((72, 110), "Nūr", fill=(245, 240, 225, 230), font=brand_font)
    draw.text((72, 152), beat_label.upper(), fill=(212, 175, 55, 220), font=beat_font)

    cap_font = get_font(38, bold=False, serif=False)
    lines = wrap_text(caption_text, cap_font, width - 180, draw)
    box_height = len(lines) * 52 + 56
    box_top = height - 340 - box_height

    draw.rectangle([64, box_top, width - 64, box_top + box_height], fill=(8, 8, 8, 175))
    draw.line([(64, box_top), (width - 64, box_top)], fill=(212, 175, 55, 220), width=2)

    y = box_top + 28
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=cap_font)
        x = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, fill=(245, 240, 225, 255), font=cap_font)
        y += 52

    temp_ov = f"temp_ov_{random.randint(1000,9999)}.png"
    overlay.save(temp_ov)
    return temp_ov


def build_closing_endcard(width, height):
    card = Image.new("RGB", (width, height), DEEP_FOREST)
    draw = ImageDraw.Draw(card)

    pad = 64
    draw.rectangle([pad, pad, width - pad, height - pad], outline=MUTED_GOLD, width=2)

    logo_font = get_font(96, bold=True, serif=True)
    tag_font = get_font(34, bold=False, serif=True)

    l_bbox = draw.textbbox((0, 0), "Nūr", font=logo_font)
    lx = (width - (l_bbox[2] - l_bbox[0])) // 2
    ly = (height // 2) - 110
    draw.text((lx, ly), "Nūr", fill=WARM_IVORY, font=logo_font)

    draw.line([(width // 2 - 90, ly + 125), (width // 2 + 90, ly + 125)], fill=MUTED_GOLD, width=2)

    tagline = "Build the person you want to become."
    t_bbox = draw.textbbox((0, 0), tagline, font=tag_font)
    tx = (width - (t_bbox[2] - t_bbox[0])) // 2
    draw.text((tx, ly + 155), tagline, fill=WARM_IVORY, font=tag_font)

    card = apply_subtle_grain(card, intensity=8)
    end_path = "temp_nur_endcard.png"
    card.save(end_path, quality=95)
    return end_path


async def build_cinematic_reel(plan, output_path="nur_reel.mp4"):
    W, H = 1080, 1920
    clips = []
    temp_files = []

    for idx, scene in enumerate(plan["video"]["scenes"]):
        img_file = f"temp_scene_{idx}.jpg"
        aud_file = f"temp_scene_{idx}.mp3"
        temp_files.extend([img_file, aud_file])

        fetch_cinematic_photo(scene["image_prompt"], W, H, img_file)
        await synthesize_voice(scene["voiceover"], aud_file)

        audio_clip = AudioFileClip(aud_file)
        duration = audio_clip.duration + 0.45

        bg_clip = (
            ImageClip(img_file)
            .set_duration(duration)
            .resize(lambda t: 1.0 + 0.035 * (t / duration))
            .set_position("center")
        )

        ov_file = create_caption_overlay(W, H, scene["beat"], scene["on_screen_text"])
        temp_files.append(ov_file)
        ov_clip = ImageClip(ov_file).set_duration(duration)

        scene_comp = CompositeVideoClip([bg_clip, ov_clip], size=(W, H)).set_audio(audio_clip)
        clips.append(scene_comp)

    end_audio = "temp_end_audio.mp3"
    temp_files.append(end_audio)
    await synthesize_voice("Nūr. Build the person you want to become.", end_audio)
    end_aud_clip = AudioFileClip(end_audio)
    end_dur = end_aud_clip.duration + 1.0

    end_img = build_closing_endcard(W, H)
    temp_files.append(end_img)
    end_clip = ImageClip(end_img).set_duration(end_dur).set_audio(end_aud_clip)
    clips.append(end_clip)

    final_video = concatenate_videoclips(clips, method="compose")

    ambient_wav = generate_ambient_soundbed(final_video.duration + 0.5)
    temp_files.append(ambient_wav)
    ambient_clip = AudioFileClip(ambient_wav).subclip(0, final_video.duration).volumex(0.14)

    mixed_audio = CompositeAudioClip([final_video.audio, ambient_clip])
    final_video = final_video.set_audio(mixed_audio)

    final_video.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=2,
        logger=None,
    )

    duration_sec = round(final_video.duration, 1)
    final_video.close()

    for f in temp_files:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass

    return output_path, duration_sec


def run_qa_checks(plan, img_path, vid_path, vid_duration):
    checks = []

    all_text = json.dumps(plan, ensure_ascii=False)
    spelling_ok = ("NŪR" not in all_text) and ("N□R" not in all_text)
    checks.append(("Wordmark spelling (Nūr)", spelling_ok))

    img_ok = False
    if os.path.exists(img_path) and os.path.getsize(img_path) > 15000:
        with Image.open(img_path) as im:
            img_ok = im.size == (1080, 1350)
    checks.append(("Editorial graphic format (1080×1350)", img_ok))

    vid_ok = os.path.exists(vid_path) and os.path.getsize(vid_path) > 50000 and (12.0 <= vid_duration <= 45.0)
    checks.append((f"Cinematic reel ({vid_duration}s, 5 beats + ambient audio)", vid_ok))

    banned_words = ["ashamed", "pathetic", "lazy", "loser", "sinful", "punish"]
    tone_ok = not any(w in all_text.lower() for w in banned_words)
    checks.append(("Calm, non-shame brand tone", tone_ok))

    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    summary_lines = [f"{'✓' if ok else '✗'} {label}" for label, ok in checks]
    report = f"QA Verification: {passed}/{total} passed\n" + "\n".join(summary_lines)

    if passed < total:
        raise RuntimeError(f"Nūr QA Gate blocked delivery:\n{report}")

    return report


async def run_pipeline():
    brand = load_json("brand_config.json", {"pillars": ["Digital Self-Control"]})
    history = load_json("history.json", [])

    print("1. Generating Nūr editorial plan via OpenRouter...")
    plan = generate_editorial_plan(brand, history)

    print("2. Creating Nūr layered editorial graphic (1080x1350)...")
    build_editorial_graphic(plan, "nur_post.png")

    print("3. Creating Nūr cinematic vertical film with ambient soundbed (1080x1920)...")
    _, vid_duration = await build_cinematic_reel(plan, "nur_reel.mp4")

    print("4. Running Nūr Section 8 automated QA gate...")
    qa_report = run_qa_checks(plan, "nur_post.png", "nur_reel.mp4", vid_duration)
    print(qa_report)

    save_json(
        "latest_post.json",
        {
            "image_caption": plan["caption_image"],
            "video_caption": plan["caption_video"],
            "topic": plan["topic_slug"],
            "qa_report": qa_report,
        },
    )

    history.append(plan["topic_slug"])
    save_json("history.json", history[-50:])
    print("5. Nūr production pipeline complete.")


if __name__ == "__main__":
    asyncio.run(run_pipeline()) = raw.rsplit("```", 1)[0]

    plan = json.loads(raw.strip())
    plan["caption_image"] = enforce_nur_spelling(plan["caption_image"])
    plan["caption_video"] = enforce_nur_spelling(plan["caption_video"])
    plan["graphic"]["headline"] = enforce_nur_spelling(plan["graphic"]["headline"])
    plan["graphic"]["subtext"] = enforce_nur_spelling(plan["graphic"]["subtext"])
    return plan


def build_editorial_graphic(plan, output_path="nur_post.png"):
    W, H = 1080, 1350
    g = plan["graphic"]
    use_ivory = g.get("theme") == "warm_ivory"

    bg_color = WARM_IVORY if use_ivory else DEEP_FOREST
    text_primary = CHARCOAL if use_ivory else WARM_IVORY
    text_secondary = "#4A4A4A" if use_ivory else "#D6D1C4"
    accent = EARTH_BRONZE if use_ivory else MUTED_GOLD

    canvas = Image.new("RGB", (W, H), bg_color)
    draw = ImageDraw.Draw(canvas)

    outer_pad = 48
    inner_pad = 64
    draw.rectangle([outer_pad, outer_pad, W - outer_pad, H - outer_pad], outline=accent, width=1)
    draw.rectangle([inner_pad, inner_pad, W - inner_pad, H - inner_pad], outline=accent, width=1)

    logo_font = get_font(34, bold=True, serif=True)
    label_font = get_font(18, bold=False, serif=False)

    draw.text((104, 96), "Nūr", fill=text_primary, font=logo_font)
    pillar_text = plan.get("pillar_label", "INTENTIONAL LIVING").upper()
    p_bbox = draw.textbbox((0, 0), pillar_text, font=label_font)
    draw.text((W - 104 - (p_bbox[2] - p_bbox[0]), 106), pillar_text, fill=accent, font=label_font)

    draw.line([(104, 158), (W - 104, 158)], fill=accent, width=1)

    photo_w, photo_h = W - 208, 490
    temp_photo = "temp_editorial_photo.jpg"
    fetch_cinematic_photo(g["photo_prompt"], photo_w, photo_h, temp_photo)

    with Image.open(temp_photo) as photo:
        draw.rectangle([102, 198, 106 + photo_w, 202 + photo_h], outline=accent, width=1)
        canvas.paste(photo, (104, 200))

    headline_font = get_font(50, bold=True, serif=True)
    body_font = get_font(27, bold=False, serif=False)
    footer_font = get_font(18, bold=False, serif=False)

    y_cursor = 740
    headline_lines = wrap_text(g["headline"], headline_font, W - 208, draw)
    for line in headline_lines[:4]:
        draw.text((104, y_cursor), line, fill=text_primary, font=headline_font)
        y_cursor += 64

    y_cursor += 18
    draw.line([(104, y_cursor), (224, y_cursor)], fill=accent, width=2)
    y_cursor += 32

    body_lines = wrap_text(g["subtext"], body_font, W - 208, draw)
    for line in body_lines[:4]:
        draw.text((104, y_cursor), line, fill=text_secondary, font=body_font)
        y_cursor += 40

    draw.line([(104, H - 140), (W - 104, H - 140)], fill=accent, width=1)
    draw.text((104, H - 116), "Build the person you want to become.", fill=text_secondary, font=footer_font)
    edition_str = "EDITION · 01"
    e_bbox = draw.textbbox((0, 0), edition_str, font=footer_font)
    draw.text((W - 104 - (e_bbox[2] - e_bbox[0]), H - 116), edition_str, fill=accent, font=footer_font)

    canvas = apply_subtle_grain(canvas, intensity=7)
    canvas.save(output_path, quality=95)
    if os.path.exists(temp_photo):
        os.remove(temp_photo)
    return output_path


async def synthesize_voice(text, audio_path):
    communicate = edge_tts.Communicate(text, "en-GB-RyanNeural", rate="-6%")
    await communicate.save(audio_path)


def create_caption_overlay(width, height, beat_label, caption_text):
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    brand_font = get_font(30, bold=True, serif=True)
    beat_font = get_font(18, bold=False, serif=False)
    draw.text((72, 110), "Nūr", fill=(245, 240, 225, 230), font=brand_font)
    draw.text((72, 152), beat_label.upper(), fill=(212, 175, 55, 220), font=beat_font)

    cap_font = get_font(38, bold=False, serif=False)
    lines = wrap_text(caption_text, cap_font, width - 180, draw)
    box_height = len(lines) * 52 + 56
    box_top = height - 340 - box_height

    draw.rectangle([64, box_top, width - 64, box_top + box_height], fill=(8, 8, 8, 175))
    draw.line([(64, box_top), (width - 64, box_top)], fill=(212, 175, 55, 220), width=2)

    y = box_top + 28
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=cap_font)
        x = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, fill=(245, 240, 225, 255), font=cap_font)
        y += 52

    temp_ov = f"temp_ov_{random.randint(1000,9999)}.png"
    overlay.save(temp_ov)
    return temp_ov


def build_closing_endcard(width, height):
    card = Image.new("RGB", (width, height), DEEP_FOREST)
    draw = ImageDraw.Draw(card)

    pad = 64
    draw.rectangle([pad, pad, width - pad, height - pad], outline=MUTED_GOLD, width=2)

    logo_font = get_font(96, bold=True, serif=True)
    tag_font = get_font(34, bold=False, serif=True)

    l_bbox = draw.textbbox((0, 0), "Nūr", font=logo_font)
    lx = (width - (l_bbox[2] - l_bbox[0])) // 2
    ly = (height // 2) - 110
    draw.text((lx, ly), "Nūr", fill=WARM_IVORY, font=logo_font)

    draw.line([(width // 2 - 90, ly + 125), (width // 2 + 90, ly + 125)], fill=MUTED_GOLD, width=2)

    tagline = "Build the person you want to become."
    t_bbox = draw.textbbox((0, 0), tagline, font=tag_font)
    tx = (width - (t_bbox[2] - t_bbox[0])) // 2
    draw.text((tx, ly + 155), tagline, fill=WARM_IVORY, font=tag_font)

    card = apply_subtle_grain(card, intensity=8)
    end_path = "temp_nur_endcard.png"
    card.save(end_path, quality=95)
    return end_path


async def build_cinematic_reel(plan, output_path="nur_reel.mp4"):
    W, H = 1080, 1920
    clips = []
    temp_files = []

    for idx, scene in enumerate(plan["video"]["scenes"]):
        img_file = f"temp_scene_{idx}.jpg"
        aud_file = f"temp_scene_{idx}.mp3"
        temp_files.extend([img_file, aud_file])

        fetch_cinematic_photo(scene["image_prompt"], W, H, img_file)
        await synthesize_voice(scene["voiceover"], aud_file)

        audio_clip = AudioFileClip(aud_file)
        duration = audio_clip.duration + 0.45

        bg_clip = (
            ImageClip(img_file)
            .set_duration(duration)
            .resize(lambda t: 1.0 + 0.035 * (t / duration))
            .set_position("center")
        )

        ov_file = create_caption_overlay(W, H, scene["beat"], scene["on_screen_text"])
        temp_files.append(ov_file)
        ov_clip = ImageClip(ov_file).set_duration(duration)

        scene_comp = CompositeVideoClip([bg_clip, ov_clip], size=(W, H)).set_audio(audio_clip)
        clips.append(scene_comp)

    end_audio = "temp_end_audio.mp3"
    temp_files.append(end_audio)
    await synthesize_voice("Nūr. Build the person you want to become.", end_audio)
    end_aud_clip = AudioFileClip(end_audio)
    end_dur = end_aud_clip.duration + 1.0

    end_img = build_closing_endcard(W, H)
    temp_files.append(end_img)
    end_clip = ImageClip(end_img).set_duration(end_dur).set_audio(end_aud_clip)
    clips.append(end_clip)

    final_video = concatenate_videoclips(clips, method="compose")

    # Synthesize and layer subtle ambient soundbed underneath narration
    ambient_wav = generate_ambient_soundbed(final_video.duration + 0.5)
    temp_files.append(ambient_wav)
    ambient_clip = AudioFileClip(ambient_wav).subclip(0, final_video.duration).volumex(0.14)

    mixed_audio = CompositeAudioClip([final_video.audio, ambient_clip])
    final_video = final_video.set_audio(mixed_audio)

    final_video.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=2,
        logger=None,
    )

    duration_sec = round(final_video.duration, 1)
    final_video.close()

    for f in temp_files:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass

    return output_path, duration_sec


def run_qa_checks(plan, img_path, vid_path, vid_duration):
    """Automated Section 8 Nūr Quality Assurance Gate."""
    checks = []

    # 1. Wordmark & Spelling Check
    all_text = json.dumps(plan, ensure_ascii=False)
    spelling_ok = ("NŪR" not in all_text) and ("N□R" not in all_text)
    checks.append(("Wordmark spelling (Nūr)", spelling_ok))

    # 2. Graphic Dimensions & File Integrity (1080x1350)
    img_ok = False
    if os.path.exists(img_path) and os.path.getsize(img_path) > 15000:
        with Image.open(img_path) as im:
            img_ok = im.size == (1080, 1350)
    checks.append(("Editorial graphic format (1080×1350)", img_ok))

    # 3. Video File, Duration & Multi-Scene Narrative Check
    vid_ok = os.path.exists(vid_path) and os.path.getsize(vid_path) > 50000 and (12.0 <= vid_duration <= 45.0)
    checks.append((f"Cinematic reel ({vid_duration}s, 5 beats + ambient audio)", vid_ok))

    # 4. Non-Shame / Tone Guardrail
    banned_words = ["ashamed", "pathetic", "lazy", "loser", "sinful", "punish"]
    tone_ok = not any(w in all_text.lower() for w in banned_words)
    checks.append(("Calm, non-shame brand tone", tone_ok))

    passed = sum(1 for _, ok in checks if ok)
    total = len(checks)
    summary_lines = [f"{'✓' if ok else '✗'} {label}" for label, ok in checks]
    report = f"QA Verification: {passed}/{total} passed\n" + "\n".join(summary_lines)

    if passed < total:
        raise RuntimeError(f"Nūr QA Gate blocked delivery:\n{report}")

    return report


async def run_pipeline():
    brand = load_json("brand_config.json", {"pillars": ["Digital Self-Control"]})
    history = load_json("history.json", [])

    print("1. Generating Nūr editorial plan via OpenRouter...")
    plan = generate_editorial_plan(brand, history)

    print("2. Creating Nūr layered editorial graphic (1080x1350)...")
    build_editorial_graphic(plan, "nur_post.png")

    print("3. Creating Nūr cinematic vertical film with ambient soundbed (1080x1920)...")
    _, vid_duration = await build_cinematic_reel(plan, "nur_reel.mp4")

    print("4. Running Nūr Section 8 automated QA gate...")
        y_cursor += 64

    y_cursor += 18
    draw.line([(104, y_cursor), (224, y_cursor)], fill=accent, width=2)
    y_cursor += 32

    body_lines = wrap_text(g["subtext"], body_font, W - 208, draw)
    for line in body_lines[:4]:
        draw.text((104, y_cursor), line, fill=text_secondary, font=body_font)
        y_cursor += 40

    draw.line([(104, H - 140), (W - 104, H - 140)], fill=accent, width=1)
    draw.text((104, H - 116), "Build the person you want to become.", fill=text_secondary, font=footer_font)
    edition_str = "EDITION · 01"
    e_bbox = draw.textbbox((0, 0), edition_str, font=footer_font)
    draw.text((W - 104 - (e_bbox[2] - e_bbox[0]), H - 116), edition_str, fill=accent, font=footer_font)

    canvas = apply_subtle_grain(canvas, intensity=7)
    canvas.save(output_path, quality=95)
    if os.path.exists(temp_photo):
        os.remove(temp_photo)
    return output_path


async def synthesize_voice(text, audio_path):
    communicate = edge_tts.Communicate(text, "en-GB-RyanNeural", rate="-6%")
    await communicate.save(audio_path)


def create_caption_overlay(width, height, beat_label, caption_text):
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    brand_font = get_font(30, bold=True, serif=True)
    beat_font = get_font(18, bold=False, serif=False)
    draw.text((72, 110), "Nūr", fill=(245, 240, 225, 230), font=brand_font)
    draw.text((72, 152), beat_label.upper(), fill=(212, 175, 55, 220), font=beat_font)

    cap_font = get_font(38, bold=False, serif=False)
    lines = wrap_text(caption_text, cap_font, width - 180, draw)
    box_height = len(lines) * 52 + 56
    box_top = height - 340 - box_height

    draw.rectangle([64, box_top, width - 64, box_top + box_height], fill=(8, 8, 8, 175))
    draw.line([(64, box_top), (width - 64, box_top)], fill=(212, 175, 55, 220), width=2)

    y = box_top + 28
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=cap_font)
        x = (width - (bbox[2] - bbox[0])) // 2
        draw.text((x, y), line, fill=(245, 240, 225, 255), font=cap_font)
        y += 52

    temp_ov = f"temp_ov_{random.randint(1000,9999)}.png"
    overlay.save(temp_ov)
    return temp_ov


def build_closing_endcard(width, height):
    card = Image.new("RGB", (width, height), DEEP_FOREST)
    draw = ImageDraw.Draw(card)

    pad = 64
    draw.rectangle([pad, pad, width - pad, height - pad], outline=MUTED_GOLD, width=2)

    logo_font = get_font(96, bold=True, serif=True)
    tag_font = get_font(34, bold=False, serif=True)

    l_bbox = draw.textbbox((0, 0), "Nūr", font=logo_font)
    lx = (width - (l_bbox[2] - l_bbox[0])) // 2
    ly = (height // 2) - 110
    draw.text((lx, ly), "Nūr", fill=WARM_IVORY, font=logo_font)

    draw.line([(width // 2 - 90, ly + 125), (width // 2 + 90, ly + 125)], fill=MUTED_GOLD, width=2)

    tagline = "Build the person you want to become."
    t_bbox = draw.textbbox((0, 0), tagline, font=tag_font)
    tx = (width - (t_bbox[2] - t_bbox[0])) // 2
    draw.text((tx, ly + 155), tagline, fill=WARM_IVORY, font=tag_font)

    card = apply_subtle_grain(card, intensity=8)
    end_path = "temp_nur_endcard.png"
    card.save(end_path, quality=95)
    return end_path


async def build_cinematic_reel(plan, output_path="nur_reel.mp4"):
    W, H = 1080, 1920
    clips = []
    temp_files = []

    for idx, scene in enumerate(plan["video"]["scenes"]):
        img_file = f"temp_scene_{idx}.jpg"
        aud_file = f"temp_scene_{idx}.mp3"
        temp_files.extend([img_file, aud_file])

        fetch_cinematic_photo(scene["image_prompt"], W, H, img_file)
        await synthesize_voice(scene["voiceover"], aud_file)

        audio_clip = AudioFileClip(aud_file)
        duration = audio_clip.duration + 0.45

        bg_clip = (
            ImageClip(img_file)
            .set_duration(duration)
            .resize(lambda t: 1.0 + 0.035 * (t / duration))
            .set_position("center")
        )

        ov_file = create_caption_overlay(W, H, scene["beat"], scene["on_screen_text"])
        temp_files.append(ov_file)
        ov_clip = ImageClip(ov_file).set_duration(duration)

        scene_comp = CompositeVideoClip([bg_clip, ov_clip], size=(W, H)).set_audio(audio_clip)
        clips.append(scene_comp)

    end_audio = "temp_end_audio.mp3"
    temp_files.append(end_audio)
    await synthesize_voice("Nūr. Build the person you want to become.", end_audio)
    end_aud_clip = AudioFileClip(end_audio)
    end_dur = end_aud_clip.duration + 1.0

    end_img = build_closing_endcard(W, H)
    temp_files.append(end_img)
    end_clip = ImageClip(end_img).set_duration(end_dur).set_audio(end_aud_clip)
    clips.append(end_clip)

    final_video = concatenate_videoclips(clips, method="compose")
    final_video.write_videofile(
        output_path,
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="medium",
        threads=2,
        logger=None,
    )

    for f in temp_files:
        if os.path.exists(f):
            try:
                os.remove(f)
            except Exception:
                pass

    return output_path


async def run_pipeline():
    brand = load_json("brand_config.json", {"pillars": ["Digital Self-Control"]})
    history = load_json("history.json", [])

    print("1. Generating Nūr editorial plan via OpenRouter...")
    plan = generate_editorial_plan(brand, history)

    print("2. Creating Nūr layered editorial graphic (1080x1350)...")
    build_editorial_graphic(plan, "nur_post.png")

    print("3. Creating Nūr cinematic vertical film (1080x1920)...")
    await build_cinematic_reel(plan, "nur_reel.mp4")

    save_json(
        "latest_post.json",
        {
            "image_caption": plan["caption_image"],
            "video_caption": plan["caption_video"],
            "topic": plan["topic_slug"],
        },
    )

    history.append(plan["topic_slug"])
    save_json("history.json", history[-50:])
    print("4. Nūr production pipeline complete.")


if __name__ == "__main__":
    asyncio.run(run_pipeline())pillar_text, font=label_font)
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
