"""Scene-specific visual prompt composition for Nūr's media pipeline.

Keeps generation prompts detailed and stock-search queries concise. This module
is pure text transformation: it makes no API calls and cannot incur costs.
"""
from __future__ import annotations

import re

GENERATION_STYLE = (
    "Premium cinematic documentary still, realistic human proportions and natural "
    "physical details, believable environment, intentional foreground/midground/background, "
    "clear single focal subject, natural light with gentle contrast, authentic emotion, "
    "subtle depth of field, camera-realistic texture, vertical 9:16 composition. "
    "Leave uncluttered negative space for editorial overlays. No text, lettering, "
    "logos, watermarks, UI, collage, poster design, artificial green tint, or staged stock-photo poses."
)

STOCK_STOP_WORDS = {
    "cinematic", "realistic", "documentary", "footage", "photo", "photograph",
    "image", "scene", "natural", "lighting", "light", "composition", "vertical",
    "portrait", "camera", "shot", "close", "wide", "medium", "detail", "soft",
    "warm", "subtle", "believable", "authentic", "premium", "film", "style",
    "depth", "focus", "texture", "background", "foreground", "midground", "with", "and",
    "the", "a", "an", "in", "on", "at", "of", "for", "to", "from", "by",
    "person", "people", "human", "show", "showing", "illustrate", "visual",
    "actual", "real", "no", "avoid", "not", "without", "over", "rather",
}


def compose_generation_prompt(scene_prompt: str, *, camera_direction: str = "",
                             movement: str = "", beat: str = "") -> str:
    """Add quality and composition constraints without changing scene meaning."""
    subject = re.sub(r"\s+", " ", str(scene_prompt or "")).strip()
    if not subject:
        raise ValueError("Scene prompt must describe a visual subject.")
    direction = " ".join(str(camera_direction or "").split())
    motion = " ".join(str(movement or "").split())
    story_beat = " ".join(str(beat or "").split())
    details = []
    if story_beat:
        details.append(f"Story beat: {story_beat}.")
    if direction:
        details.append(f"Camera framing: {direction}.")
    if motion:
        details.append(f"Implied camera movement: {motion}.")
    return " ".join([
        GENERATION_STYLE,
        "Scene subject and action:", subject,
        *details,
        "Compose the subject clearly and keep important faces or objects away from overlay-safe margins.",
    ])


def build_stock_search_query(scene_prompt: str, *, max_words: int = 12) -> str:
    """Extract subject/action terms for a stock library instead of sending prose."""
    words = re.findall(r"[A-Za-z][A-Za-z'-]{1,}", str(scene_prompt or "").lower())
    selected = []
    for word in words:
        if word in STOCK_STOP_WORDS or word in selected:
            continue
        selected.append(word)
        if len(selected) >= max(1, max_words):
            break
    return " ".join(selected) or "wellbeing personal growth everyday life"
