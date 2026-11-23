"""Per-scene visual direction and text-guided character continuity for Nūr.

This module is deterministic and provider-independent. It defines editorial intent;
it does not claim that a provider can reproduce a character without image references.
"""
from __future__ import annotations

import re
from typing import Any

VISUAL_SOURCES = ("stock_video", "generated_still", "stock_photo", "designed_visual")
COMPOSITIONS = ("full_frame", "bento_modular", "hybrid_editorial")
DEPTH_TREATMENTS = ("natural_cinematic", "glass_tactile", "3d_surreal")
TYPOGRAPHY_TREATMENTS = ("editorial_minimal", "hyperbold_brutalist")

DEFAULT_SCENE_DIRECTIONS = (
    {
        "visual_source": "stock_video",
        "composition": "full_frame",
        "depth_treatment": "natural_cinematic",
        "typography_treatment": "hyperbold_brutalist",
    },
    {
        "visual_source": "generated_still",
        "composition": "bento_modular",
        "depth_treatment": "glass_tactile",
        "typography_treatment": "editorial_minimal",
    },
    {
        "visual_source": "stock_video",
        "composition": "hybrid_editorial",
        "depth_treatment": "natural_cinematic",
        "typography_treatment": "hyperbold_brutalist",
    },
    {
        "visual_source": "designed_visual",
        "composition": "full_frame",
        "depth_treatment": "natural_cinematic",
        "typography_treatment": "editorial_minimal",
    },
)

_SOURCE_ALIASES = {
    "stock_footage": "stock_video",
    "stock_footage_or_photograph": "stock_video",
    "video": "stock_video",
    "ai_generated": "generated_still",
    "generated_image": "generated_still",
    "illustration": "designed_visual",
    "motion_graphic": "designed_visual",
}


def _normalise_choice(value: Any, allowed: tuple[str, ...], field: str) -> str:
    choice = str(value or "").strip().lower()
    if field == "visual_source":
        choice = _SOURCE_ALIASES.get(choice, choice)
    if choice not in allowed:
        raise ValueError(f"Unknown {field}: {choice or '<empty>'}")
    return choice


def normalise_video_visual_direction(video: dict[str, Any]) -> dict[str, Any]:
    """Add safe per-scene defaults and validate recurring-character references.

    Defaults create a balanced four-scene mix for older plans: stock video,
    generated still, stock video, and an original designed visual. Explicit
    editorial choices always take precedence.
    """
    if not isinstance(video, dict):
        raise ValueError("video must be an object")

    characters = video.get("characters") or []
    if not isinstance(characters, list):
        raise ValueError("video.characters must be a list")

    normalised_characters: list[dict[str, str]] = []
    known_ids: set[str] = set()
    for character in characters:
        if not isinstance(character, dict):
            raise ValueError("Each video character must be an object.")
        character_id = str(character.get("id", "")).strip().lower()
        description = " ".join(str(character.get("visual_description", "")).split())
        if not re.fullmatch(r"[a-z0-9][a-z0-9_-]{0,47}", character_id):
            raise ValueError("Character id must be a short lowercase identifier.")
        if character_id in known_ids:
            raise ValueError(f"Duplicate character id: {character_id}")
        if not 12 <= len(description) <= 500:
            raise ValueError(f"Character {character_id} needs a visual_description of 12–500 characters.")
        known_ids.add(character_id)
        normalised_characters.append({
            "id": character_id,
            "visual_description": description,
        })
    video["characters"] = normalised_characters

    scenes = video.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != 4:
        raise ValueError("Visual direction requires exactly four scenes.")

    for index, scene in enumerate(scenes):
        if not isinstance(scene, dict):
            raise ValueError("Each scene must be an object.")
        defaults = DEFAULT_SCENE_DIRECTIONS[index]
        for field, allowed in (
            ("visual_source", VISUAL_SOURCES),
            ("composition", COMPOSITIONS),
            ("depth_treatment", DEPTH_TREATMENTS),
            ("typography_treatment", TYPOGRAPHY_TREATMENTS),
        ):
            raw_choice = scene.get(field)
            if raw_choice is None or str(raw_choice).strip().lower() in ("", "auto"):
                raw_choice = defaults[field]
            scene[field] = _normalise_choice(raw_choice, allowed, field)

        character_ids = scene.get("character_ids") or []
        if not isinstance(character_ids, list):
            raise ValueError(f"Scene {index + 1} character_ids must be a list.")
        cleaned_ids = []
        for value in character_ids:
            character_id = str(value).strip().lower()
            if character_id not in known_ids:
                raise ValueError(
                    f"Scene {index + 1} references unknown character id: {character_id}"
                )
            if character_id not in cleaned_ids:
                cleaned_ids.append(character_id)
        if cleaned_ids and scene["visual_source"] == "designed_visual":
            # The current local illustration is symbolic and cannot depict a
            # recurring character. Prefer the still-image chain instead.
            scene["visual_source"] = "generated_still"
            scene["source_adjustment"] = (
                "designed_visual changed to generated_still because this scene "
                "references a recurring character"
            )
        scene["character_ids"] = cleaned_ids

    return video


def build_character_direction(
    scene: dict[str, Any], characters: list[dict[str, str]]
) -> str:
    """Build a repeatable text identity brief for characters in one scene."""
    selected = set(scene.get("character_ids") or [])
    if not selected:
        return ""
    details = [
        f"{item['id']}: {item['visual_description']}"
        for item in characters if item.get("id") in selected
    ]
    if not details:
        return ""
    return (
        "TEXT-GUIDED CHARACTER CONTINUITY (no visual reference image is supplied): "
        + " | ".join(details)
        + ". Keep each referenced fictional character recognisably consistent "
          "in face, hair, apparent age, clothing, accessories and proportions. "
          "Do not silently redesign or substitute the character."
    )


def build_visual_direction_manifest(video: dict[str, Any]) -> dict[str, Any]:
    """Return auditable visual intent and disclose continuity limitations."""
    characters = video.get("characters", [])
    scene_entries = []
    for index, scene in enumerate(video.get("scenes", [])):
        scene_entries.append({
            "scene": index + 1,
            "visual_source_preference": scene["visual_source"],
            "composition": scene["composition"],
            "depth_treatment": scene["depth_treatment"],
            "typography_treatment": scene["typography_treatment"],
            "character_ids": list(scene.get("character_ids", [])),
            "source_adjustment": scene.get("source_adjustment"),
            "same_performer_unverified": bool(
                scene.get("character_ids")
                and scene["visual_source"] in ("stock_video", "stock_photo")
            ),
        })
    return {
        "visual_identity": "cinematic",
        "source_selection": "editorial_per_scene",
        "character_continuity_mode": "text_guided_only" if characters else "not_used",
        "provider_reference_image_support": False,
        "characters": characters,
        "scenes": scene_entries,
        "limitations": (
            ["Text prompts do not guarantee visual identity; provider reference-image support is not integrated."]
            if characters else []
        ),
    }
