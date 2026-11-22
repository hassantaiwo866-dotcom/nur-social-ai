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

def repair_payoff_action(plan: dict) -> dict:
    """Append a practical, non-shaming next step when a provider omits one."""
    video = plan.get("video") if isinstance(plan, dict) else None
    scenes = video.get("scenes") if isinstance(video, dict) else None
    if not isinstance(scenes, list) or len(scenes) != 4 or not isinstance(scenes[-1], dict):
        return plan
    voiceover = str(scenes[-1].get("voiceover", "")).strip()
    action_words = ("choose", "take", "try", "pause", "start", "ask", "write", "move", "reach", "notice")
    if voiceover and not any(word in voiceover.lower() for word in action_words):
        scenes[-1]["voiceover"] = voiceover.rstrip(".!?") + ". Pause, then choose one small action that supports what matters to you."
    return plan


def complete_missing_captions(plan: dict) -> dict:
    """Derive safe captions when a model omits optional caption fields."""
    if not isinstance(plan, dict):
        return plan
    graphic = plan.get("graphic") if isinstance(plan.get("graphic"), dict) else {}
    video = plan.get("video") if isinstance(plan.get("video"), dict) else {}
    scenes = video.get("scenes") if isinstance(video.get("scenes"), list) else []
    if not str(plan.get("caption_image", "")).strip():
        headline = str(graphic.get("headline", "")).strip()
        subtext = str(graphic.get("subtext", "")).strip()
        plan["caption_image"] = "\n\n".join(part for part in (headline, subtext, "Choose one helpful next step.", "#SelfControl #PersonalGrowth #Nūr") if part)
    if not str(plan.get("caption_video", "")).strip():
        title = str(video.get("title", "")).strip()
        lines = [str(scene.get("voiceover", "")).strip() for scene in scenes if isinstance(scene, dict)]
        body = " ".join(line for line in lines if line)
        plan["caption_video"] = "\n\n".join(part for part in (title, body, "#SelfControl #Recovery #PersonalGrowth #Nūr") if part)
    return plan
