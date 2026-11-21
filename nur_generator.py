
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



def _model_name(item):
    return str(item.get("name") or item.get("id") or "").strip().rsplit("/", 1)[-1]


def discover_gemini_model(api_key, preferred=None):
    r=requests.get("https://generativelanguage.googleapis.com/v1beta/models",
        headers={"x-goog-api-key":api_key},params={"pageSize":1000},timeout=30)
    r.raise_for_status()
    models=r.json().get("models",[])
    names=[_model_name(m) for m in models if "generateContent" in m.get("supportedGenerationMethods",[])]
    if preferred and preferred in names: return preferred
    if not names: raise RuntimeError("Gemini account exposes no generateContent models.")
    flash=sorted(n for n in names if "flash" in n.lower())
    return (flash or sorted(names))[0]


def discover_groq_model(api_key, preferred=None):
    r=requests.get("https://api.groq.com/openai/v1/models",
        headers={"Authorization":f"Bearer {api_key}"},timeout=30)
    r.raise_for_status()
    names=[_model_name(m) for m in r.json().get("data",[]) if m.get("active",True)]
    if preferred and preferred in names: return preferred
    if not names: raise RuntimeError("Groq account exposes no active models.")
    for n in ("llama-3.3-70b-versatile","llama-3.1-8b-instant"):
        if n in names: return n
    return sorted(names)[0]


def provider_error(response):
    try: detail=response.json()
    except ValueError: detail=response.text
    return f"HTTP {response.status_code}: {str(detail)[:500]}"


ASSET_ATTRIBUTIONS=[]
_USED_ASSET_IDS=set()


def _clean_metadata(value):
    import html, re
    raw=value.get("value","") if isinstance(value,dict) else value or ""
    return " ".join(html.unescape(re.sub(r"<[^>]+>"," ",str(raw))).split())


def _commons_license_allowed(short_name, license_url):
    label,url=str(short_name or "").lower(),str(license_url or "").lower()
    if not label or not url or any(x in label for x in ("noncommercial","no derivatives","-nc","-nd")):
        return False
    return ("creativecommons.org/publicdomain/zero" in url or
        "creativecommons.org/licenses/by/" in url or
        "creativecommons.org/licenses/by-sa/" in url or "public domain" in label or "public domain" in url)


def _normalise_download(content,width,height,destination):
    destination=Path(destination)
    if not content or len(content)<5000: raise RuntimeError("Image file is empty or unusually small.")
    destination.write_bytes(content)
    try:
        with Image.open(destination) as im: im.verify()
        with Image.open(destination) as im:
            if im.width<320 or im.height<240: raise RuntimeError("Image dimensions are too small.")
            ImageOps.fit(im.convert("RGB"),(width,height),method=Image.Resampling.LANCZOS).save(destination,format="JPEG",quality=94,optimize=True)
    except Exception as exc:
        destination.unlink(missing_ok=True)
        raise RuntimeError("Image could not be validated or processed.") from exc
    return destination


def _search_commons(query,width,height,destination):
    r=requests.get("https://commons.wikimedia.org/w/api.php",params={
        "action":"query","generator":"search","gsrsearch":query,"gsrnamespace":6,"gsrlimit":15,
        "prop":"imageinfo","iiprop":"url|extmetadata",
        "iiextmetadatafilter":"LicenseShortName|LicenseUrl|Artist|Attribution|Restrictions","format":"json"},
        headers={"User-Agent":"NurSocialAI/1.0 (editorial media sourcing)"},timeout=30)
    r.raise_for_status()
    pages=list(r.json().get("query",{}).get("pages",{}).values()); random.shuffle(pages)
    for page in pages:
        infos=page.get("imageinfo") or []
        if not infos: continue
        info=infos[0]; meta=info.get("extmetadata",{})
        lic=_clean_metadata(meta.get("LicenseShortName")); licurl=_clean_metadata(meta.get("LicenseUrl"))
        if _clean_metadata(meta.get("Restrictions")) or not _commons_license_allowed(lic,licurl): continue
        aid=str(page.get("pageid") or page.get("title") or "")
        if aid in _USED_ASSET_IDS: continue
        url=info.get("thumburl") or info.get("url")
        if not url: continue
        try:
            img=requests.get(url,timeout=60); img.raise_for_status()
            path=_normalise_download(img.content,width,height,destination)
            _USED_ASSET_IDS.add(aid)
            ASSET_ATTRIBUTIONS.append({"provider":"Wikimedia Commons","asset_id":aid,
                "title":page.get("title"),"creator":_clean_metadata(meta.get("Attribution") or meta.get("Artist")),
                "source_page":info.get("descriptionurl"),"license":lic,"license_url":licurl})
            return path
        except Exception as exc: print(f"Skipping Commons result: {type(exc).__name__}: {str(exc)[:160]}")
    raise RuntimeError("No unused Commons image with an accepted, identified licence was found.")


def _generate_local_illustration(prompt, width, height, destination):
    """Create original Nūr editorial artwork as a clearly labelled last resort."""
    import hashlib

    seed = int(hashlib.sha256(str(prompt).encode("utf-8")).hexdigest()[:8], 16)
    rng = random.Random(seed)
    image = Image.new("RGB", (width, height), "#F5F0E1")
    draw = ImageDraw.Draw(image)
    forest, green, ivory = "#064E3B", "#0B5D3B", "#F5F0E1"
    gold, bronze, charcoal = "#D4AF37", "#A68A64", "#1C1C1C"
    horizon = int(height * rng.uniform(0.55, 0.66))
    margin = int(width * 0.12)
    draw.rounded_rectangle((margin, int(height*.09), width-margin, horizon-int(height*.07)),
        radius=max(8,width//70), fill="#E8DCC1", outline=bronze, width=max(2,width//300))
    sun_r=max(12,min(width,height)//12)
    sun_x=width//2+rng.randint(-width//8,width//8)
    sun_y=int(height*.29)
    draw.ellipse((sun_x-sun_r,sun_y-sun_r,sun_x+sun_r,sun_y+sun_r),fill=gold)
    draw.ellipse((-width//3,horizon-int(height*.08),int(width*.72),horizon+int(height*.18)),fill=bronze)
    draw.ellipse((int(width*.3),horizon-int(height*.14),width+width//3,horizon+int(height*.16)),fill=green)
    draw.rectangle((0,horizon,width,height),fill=forest)
    desk_y=int(height*.78)
    draw.rectangle((0,desk_y,width,height),fill=charcoal)
    bw,bh=int(width*.43),int(height*.13)
    bx=(width-bw)//2; by=desk_y-int(height*.08)
    draw.rounded_rectangle((bx,by,bx+bw,by+bh),radius=max(5,width//100),fill=ivory,outline=gold,width=max(2,width//300))
    draw.line((width//2,by+8,width//2,by+bh-8),fill=bronze,width=max(1,width//500))
    for n in range(3):
        yy=by+int(bh*(.25+n*.22))
        draw.line((bx+int(bw*.1),yy,width//2-int(width*.03),yy),fill=bronze,width=max(1,width//450))
        draw.line((width//2+int(width*.03),yy,bx+int(bw*.9),yy),fill=bronze,width=max(1,width//450))
    plant_x=int(width*.82)
    draw.line((plant_x,desk_y,plant_x,desk_y-int(height*.15)),fill=ivory,width=max(2,width//220))
    for dx,dy in [(-1,-1),(1,-1),(-1,-2),(1,-2)]:
        ex=plant_x+dx*int(width*.05); ey=desk_y+dy*int(height*.045)
        draw.ellipse((min(plant_x,ex)-width//35,min(desk_y-int(height*.15),ey)-height//60,
                      max(plant_x,ex)+width//35,max(desk_y-int(height*.15),ey)+height//60),fill=green)
    image.save(destination,format="JPEG",quality=93,optimize=True)
    ASSET_ATTRIBUTIONS.append({
        "provider":"Nūr Social AI local illustration",
        "asset_id":hashlib.sha256(str(prompt).encode("utf-8")).hexdigest()[:16],
        "creator":"Generated locally by Nūr Social AI",
        "source_page":None,
        "license":"Original generated artwork",
        "license_url":None,
        "media_type":"illustration_not_photograph",
    })
    return Path(destination)


def generate_photo(prompt,width,height,destination):
    import re
    query=" ".join(re.findall(r"[A-Za-z0-9']+",str(prompt)))[:180]
    try:
        return _search_commons(query,width,height,destination)
    except Exception as exc:
        print(f"Wikimedia Commons unavailable: {type(exc).__name__}: {str(exc)[:240]}")
        print("Using built-in Nūr illustration fallback; this is not a photograph.")
        return _generate_local_illustration(prompt,width,height,destination)


def generate_editorial_plan(brand, history):
    """Gemini primary, Groq backup, then a local editorial fallback."""
    pillar = random.choice(brand.get("pillars") or ["Digital Self-Control"])
    category = random.choice(VIDEO_CATEGORIES)
    recent = ", ".join(history[-15:]) if history else "None"
    system_prompt = (
        "You are the editorial director for Nūr. Always spell the brand exactly as Nūr. "
        "Nūr supports self-control, protection, recovery and personal growth. "
        "Its philosophy is privacy-first, non-judgemental and user-controlled. "
        "Never shame people, induce guilt, use fear-based marketing, invent statistics, "
        "fabricate religious quotations, or claim unverified app features exist. "
        "Use British English. Be calm, intelligent, precise and human. "
        "Return valid JSON only, without Markdown fences."
    )
    user_prompt = f"""
Create one original Nūr social-media content package.
Pillar: {pillar}
Category: {category}
Avoid these recent topics: {recent}
Return a JSON object with topic_slug, pillar_label, graphic, caption_image, video and caption_video.
graphic must contain theme, headline, subtext and photo_prompt.
video must contain a title and exactly four scenes.
Each scene must contain beat, voiceover, on_screen_text and image_prompt.
Make the four visual scenes noticeably different, realistic and cinematic.
Avoid generic gradients, empty green backgrounds and abstract shapes.
"""

    def validate_plan(plan):
        if not isinstance(plan, dict):
            raise ValueError("Editorial response must be a JSON object.")
        required = ("topic_slug", "pillar_label", "graphic", "caption_image", "video", "caption_video")
        for key in required:
            if key not in plan:
                raise ValueError(f"Missing editorial field: {key}")
        if not isinstance(plan["graphic"], dict) or not isinstance(plan["video"], dict):
            raise ValueError("Graphic and video must be JSON objects.")
        for key in ("theme", "headline", "subtext", "photo_prompt"):
            if not plan["graphic"].get(key):
                raise ValueError(f"Graphic is missing {key}.")
        scenes = plan["video"].get("scenes", [])
        if not isinstance(scenes, list) or len(scenes) != 4:
            raise ValueError("Exactly four video scenes are required.")
        for scene in scenes:
            if not isinstance(scene, dict):
                raise ValueError("Each scene must be an object.")
            for key in ("beat", "voiceover", "on_screen_text", "image_prompt"):
                if not scene.get(key):
                    raise ValueError(f"Scene is missing {key}.")
        visual_prompts = {
            " ".join(str(scene["image_prompt"]).lower().split())
            for scene in scenes
        }
        if len(visual_prompts) != 4:
            raise ValueError("Each video scene must have a distinct visual prompt.")
        for key in ("topic_slug", "pillar_label", "caption_image", "caption_video"):
            if not isinstance(plan[key], str) or not plan[key].strip():
                raise ValueError(f"{key} must be non-empty text.")
        plan["caption_image"] = enforce_wordmark(plan["caption_image"])
        plan["caption_video"] = enforce_wordmark(plan["caption_video"])
        plan["graphic"]["headline"] = enforce_wordmark(plan["graphic"]["headline"])
        plan["graphic"]["subtext"] = enforce_wordmark(plan["graphic"]["subtext"])
        return plan

    def fallback_plan():
        return {
            "topic_slug": f"small-steps-{random.randint(1000, 9999)}",
            "pillar_label": "SMALL, INTENTIONAL STEPS",
            "graphic": {
                "theme": "dark_forest",
                "headline": "You can begin again with one small choice",
                "subtext": "A difficult moment does not erase your progress. Pause, notice what you need, and choose one helpful next step.",
                "photo_prompt": "A quiet, warmly lit room at dawn, notebook and glass of water on a wooden desk, natural window light, realistic editorial photography.",
            },
            "caption_image": "Progress is not built by getting everything right.\n\nIt grows through small decisions, honest reflection, and the willingness to return to what matters after a difficult moment.\n\nChoose one helpful next step today.\n\n#SelfControl #PersonalGrowth #SmallSteps #Nūr",
            "video": {
                "title": "One Small Choice Can Help You Reset",
                "scenes": [
                    {"beat": "01 - THE HOOK", "voiceover": "Sometimes the hardest part is believing you can begin again.", "on_screen_text": "You can begin again.", "image_prompt": "A person sitting quietly beside a window at dawn, reflective mood, natural light, realistic home."},
                    {"beat": "02 - THE PROBLEM", "voiceover": "When a moment does not go as planned, it can be tempting to give up on the rest of the day.", "on_screen_text": "One moment is not the whole day.", "image_prompt": "A person closing a laptop and stepping away from a desk, evening indoor lighting, thoughtful realistic scene."},
                    {"beat": "03 - THE REALISATION", "voiceover": "Progress is not a perfect record. It is the practice of noticing and choosing again.", "on_screen_text": "Progress is a practice.", "image_prompt": "A person writing a short reflection in a paper notebook at a wooden table, warm lamp light, realistic surroundings."},
                    {"beat": "04 - THE RESPONSE", "voiceover": "Take a breath, identify what you need, and choose one small action that supports the person you want to become.", "on_screen_text": "Choose one helpful next step.", "image_prompt": "A person walking along a peaceful tree-lined path in soft morning light, hopeful natural atmosphere."},
                ],
            },
            "caption_video": "You do not need to solve everything at once. Pause, understand what you need, and take one constructive step.\n\n#SelfControl #Recovery #PersonalGrowth #Nūr",
        }

    gemini_key = os.environ.get("GEMINI_API_KEY", "").strip()
    groq_key = os.environ.get("GROQ_API_KEY", "").strip()
    providers = []
    if gemini_key:
        providers.append("gemini")
    if groq_key:
        providers.append("groq")

    for provider in providers:
        try:
            print(f"Generating editorial plan with {provider.title()}...")
            if provider == "gemini":
                preferred = os.environ.get("GEMINI_MODEL", "").strip() or None
                model = discover_gemini_model(gemini_key, preferred)
                print(f"Gemini selected available model: {model}")
                response = requests.post(
                    f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                    headers={"x-goog-api-key": gemini_key, "Content-Type": "application/json"},
                    json={
                        "systemInstruction": {"parts": [{"text": system_prompt}]},
                        "contents": [{"role": "user", "parts": [{"text": user_prompt}]}],
                        "generationConfig": {"temperature": 0.7, "responseMimeType": "application/json"},
                    },
                    timeout=90,
                )
                if not response.ok: raise RuntimeError(provider_error(response))
                raw = response.json()["candidates"][0]["content"]["parts"][0]["text"]
            else:
                preferred = os.environ.get("GROQ_MODEL", "").strip() or None
                model = discover_groq_model(groq_key, preferred)
                print(f"Groq selected available model: {model}")
                response = requests.post(
                    "https://api.groq.com/openai/v1/chat/completions",
                    headers={"Authorization": f"Bearer {groq_key}", "Content-Type": "application/json"},
                    json={
                        "model": model,
                        "messages": [
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt},
                        ],
                        "temperature": 0.7,
                        "response_format": {"type": "json_object"},
                    },
                    timeout=90,
                )
                if not response.ok: raise RuntimeError(provider_error(response))
                raw = response.json()["choices"][0]["message"]["content"]
            raw = str(raw or "").strip()
            if raw.startswith("```"):
                raw = raw.split("\n", 1)[-1].rsplit("```", 1)[0].strip()
            first, last = raw.find("{"), raw.rfind("}")
            if first < 0 or last <= first:
                raise ValueError("Provider did not return a JSON object.")
            plan = validate_plan(json.loads(raw[first:last + 1]))
            print(f"Editorial plan generated successfully with {provider.title()}.")
            return plan
        except Exception as error:
            print(f"{provider.title()} failed: {type(error).__name__}: {str(error)[:600]}")

    if providers:
        print("All AI providers failed. Using the built-in editorial fallback.")
    else:
        print("No Gemini or Groq key supplied. Using the built-in editorial fallback.")
    return validate_plan(fallback_plan())


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


def scene_caption_layout(scene_index):
    """Return a repeatable but varied caption-panel layout for each scene."""
    layouts = (
        {"left": 58, "right": WIDTH - 58, "align": "center"},
        {"left": 58, "right": 790, "align": "left"},
        {"left": 290, "right": WIDTH - 58, "align": "left"},
        {"left": 104, "right": WIDTH - 104, "align": "center"},
    )
    return layouts[int(scene_index) % len(layouts)]


def build_scene_frame(photo_path, scene, destination, scene_index=0):
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

    layout = scene_caption_layout(scene_index)
    panel_left, panel_right = layout["left"], layout["right"]
    panel_width = panel_right - panel_left
    caption_font = font(43, serif=True)
    lines = wrap_text(
        scene["on_screen_text"],
        caption_font,
        draw,
        panel_width - 76,
    )

    if len(lines) > 3:
        caption_font = font(37, serif=True)
        lines = wrap_text(
            scene["on_screen_text"],
            caption_font,
            draw,
            panel_width - 76,
        )
    if len(lines) > 3:
        caption_font = font(32, serif=True)
        lines = wrap_text(
            scene["on_screen_text"],
            caption_font,
            draw,
            panel_width - 76,
        )
    if len(lines) > 3:
        raise ValueError("Scene caption is too long to fit legibly; regenerate the editorial plan.")

    line_height = 62 if caption_font.size >= 37 else 48
    panel_height = max(210, 88 + len(lines) * line_height)
    panel_bottom = 1790
    panel_top = panel_bottom - panel_height

    draw.rounded_rectangle(
        (panel_left, panel_top, panel_right, panel_bottom),
        radius=22,
        fill=(8, 8, 8, 205),
        outline=(212, 175, 55, 210),
        width=2,
    )

    y = panel_top + (panel_height - len(lines) * line_height) // 2
    for line in lines:
        bounds = draw.textbbox((0, 0), line, font=caption_font)
        text_width = bounds[2] - bounds[0]
        if layout["align"] == "center":
            x = panel_left + (panel_width - text_width) // 2
        else:
            x = panel_left + 34
        draw.text(
            (x, y),
            line,
            fill=(245, 240, 225, 255),
            font=caption_font,
        )
        y += line_height

    # A restrained scene-progress marker gives the sequence a clear rhythm.
    progress_y = 1840
    draw.rounded_rectangle(
        (78, progress_y, WIDTH - 78, progress_y + 5),
        radius=3,
        fill=(245, 240, 225, 105),
    )
    progress_right = 78 + int((WIDTH - 156) * ((int(scene_index) + 1) / 4))
    draw.rounded_rectangle(
        (78, progress_y, progress_right, progress_y + 5),
        radius=3,
        fill=(212, 175, 55, 245),
    )

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
    scene_index=0,
):
    if zoom:
        total_frames = max(1, int(float(duration) * FPS))
        if int(scene_index) % 2 == 0:
            x_start, x_end = 0.18, 0.68
        else:
            x_start, x_end = 0.82, 0.32
        y_start, y_end = (0.30, 0.58) if int(scene_index) < 2 else (0.68, 0.42)
        x_motion = (
            f"(iw-iw/zoom)*({x_start}+"
            f"({x_end}-{x_start})*on/{total_frames})"
        )
        y_motion = (
            f"(ih-ih/zoom)*({y_start}+"
            f"({y_end}-{y_start})*on/{total_frames})"
        )
        video_filter = (
            "zoompan=z='min(1+0.00065*on,1.045)':"
            f"x='{x_motion}':y='{y_motion}':"
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

    scenes = plan.get("video", {}).get("scenes", [])
    visual_prompts = {
        " ".join(str(scene.get("image_prompt", "")).lower().split())
        for scene in scenes
    }
    if len(scenes) != 4 or len(visual_prompts) != 4:
        failures.append("Video scenes must contain four distinct visual prompts.")

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
            "Four distinct scene visual prompts",
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
    ASSET_ATTRIBUTIONS.clear()
    _USED_ASSET_IDS.clear()

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
                scene_index=index,
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
                scene_index=index,
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
                "assets": ASSET_ATTRIBUTIONS,
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
