"""Visual finishing and video assembly for Nūr Social AI.

The module deliberately uses original/licensed source imagery rather than
pretending that generated geometric shapes are photographs.
"""
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

WIDTH = 1080
HEIGHT = 1920
FOREST = (11, 93, 59)  # Nūr primary emerald #0B5D3B
DEEP_FOREST = (6, 78, 59)  # secondary depth colour
IVORY = (245, 240, 225)
GOLD = (212, 175, 55)
CHARCOAL = (18, 24, 21)


def _font(size, serif=False, bold=False):
    name = ("DejaVuSerif" if serif else "DejaVuSans") + ("-Bold" if bold else "") + ".ttf"
    for path in (
        f"/usr/share/fonts/truetype/dejavu/{name}",
        f"/usr/share/fonts/dejavu/{name}",
    ):
        if Path(path).is_file():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default()


def _wrap(text, font, draw, width):
    lines, current = [], ""
    for word in str(text).split():
        candidate = f"{current} {word}".strip()
        if draw.textbbox((0, 0), candidate, font=font)[2] <= width:
            current = candidate
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def enhance_photo(path):
    """Apply restrained photographic finishing without fabricating scene detail."""
    path = Path(path)
    with Image.open(path) as opened:
        image = ImageOps.exif_transpose(opened).convert("RGB")
    image = ImageOps.autocontrast(image, cutoff=0.35)
    image = ImageEnhance.Color(image).enhance(1.08)
    image = ImageEnhance.Contrast(image).enhance(1.08)
    image = ImageEnhance.Brightness(image).enhance(1.015)
    image = ImageEnhance.Sharpness(image).enhance(1.12)
    image.save(path, format="JPEG", quality=95, optimize=True, progressive=True)
    return path


def render_scene_overlay(scene, destination, scene_index=0, visual_style="cinematic_documentary"):
    """Create a transparent Nūr typography layer for genuine moving footage."""
    overlay = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    for y in range(HEIGHT):
        top_alpha = int(112 * max(0.0, 1.0 - y / 520))
        bottom_start = int(HEIGHT * 0.58)
        bottom_alpha = int(205 * max(0.0, (y - bottom_start) / (HEIGHT - bottom_start)))
        alpha = max(top_alpha, bottom_alpha)
        if alpha:
            draw.line((0, y, WIDTH, y), fill=(4, 16, 12, alpha), width=1)
    draw.text((76, 82), "Nūr", font=_font(43, serif=True, bold=True), fill=IVORY + (255,))
    draw.line((78, 151, 1002, 151), fill=FOREST + (245,), width=4)
    beat = str(scene.get("beat", f"SCENE {scene_index + 1}")).upper()
    draw.text((80, 177), beat[:48], font=_font(20, bold=True), fill=GOLD + (255,))
    caption = str(scene.get("on_screen_text", "")).strip()
    if visual_style in ("tactile_editorial_collage", "hybrid_documentary_collage"):
        paper = (245, 240, 225, 238) if visual_style == "tactile_editorial_collage" else (245, 240, 225, 215)
        # Editorial paper strip with a deliberately imperfect cut edge.
        points = [(64, 1410), (1010, 1420), (1000, 1785), (955, 1792), (875, 1784),
                  (760, 1793), (640, 1784), (510, 1792), (390, 1785), (260, 1793), (130, 1784), (70, 1791)]
        draw.polygon(points, fill=paper)
        draw.line((100, 1435, 270, 1432, 300, 1437), fill=FOREST + (255,), width=7)
        caption_color = CHARCOAL + (255,)
        caption_width = 850
    else:
        caption_color = IVORY + (255,)
        caption_width = 900
    size = 62
    caption_font = _font(size, serif=True)
    lines = _wrap(caption, caption_font, draw, caption_width)
    while len(lines) > 3 and size > 42:
        size -= 4
        caption_font = _font(size, serif=True)
        lines = _wrap(caption, caption_font, draw, 900)
    if len(lines) > 3:
        raise ValueError("Scene caption exceeds the visual-quality limit of three lines.")
    y = 1480
    draw.rounded_rectangle((80, 1435, 178, 1442), radius=3, fill=FOREST + (255,))
    for line in lines:
        draw.text((95 if visual_style in ("tactile_editorial_collage", "hybrid_documentary_collage") else 80, y), line, font=caption_font, fill=caption_color,
                  stroke_width=0 if visual_style in ("tactile_editorial_collage", "hybrid_documentary_collage") else 1,
                  stroke_fill=(0, 0, 0, 90))
        y += int(size * 1.22)
    for index in range(4):
        left = 80 + index * 235
        fill = FOREST + (255,) if index <= int(scene_index) else (245, 240, 225, 115)
        draw.rounded_rectangle((left, 1830, left + 205, 1835), radius=3, fill=fill)
    overlay.save(destination, format="PNG", optimize=True)
    return Path(destination)


def render_scene_frame(photo_path, scene, destination, scene_index=0, visual_style="cinematic_documentary"):
    """Render a coherent premium vertical frame with readable, restrained type."""
    with Image.open(photo_path) as opened:
        frame = ImageOps.fit(
            opened.convert("RGB"), (WIDTH, HEIGHT),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.43),
        ).convert("RGBA")

    # Darken only the typography zones; retain the photograph as the hero.
    overlay = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    pixels = overlay.load()
    for y in range(HEIGHT):
        top_alpha = int(112 * max(0.0, 1.0 - y / 520))
        bottom_start = int(HEIGHT * 0.58)
        bottom_alpha = int(205 * max(0.0, (y - bottom_start) / (HEIGHT - bottom_start)))
        alpha = max(top_alpha, bottom_alpha)
        if alpha:
            for x in range(WIDTH):
                pixels[x, y] = (4, 16, 12, alpha)
    frame = Image.alpha_composite(frame, overlay)
    draw = ImageDraw.Draw(frame)

    # Consistent masthead across every scene.
    draw.text((76, 82), "Nūr", font=_font(43, serif=True, bold=True), fill=IVORY + (255,))
    draw.line((78, 151, 1002, 151), fill=FOREST + (245,), width=4)
    beat = str(scene.get("beat", f"SCENE {scene_index + 1}")).upper()
    draw.text((80, 177), beat[:48], font=_font(20, bold=True), fill=GOLD + (255,))

    caption = str(scene.get("on_screen_text", "")).strip()
    if visual_style in ("tactile_editorial_collage", "hybrid_documentary_collage"):
        paper_alpha = 238 if visual_style == "tactile_editorial_collage" else 218
        points = [(64, 1410), (1010, 1420), (1000, 1785), (955, 1792), (875, 1784),
                  (760, 1793), (640, 1784), (510, 1792), (390, 1785), (260, 1793), (130, 1784), (70, 1791)]
        draw.polygon(points, fill=(245, 240, 225, paper_alpha))
        draw.line((100, 1435, 270, 1432, 300, 1437), fill=FOREST, width=7)
        caption_color = CHARCOAL
        caption_width = 850
    else:
        caption_color = IVORY
        caption_width = 900
    size = 62
    caption_font = _font(size, serif=True)
    lines = _wrap(caption, caption_font, draw, caption_width)
    while len(lines) > 3 and size > 42:
        size -= 4
        caption_font = _font(size, serif=True)
        lines = _wrap(caption, caption_font, draw, 900)
    if len(lines) > 3:
        raise ValueError("Scene caption exceeds the visual-quality limit of three lines.")

    # Editorial lower-third: open space, a gold rule and a stable left edge.
    rule_y = 1435
    draw.rounded_rectangle((80, rule_y, 178, rule_y + 7), radius=3, fill=FOREST + (255,))
    line_height = int(size * 1.22)
    y = 1480
    for line in lines:
        draw.text((95 if visual_style in ("tactile_editorial_collage", "hybrid_documentary_collage") else 80, y), line, font=caption_font, fill=caption_color,
                  stroke_width=1 if visual_style == "cinematic_documentary" else 0,
                  stroke_fill=(0, 0, 0, 90))
        y += line_height

    # Four quiet progress marks; no decorative boxed caption.
    mark_y = 1830
    for index in range(4):
        left = 80 + index * 235
        fill = FOREST + (255,) if index <= int(scene_index) else (245, 240, 225, 115)
        draw.rounded_rectangle((left, mark_y, left + 205, mark_y + 5),
                               radius=3, fill=fill)
    frame.convert("RGB").save(destination, format="JPEG", quality=95, optimize=True)
    return Path(destination)


def _duration(path):
    result = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", str(path)],
        capture_output=True, text=True, check=True,
    )
    return float(result.stdout.strip())


def join_video_segments(segments, destination, transition=0.35, transitions=None):
    """Join voice-led scenes with short video/audio crossfades and fast-start MP4."""
    segments = [Path(item) for item in segments]
    if len(segments) < 2:
        raise ValueError("At least two video segments are required.")
    durations = [_duration(item) for item in segments]
    if any(value <= transition for value in durations):
        raise ValueError("A scene is too short for the configured transition.")

    command = ["ffmpeg", "-y"]
    for item in segments:
        command.extend(["-i", str(item)])

    filters = []
    transitions = list(transitions or [])
    allowed_transitions = {"fade", "wipeleft", "wiperight", "slideleft", "slideright", "smoothleft", "smoothright", "circleopen", "soft_cut"}
    video_label = "[0:v]"
    audio_label = "[0:a]"
    elapsed = durations[0]
    for index in range(1, len(segments)):
        next_video = f"[v{index}]"
        next_audio = f"[a{index}]"
        offset = elapsed - transition
        transition_name = transitions[index - 1] if index - 1 < len(transitions) else "fade"
        if transition_name == "soft_cut":
            transition_name = "fade"
        if transition_name not in allowed_transitions:
            transition_name = "fade"
        filters.append(
            f"{video_label}[{index}:v]xfade=transition={transition_name}:duration={transition}:"
            f"offset={offset:.3f}{next_video}"
        )
        filters.append(
            f"{audio_label}[{index}:a]acrossfade=d={transition}:c1=tri:c2=tri{next_audio}"
        )
        video_label, audio_label = next_video, next_audio
        elapsed += durations[index] - transition

    command.extend([
        "-filter_complex", ";".join(filters),
        "-map", video_label, "-map", audio_label,
        "-c:v", "libx264", "-preset", "medium", "-crf", "19",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart", str(destination),
    ])
    result = subprocess.run(command, capture_output=True, text=True, check=False)
    if result.returncode:
        raise RuntimeError(f"FFmpeg transition assembly failed: {result.stderr[-2500:]}")
    return Path(destination)


def render_editorial_poster(plan, destination, photo_path):
    """Build a photo-led 4:5 poster with a disciplined editorial hierarchy."""
    graphic = plan["graphic"]
    canvas = Image.new("RGB", (1080, 1350), (245, 240, 225))
    photo_box = (64, 64, 1016, 690)
    with Image.open(photo_path) as opened:
        photo = ImageOps.fit(
            opened.convert("RGB"),
            (photo_box[2] - photo_box[0], photo_box[3] - photo_box[1]),
            method=Image.Resampling.LANCZOS,
            centering=(0.5, 0.42),
        ).convert("RGBA")

    # Softly rounded hero image, not a small rectangular inset.
    mask = Image.new("L", photo.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        (0, 0, photo.width - 1, photo.height - 1), radius=24, fill=255
    )
    canvas.paste(photo.convert("RGB"), photo_box[:2], mask)
    draw = ImageDraw.Draw(canvas, "RGBA")

    # Restrained top scrim ensures the wordmark and category remain legible.
    scrim = Image.new("RGBA", photo.size, (0, 0, 0, 0))
    scrim_draw = ImageDraw.Draw(scrim)
    for y in range(210):
        alpha = int(158 * (1 - y / 210))
        scrim_draw.line((0, y, photo.width, y), fill=(4, 18, 13, alpha))
    canvas.paste(Image.alpha_composite(photo, scrim).convert("RGB"), photo_box[:2], mask)

    draw.text((92, 94), "Nūr", font=_font(48, serif=True, bold=True), fill=IVORY + (255,))
    category = str(plan.get("pillar_label", "INTENTIONAL LIVING")).upper()
    category_font = _font(17, bold=True)
    category_width = draw.textbbox((0, 0), category, font=category_font)[2]
    draw.text((980 - category_width, 119), category, font=category_font, fill=GOLD + (255,))

    # Headline block: consistent left alignment and deliberate line spacing.
    headline = str(graphic.get("headline", "")).strip()
    size = 64
    headline_font = _font(size, serif=True, bold=True)
    lines = _wrap(headline, headline_font, draw, 920)
    while len(lines) > 3 and size > 46:
        size -= 4
        headline_font = _font(size, serif=True, bold=True)
        lines = _wrap(headline, headline_font, draw, 920)
    if len(lines) > 3:
        raise ValueError("Poster headline exceeds three lines; regenerate the editorial plan.")

    y = 748
    line_height = int(size * 1.12)
    for line in lines:
        draw.text((76, y), line, font=headline_font, fill=CHARCOAL + (255,))
        y += line_height

    y += 16
    draw.rounded_rectangle((78, y, 190, y + 6), radius=3, fill=FOREST + (255,))
    y += 32

    body_font = _font(27)
    body_lines = _wrap(str(graphic.get("subtext", "")), body_font, draw, 920)
    if len(body_lines) > 3:
        body_font = _font(24)
        body_lines = _wrap(str(graphic.get("subtext", "")), body_font, draw, 920)
    if len(body_lines) > 3:
        raise ValueError("Poster subtext exceeds three lines; regenerate the editorial plan.")
    for line in body_lines:
        draw.text((78, y), line, font=body_font, fill=(75, 78, 72, 255))
        y += 39

    draw.line((78, 1214, 1002, 1214), fill=(166, 138, 100, 210), width=1)
    draw.text((78, 1240), "Build the person you want to become.",
              font=_font(20, serif=True), fill=(75, 78, 72, 255))
    edition = "Nūr  /  EDITORIAL"
    edition_font = _font(15, bold=True)
    edition_width = draw.textbbox((0, 0), edition, font=edition_font)[2]
    draw.text((1002 - edition_width, 1244), edition,
              font=edition_font, fill=(140, 107, 31, 255))

    canvas.save(destination, format="PNG", optimize=True)
    return Path(destination)
