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

WIDTH = 1080
HEIGHT = 1920
FPS = 24

DEEP_FOREST = "#064E3B"
LIVING_GREEN = "#0B5D3B"
NEAR_BLACK = "#080808"
WARM_IVORY = "#F5F0E1"
MUTED_GOLD = "#D4AF37"
EARTH_BRONZE = "#A68A64"
CHARCOAL = "#1C1C1C"

WORDMARK = "Nūr"
TAGLINE = "Build the person you want to become."

VIDEO_CATEGORIES = [
    "Awareness and digital habits",
    "Practical education and focus",
    "Recovery without shame",
    "Intentional living",
    "Discipline and personal growth",
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
            f"Command failed: {' '.join(map(str, command))}\n"
            f"{result.stderr[-3000:]}"
        )

    return result.stdout.strip()


def require_tools():
    for tool in ("ffmpeg", "ffprobe"):
        if shutil.which(tool) is None:
            raise RuntimeError(f"{tool} is not installed.")


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
    if serif:
        filename = (
            "DejaVuSerif-Bold.ttf"
            if bold else "DejaVuSerif.ttf"
        )
    else:
        filename = (
            "DejaVuSans-Bold.ttf"
            if bold else "DejaVuSans.ttf"
        )

    candidates = [
        f"/usr/share/fonts/truetype/dejavu/{filename}",
        f"/usr/share/fonts/dejavu/{filename}",
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
        bounds = draw.textbbox(
            (0, 0),
            candidate,
            font=selected_font,
        )

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

    return (
        value.replace("NŪR", "Nūr")
        .replace("NUR", "Nūr")
        .replace("N□R", "Nūr")
    )


def generate_photo(prompt, width, height, destination):
    full_prompt = (
        f"{prompt}. Premium realistic editorial photography, "
        "cinematic natural lighting, believable human environments, "
        "authentic materials and detailed surroundings, "
        "deep forest green and warm neutral colour grading, "
        "35mm film character, careful composition, "
        "no text, no typography, no logos, no watermarks, "
        "no green-screen background."
    )

    encoded = urllib.parse.quote(full_prompt)
    seed = random.randint(10000, 99999999)

    url = (
        f"https://image.pollinations.ai/prompt/{encoded}"
        f"?width={width}&height={height}"
        f"&seed={seed}&nologo=true"
    )

    response = requests.get(url, timeout=120)
    response.raise_for_status()

    if len(response.content) < 12000:
        raise RuntimeError("Image service returned an invalid image.")

    destination = Path(destination)
    destination.write_bytes(response.content)

    try:
        with Image.open(destination) as image:
            image = ImageOps.fit(
                image.convert("RGB"),
                (width, height),
                method=Image.Resampling.LANCZOS,
            )
            image.save(
                destination,
                format="JPEG",
                quality=94,
                optimize=True,
            )
    except Exception as exc:
        destination.unlink(missing_ok=True)
        raise RuntimeError("Could not process generated image.") from exc

    return destination


def generate_editorial_plan(brand, history):
    api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()

    if not api_key:
        raise RuntimeError("Missing OPENROUTER_API_KEY secret.")

    pillars = brand.get(
        "pillars",
        ["Digital Self-Control"],
    )

    pillar = random.choice(pillars)
    category = random.choice(VIDEO_CATEGORIES)
    recent = ", ".join(history[-15:]) if history else "None"

    system_prompt = """
You are the editorial director for Nūr.

Always spell the brand exactly as Nūr.
Never write NŪR or NUR as the brand name.

Nūr supports self-control, protection, recovery
and personal growth.

Its philosophy is privacy-first, non-judgemental
and user-controlled.

Never shame people or induce guilt.
Never use fear-based marketing.
Never invent statistics.
Never fabricate religious quotations.
Never claim unverified app features exist.

Use British English.
Be calm, intelligent, precise and human.
Return valid JSON only.
Do not use Markdown fences.
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
            "HTTP-Referer": (
                "https://github.com/"
                "hassantaiwo866-dotcom/nur-social-ai"
            ),
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
        timeout=90,
    )

    response.raise_for_status()

    raw = response.json()["choices"][0]["message"]["content"].strip()

    if raw.startswith("```"):
        raw = raw.split("\n", 1)[-1]
        raw = raw.rsplit("```", 1)[0]

    plan = json.loads(raw.strip())

    required = [
        "topic_slug",
        "pillar_label",
        "graphic",
        "caption_image",
        "video",
        "caption_video",
    ]

    for key in required:
        if key not in plan:
            raise ValueError(f"Missing editorial field: {key}")

    scenes = plan["video"].get("scenes", [])

    if len(scenes) != 4:
        raise ValueError("Exactly four video scenes are required.")

    for scene in scenes:
        for key in (
            "beat",
            "voiceover",
            "on_screen_text",
            "image_prompt",
        ):
            if not scene.get(key):
                raise ValueError(f"Scene is missing {key}.")

    plan["caption_image"] = enforce_wordmark(plan["caption_image"])
    plan["caption_video"] = enforce_wordmark(plan["caption_video"])
    plan["graphic"]["headline"] = enforce_wordmark(
        plan["graphic"]["headline"]
    )
    plan["graphic"]["subtext"] = enforce_wordmark(
        plan["graphic"]["subtext"]
    )

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

    draw.rectangle(
        (48, 48, 1032, 1302),
        outline=accent,
        width=2,
    )

    logo_font = font(38, serif=True, bold=True)
    label_font = font(17)
    headline_font = font(49, serif=True, bold=True)
    body_font = font(26)
    footer_font = font(17)

    draw.text(
        (104, 88),
        WORDMARK,
        fill=primary,
        font=logo_font,
    )

    label = str(
        plan.get("pillar_label", "INTENTIONAL LIVING")
    ).upper()

    label_bounds = draw.textbbox(
        (0, 0),
        label,
        font=label_font,
    )

    draw.text(
        (976 - (label_bounds[2] - label_bounds[0]), 105),
        label,
        fill=accent,
        font=label_font,
    )

    draw.line(
        (104, 158, 976, 158),
        fill=accent,
        width=2,
    )

    with Image.open(photo_path) as photo:
        photo = ImageOps.fit(
            photo.convert("RGB"),
            (872, 440),
            method=Image.Resampling.LANCZOS,
        )
        canvas.paste(photo, (104, 190))

    y = 680

    headline_lines = wrap_text(
        graphic["headline"],
        headline_font,
        draw,
        872,
    )

    for line in headline_lines[:3]:
        draw.text(
            (104, y),
            line,
            fill=primary,
            font=headline_font,
        )
        y += 61

    y += 15

    draw.line(
        (104, y, 220, y),
        fill=accent,
        width=3,
    )

    y += 28

    body_lines = wrap_text(
        graphic["subtext"],
        body_font,
        draw,
        872,
    )

    for line in body_lines[:3]:
        draw.text(
            (104, y),
            line,
            fill=secondary,
            font=body_font,
        )
        y += 39

    draw.line(
        (104, 1190, 976, 1190),
        fill=accent,
        width=1,
    )

    draw.text(
        (104, 1210),
        TAGLINE,
        fill=secondary,
        font=footer_font,
    )

    edition = "Nūr EDITORIAL"
    edition_bounds = draw.textbbox(
        (0, 0),
        edition,
        font=footer_font,
    )

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
        bounds = draw.textbbox(
            (0, 0),
            line,
            font=caption_font,
        )

        x = (WIDTH - (bounds[2] - bounds[0])) // 2

        draw.text(
            (x, y),
            line,
            fill=(245, 240, 225, 255),
            font=caption_font,
        )

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


def make_video_segment(
    frame_path,
    audio_path,
    output_path,
    duration,
    zoom=True,
):
    if zoom:
        video_filter = (
            "zoompan=z='min(zoom+0.00035,1.035)':"
            "d=1:s=1080x1920:fps=24,"
            "format=yuv420p"
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
                weight * math.sin(
                    2 * math.pi * frequency * t
                )
                for frequency, weight in zip(
                    frequencies,
                    weights,
                )
            )

            envelope = 1.0

            if index < fade:
                envelope = index / fade
            elif index > total_samples - fade:
                envelope = max(
                    0.0,
                    (total_samples - index) / fade,
                )

            sample = int(value * envelope * 3500)
            sample = max(-32767, min(32767, sample))

            block.extend(struct.pack("<h", sample))

            if len(block) >= 65536:
                wav.writeframes(block)
                block.clear()

        if block:
            wav.writeframes(block)


def create_end_card(destination):
    image = Image.new(
        "RGB",
        (WIDTH, HEIGHT),
        DEEP_FOREST,
    )

    draw = ImageDraw.Draw(image)

    draw.rectangle(
        (64, 64, WIDTH - 64, HEIGHT - 64),
        outline=MUTED_GOLD,
        width=3,
    )

    logo_font = font(112, serif=True, bold=True)
    tagline_font = font(38, serif=True)

    logo_bounds = draw.textbbox(
        (0, 0),
        WORDMARK,
        font=logo_font,
    )

    logo_x = (
        WIDTH - (logo_bounds[2] - logo_bounds[0])
    ) // 2

    draw.text(
        (logo_x, 790),
        WORDMARK,
        fill=WARM_IVORY,
        font=logo_font,
    )

    draw.line(
        (
            WIDTH // 2 - 100,
            940,
            WIDTH // 2 + 100,
            940,
        ),
        fill=MUTED_GOLD,
        width=3,
    )

    tagline_bounds = draw.textbbox(
        (0, 0),
        TAGLINE,
        font=tagline_font,
    )

    tagline_x = (
        WIDTH - (tagline_bounds[2] - tagline_bounds[0])
    ) // 2

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
        failures.append("Video is missing or too small.")

    if video_path.exists():
        duration = probe_duration(video_path)

        if not 12 <= duration <= 60:
            failures.append(
                f"Unexpected video duration: {duration:.1f}s."
            )

    all_text = json.dumps(plan, ensure_ascii=False)

    if "NŪR" in all_text or "N□R" in all_text:
        failures.append("Incorrect brand spelling found.")

    harmful_terms = [
        "pathetic",
        "loser",
        "worthless",
        "lazy",
        "punish yourself",
        "you should be ashamed",
    ]

    lowered = all_text.lower()

    for term in harmful_terms:
        if term in lowered:
            failures.append(
                f"Potentially shaming language found: {term}"
            )

    if failures:
        raise RuntimeError(
            "Quality checks failed:\n- "
            + "\n- ".join(failures)
        )

    return {
        "status": "passed",
        "checks": [
            "Editorial image dimensions",
            "Video file and duration",
            "Generated text brand spelling",
            "Basic non-shaming language check",
        ],
        "manual_review_required": True,
        "manual_review_note": (
            "Automated checks cannot reliably detect "
            "watermarks, poor composition or visual defects. "
            "Review both assets before publishing."
        ),
    }


async def run_pipeline():
    require_tools()

    brand = load_json(
        ROOT / "brand_config.json",
        {"pillars": ["Digital Self-Control"]},
    )

    history = load_json(ROOT / "history.json", [])

    if not isinstance(history, list):
        history = []

    print("1. Creating editorial plan...")

    plan = generate_editorial_plan(brand, history)

    with tempfile.TemporaryDirectory(
        prefix="nur_media_"
    ) as temporary_directory:

        temp = Path(temporary_directory)

        print("2. Generating editorial photograph...")

        graphic_photo = generate_photo(
            plan["graphic"]["photo_prompt"],
            872,
            440,
            temp / "graphic_photo.jpg",
        )

        print("3. Building editorial graphic...")

        image_path = OUTPUT / "nur_post.png"

        build_editorial_graphic(
            plan,
            image_path,
            graphic_photo,
        )

        print("4. Producing cinematic scenes...")

        segments = []

        for index, scene in enumerate(
            plan["video"]["scenes"]
        ):
            print(f"Scene {index + 1}/4")

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

            await make_voiceover(
                scene["voiceover"],
                audio,
            )

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

        end_card = create_end_card(
            temp / "end_card.jpg"
        )

        end_audio = temp / "end_voice.mp3"

        await make_voiceover(
            "Nūr. Build the person you want to become.",
            end_audio,
        )

        end_duration = probe_duration(end_audio) + 1.2

        end_segment = temp / "end_segment.mp4"

        make_video_segment(
            end_card,
            end_audio,
            end_segment,
            end_duration,
            zoom=False,
        )

        segments.append(end_segment)

        print("6. Combining cinematic scenes...")

        concat_list = temp / "segments.txt"

        concat_list.write_text(
            "".join(
                f"file '{segment.as_posix()}'\n"
                for segment in segments
            ),
            encoding="utf-8",
        )

        raw_video = temp / "combined.mp4"

        run_command([
            "ffmpeg", "-y",
            "-f", "concat",
            "-safe", "0",
            "-i", str(concat_list),
            "-c:v", "libx264",
            "-preset", "medium",
            "-crf", "19",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            str(raw_video),
        ])

        duration = probe_duration(raw_video)

        print("7. Adding ambient sound...")

        ambient = temp / "ambient.wav"

        make_ambient_sound(
            duration,
            ambient,
        )

        video_path = OUTPUT / "nur_reel.mp4"

        run_command([
            "ffmpeg", "-y",
            "-i", str(raw_video),
            "-i", str(ambient),
            "-filter_complex",
            "[1:a]volume=0.12[bg];"
            "[0:a][bg]amix=inputs=2:duration=first:"
            "dropout_transition=2[a]",
            "-map", "0:v:0",
            "-map", "[a]",
            "-c:v", "copy",
            "-c:a", "aac",
            "-b:a", "192k",
            "-shortest",
            str(video_path),
        ])

        print("8. Running quality checks...")

        qa = run_qa(
            image_path,
            video_path,
            plan,
        )

        save_json(
            OUTPUT / "latest_post.json",
            {
                "topic": plan["topic_slug"],
                "image_caption": plan["caption_image"],
                "video_caption": plan["caption_video"],
                "qa": qa,
            },
        )

        history.append(plan["topic_slug"])

        save_json(
            ROOT / "history.json",
            history[-50:],
        )

        print("Nūr media generation completed.")
        print(f"Image: {image_path}")
        print(f"Video: {video_path}")
        print("Manual review is required before publishing.")


if __name__ == "__main__":
    asyncio.run(run_pipeline())
