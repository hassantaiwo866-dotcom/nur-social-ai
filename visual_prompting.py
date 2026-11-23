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
    "logos, watermarks, UI, poster design, artificial green tint, or staged stock-photo poses."
)

COMPOSITION_DIRECTIONS = {
    "full_frame": (
        "Use a clear full-frame cinematic composition with one dominant focal subject."
    ),
    "bento_modular": (
        "Compose with a strong primary focal area and deliberate open zones that can "
        "support modular bento-style panels in post-production. Do not render text, "
        "interface controls, borders or a collage into the image."
    ),
    "hybrid_editorial": (
        "Keep the cinematic scene dominant while leaving intentional space for a "
        "restrained editorial module or graphic layer to be added in post-production."
    ),
}

DEPTH_DIRECTIONS = {
    "natural_cinematic": (
        "Keep materials, lighting and physical details natural, restrained and grounded."
    ),
    "glass_tactile": (
        "If it supports the subject, include one restrained tactile translucent or "
        "glass-like element with believable reflections; avoid floating interface clutter."
    ),
    "3d_surreal": (
        "If it supports the subject, use one coherent sculptural 3D visual metaphor "
        "integrated into the real environment, with believable light and perspective."
    ),
}

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


def compose_generation_prompt(
    scene_prompt: str,
    *,
    camera_direction: str = "",
    movement: str = "",
    beat: str = "",
    sequence_direction: str = "",
    character_direction: str = "",
    composition: str = "full_frame",
    depth_treatment: str = "natural_cinematic",
) -> str:
    """Add cinematic, scene, composition and text-guided character direction."""
    subject = re.sub(r"\s+", " ", str(scene_prompt or "")).strip()
    if not subject:
        raise ValueError("Scene prompt must describe a visual subject.")
    direction = " ".join(str(camera_direction or "").split())
    motion = " ".join(str(movement or "").split())
    story_beat = " ".join(str(beat or "").split())
    sequence = " ".join(str(sequence_direction or "").split())
    character = " ".join(str(character_direction or "").split())
    composition_hint = COMPOSITION_DIRECTIONS.get(str(composition), COMPOSITION_DIRECTIONS["full_frame"])
    depth_hint = DEPTH_DIRECTIONS.get(str(depth_treatment), DEPTH_DIRECTIONS["natural_cinematic"])
    details = [composition_hint, depth_hint]
    if story_beat:
        details.append(f"Story beat: {story_beat}.")
    if direction:
        details.append(f"Camera framing: {direction}.")
    if motion:
        details.append(f"Implied camera movement: {motion}.")
    if sequence:
        details.append(f"Story continuity direction: {sequence}")
    if character:
        details.append(f"Character continuity direction: {character}")
    return " ".join([
        GENERATION_STYLE,
        "Scene subject and action:", subject,
        *details,
        "Compose the subject clearly and keep important faces or objects away from overlay-safe margins.",
    ])


def build_stock_search_query(scene_prompt: str, *, narration: str = "",
                             max_words: int = 12) -> str:
    """Build a concise stock query from the scene subject and narrated action.

    Subject terms retain priority; narration contributes action/context terms
    when the image prompt alone is too generic. This is deterministic and local.
    """
    source = f"{scene_prompt or ''} {narration or ''}"
    words = re.findall(r"[A-Za-z][A-Za-z'-]{1,}", source.lower())
    selected = []
    for word in words:
        if word in STOCK_STOP_WORDS or word in selected:
            continue
        selected.append(word)
        if len(selected) >= max(1, max_words):
            break
    return " ".join(selected) or "wellbeing personal growth everyday life"
