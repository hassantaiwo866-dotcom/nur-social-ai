import os
import json
import random
import asyncio
import urllib.parse
import requests
import edge_tts
from PIL import Image, ImageDraw, ImageFont
from moviepy import ImageClip, AudioFileClip, CompositeVideoClip, concatenate_videoclips

# CONFIGURATION
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "YOUR_OPENROUTER_API_KEY_HERE")
VOICE = "en-GB-RyanNeural"  # Calm, intelligent British English voice
OUTPUT_DIR = "output"
FONTS_DIR = "fonts"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def load_json(path: str, default):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return default

def save_json(path: str, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def load_brand_font(filename: str, size: int):
    """Loads NŪR's custom .ttf font from fonts/ with a safe fallback."""
    font_path = os.path.join(FONTS_DIR, filename)
    if os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size=size)
        except Exception as e:
            print(f"Warning: Could not load {font_path} ({e}). Using default font.")
    return ImageFont.load_default(size=size)

def generate_nur_content(brand: dict, history: list) -> dict:
    """Calls OpenRouter's free auto-router with strict NŪR brand guardrails."""
    chosen_pillar = random.choice(brand["pillars"])
    recent_topics = history[-15:] if history else ["None yet"]

    system_prompt = f"""
    You are the Head of Brand Editorial for {brand['brand_name']} — "{brand['tagline']}".
    Follow these rules strictly:
    - Tone: {" | ".join(brand['tone_rules'])}
    - Visual Direction: {brand['visual_style']}
    - Do NOT repeat any of these recent topics: {recent_topics}
    """

    user_prompt = f"""
    Create today's social media content package under the pillar: "{chosen_pillar}".
    Follow NŪR's communication pattern: Identify -> Create Awareness -> Reframe -> Provide Value -> Encourage Action -> Subtle connection to NŪR.

    Return ONLY valid JSON (no markdown fences) with this exact structure:
    {{
        "topic_summary": "5-word summary of today's topic for history tracking",
        "single_image_post": {{
            "headline": "Short, calm editorial insight (max 12 words, British English)",
            "subtext": "One practical reflection sentence (max 18 words)",
            "visual_prompt": "Minimalist photographic scene matching NŪR palette (deep forest green, warm ivory, charcoal, subtle gold light), no text",
            "caption": "Thoughtful Instagram/LinkedIn caption in British English ending with 'Build the person you want to become.' and 3 clean hashtags"
        }},
        "video_post": {{
            "caption": "Short-form video caption for Reels/Shorts/TikTok in British English with 3 hashtags",
            "scenes": [
                {{
                    "stage": "Identify & Awareness",
                    "narration": "Calm spoken sentence identifying a digital habit challenge and why it happens (14-18 words).",
                    "subtitle": "Short on-screen text (max 9 words)",
                    "image_prompt": "Minimalist 9:16 vertical photography, calm forest green and charcoal tones, generous negative space, no text"
                }},
                {{
                    "stage": "Reframe & Value",
                    "narration": "Calm spoken sentence reframing the struggle without shame and giving one practical insight (14-18 words).",
                    "subtitle": "Short on-screen text (max 9 words)",
                    "image_prompt": "Minimalist 9:16 vertical photography, warm ivory and muted gold morning light, serene workspace or architecture, no text"
                }},
                {{
                    "stage": "Action & Nūr",
                    "narration": "One achievable next step today, closing with how Nūr helps you build the person you want to become (14-18 words).",
                    "subtitle": "Build the person you want to become.",
                    "image_prompt": "Minimalist 9:16 vertical photography, deep emerald green and subtle gold accent, calm focus atmosphere, no text"
                }}
            ]
        }}
    }}
    """

    response = requests.post(
        "https://openrouter.ai/api/v1/chat/completions",
        headers={
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "Content-Type": "application/json",
        },
        json={
            "model": "openrouter/free",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "temperature": 0.65
        },
        timeout=60
    )
    response.raise_for_status()
    raw = response.json()["choices"][0]["message"]["content"].strip()

    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return json.loads(raw.strip())

def fetch_brand_image(prompt, width, height, filename):
    encoded = urllib.parse.quote(f"{prompt}, ultra minimalist editorial photography, forest green #0B5D3B and warm ivory #F5F0E1 tones, calm lighting, high aesthetic, no words, no letters")
    seed = random.randint(1, 999999)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&seed={seed}&nologo=true"
    
    try:
        res = requests.get(url, timeout=30)
        if res.status_code == 200 and len(res.content) > 1000:
            with open(filename, "wb") as f:
                f.write(res.content)
            return filename
    except Exception as e:
        print(f"Image API skipped ({e}), using NŪR branded studio canvas...")

    # Fallback: Generate a clean, textured NŪR Forest Green & Gold minimalist backdrop
    img = Image.new("RGB", (width, height), "#064E3B")
    draw = ImageDraw.Draw(img)
    for y in range(height):
        ratio = y / height
        r = int(6 + (11 - 6) * ratio)
        g = int(78 + (93 - 78) * ratio)
        b = int(59 + (59 - 59) * ratio)
        draw.line([(0, y), (width, y)], fill=(r, g, b))
    
    margin = int(width * 0.08)
    draw.rectangle([margin, margin, width - margin, height - margin], outline="#D4AF37", width=2)
    img.save(filename)
    return filename
    """Fetches a clean, watermark-free image matching NŪR's visual style."""
    full_prompt = f"{prompt}, ultra minimalist editorial photography, forest green #0B5D3B and warm ivory #F5F0E1 tones, calm lighting, high aesthetic, no words, no letters"
    encoded = urllib.parse.quote(full_prompt)
    seed = random.randint(1, 999999)
    url = f"https://image.pollinations.ai/prompt/{encoded}?width={width}&height={height}&seed={seed}&nologo=true"

    res = requests.get(url, timeout=90)
    res.raise_for_status()
    with open(save_path, "wb") as f:
        f.write(res.content)

def create_editorial_graphic(bg_image_path: str, headline: str, subtext: str, output_path: str):
    """Creates a clean 1080x1350 branded NŪR card using Cinzel and Cormorant Garamond."""
    base = Image.open(bg_image_path).convert("RGBA").resize((1080, 1350))
    
    # Subtle dark charcoal gradient overlay for crisp typography legibility
    overlay = Image.new("RGBA", base.size, (8, 8, 8, 125))
    card = Image.alpha_composite(base, overlay).convert("RGB")
    draw = ImageDraw.Draw(card)

    # Load NŪR editorial fonts with safe fallbacks
    font_brand = load_brand_font("Cinzel-Regular.ttf", size=38)
    font_head = load_brand_font("Cinzel-Regular.ttf", size=52)
    font_sub = load_brand_font("CormorantGaramond-Regular.ttf", size=40)

    # Muted Gold (#D4AF37) top brand mark & thin accent line
    draw.text((90, 90), "N Ū R", fill="#D4AF37", font=font_brand)
    draw.line([(90, 150), (185, 150)], fill="#D4AF37", width=3)

    # Wrap headline cleanly
    words = headline.split()
    lines, current = [], ""
    for w in words:
        if len(current + " " + w) <= 26:
            current = (current + " " + w).strip()
        else:
            lines.append(current)
            current = w
    if current:
        lines.append(current)

    y_pos = 760
    for line in lines:
        draw.text((90, y_pos), line, fill="#F5F0E1", font=font_head)
        y_pos += 74

    # Subtext in Sand / Warm Ivory using Cormorant Garamond
    y_pos += 28
    sub_words = subtext.split()
    sub_lines, current = [], ""
    for w in sub_words:
        if len(current + " " + w) <= 42:
            current = (current + " " + w).strip()
        else:
            sub_lines.append(current)
            current = w
    if current:
        sub_lines.append(current)

    for line in sub_lines:
        draw.text((90, y_pos), line, fill="#D4AF37", font=font_sub)
        y_pos += 52

    card.save(output_path)

async def make_voiceover(text: str, output_path: str):
    communicate = edge_tts.Communicate(text, VOICE, rate="-4%")
    await communicate.save(output_path)

def make_subtitle_banner(text: str, output_path: str):
    """Renders a clean, minimalist NŪR subtitle bar using Cormorant Garamond."""
    img = Image.new("RGBA", (1080, 220), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle(
        [(80, 20), (1000, 180)],
        radius=20,
        fill=(8, 8, 8, 205),
        outline=(212, 175, 55, 180),
        width=2
    )
    font = load_brand_font("CormorantGaramond-Regular.ttf", size=44)
    
    # Centre text horizontally inside the banner
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    x_pos = max(110, (1080 - text_width) // 2)
    draw.text((x_pos, 72), text, fill="#F5F0E1", font=font)
    img.save(output_path)

async def run_pipeline():
    brand = load_json("brand_config.json", {})
    history = load_json("history.json", [])

    print("1. Generating NŪR editorial plan via OpenRouter...")
    content = generate_nur_content(brand, history)

    # Save topic to history so it never repeats
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
