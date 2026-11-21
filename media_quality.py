"""Visual finishing and video assembly for Nūr Social AI.

The module deliberately uses original/licensed source imagery rather than
pretending that generated geometric shapes are photographs.
"""
from pathlib import Path
import subprocess

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont, ImageOps

WIDTH = 1080
HEIGHT = 1920
FOREST = (6, 78, 59)
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


def render_scene_frame(photo_path, scene, destination, scene_index=0):
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
    draw.line((78, 151, 1002, 151), fill=GOLD + (225,), width=2)
    beat = str(scene.get("beat", f"SCENE {scene_index + 1}")).upper()
    draw.text((80, 177), beat[:48], font=_font(20, bold=True), fill=GOLD + (255,))

    caption = str(scene.get("on_screen_text", "")).strip()
    size = 62
    caption_font = _font(size, serif=True)
    lines = _wrap(caption, caption_font, draw, 900)
    while len(lines) > 3 and size > 42:
        size -= 4
        caption_font = _font(size, serif=True)
        lines = _wrap(caption, caption_font, draw, 900)
    if len(lines) > 3:
        raise ValueError("Scene caption exceeds the visual-quality limit of three lines.")

    # Editorial lower-third: open space, a gold rule and a stable left edge.
    rule_y = 1435
    draw.rounded_rectangle((80, rule_y, 178, rule_y + 7), radius=3, fill=GOLD + (255,))
    line_height = int(size * 1.22)
    y = 1480
    for line in lines:
        draw.text((80, y), line, font=caption_font, fill=IVORY + (255,),
                  stroke_width=1, stroke_fill=(0, 0, 0, 90))
        y += line_height

    # Four quiet progress marks; no decorative boxed caption.
    mark_y = 1830
    for index in range(4):
        left = 80 + index * 235
        fill = GOLD + (255,) if index <= int(scene_index) else (245, 240, 225, 115)
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


def join_video_segments(segments, destination, transition=0.35):
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
    video_label = "[0:v]"
    audio_label = "[0:a]"
    elapsed = durations[0]
    for index in range(1, len(segments)):
        next_video = f"[v{index}]"
        next_audio = f"[a{index}]"
        offset = elapsed - transition
        filters.append(
            f"{video_label}[{index}:v]xfade=transition=fade:duration={transition}:"
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
