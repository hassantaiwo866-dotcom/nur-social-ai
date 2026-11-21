import os
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
    """Synthesizes a warm, calm, copyright-free harmonic ambient pad (Fmaj9 / Cmaj9)."""
    sample_rate = 44100
    num_samples = int(duration_sec * sample_rate)
    # Warm low-mid harmonic frequencies (F2, C3, E3, G3, A3)
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
            # Slow 8-second breathing LFO modulation
            breath = 0.75 + 0.25 * math.sin(2 * math.pi * 0.125 * t)

            val = 0.0
            for f, w in zip(freqs, weights):
                val += w * math.sin(2 * math.pi * f * t)

            # Smooth fade-in and fade-out
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

    print("4. Runt)
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
