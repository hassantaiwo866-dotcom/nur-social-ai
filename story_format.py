"""Story format and visual direction rules for Nūr short-form content."""
from __future__ import annotations

STORY_BEATS = ("HOOK / OPEN LOOP", "DEVELOPMENT", "RE-HOOK", "PAYOFF")
VISUAL_STYLES = ("cinematic_documentary", "tactile_editorial_collage", "hybrid_documentary_collage")

def scene_defaults_for_beat(scene: dict) -> dict:
    beat = str(scene.get("beat", "")).upper()
    defaults = {"camera_direction": "Natural cinematic framing; preserve visual clarity.", "movement": "Subtle camera movement only.", "visual_asset_type": "stock_footage_or_photograph", "transition": "soft_cut", "sound_effect": "none"}
    if "HOOK" in beat:
        defaults.update(camera_direction="Immediate visual detail or human moment; no establishing logo shot.", movement="Purposeful, restrained push-in or movement that earns attention.")
    elif "RE-HOOK" in beat:
        defaults.update(camera_direction="Change framing or subject detail to renew visual interest.", movement="Distinct but restrained movement; avoid repeating the previous shot.")
    elif "PAYOFF" in beat:
        defaults.update(camera_direction="Clear, grounded composition supporting the practical takeaway.", movement="Slow, stable movement or deliberate hold.")
    return defaults

def validate_story_plan(plan: dict) -> None:
    video = plan.get("video")
    if not isinstance(video, dict): raise ValueError("video must be an object")
    if video.get("visual_style", "cinematic_documentary") not in VISUAL_STYLES: raise ValueError("unknown visual style")
    scenes = video.get("scenes")
    if not isinstance(scenes, list) or len(scenes) != 4: raise ValueError("story arc requires exactly four scenes")
    for i, scene in enumerate(scenes):
        beat = str(scene.get("beat", "")).upper()
        if STORY_BEATS[i].split(" / ")[0] not in beat: raise ValueError(f"scene {i+1} must represent {STORY_BEATS[i]}")
        for field in ("voiceover", "on_screen_text", "image_prompt"):
            if not str(scene.get(field, "")).strip(): raise ValueError(f"scene {i+1} missing {field}")
        for field in ("camera_direction", "movement", "visual_asset_type", "transition", "sound_effect"):
            if not str(scene.get(field, "")).strip(): raise ValueError(f"scene {i+1} missing direction: {field}")
    if not any(word in scenes[-1]["voiceover"].lower() for word in ("choose", "take", "try", "pause", "start", "ask", "write", "move", "reach", "notice")): raise ValueError("payoff scene should offer a practical next step")
