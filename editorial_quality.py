"""Deterministic editorial-quality diagnostics for Nūr content plans.

This module provides advisory checks only. It does not block generation,
replace human review, or make claims about audience performance.
"""
from __future__ import annotations

from typing import Any

ACTION_CUES = (
    "choose", "try", "pause", "start", "ask", "write", "move", "reach",
    "notice", "identify", "take", "set", "put", "open", "close", "walk",
    "breathe", "plan", "remove", "turn", "focus", "return",
)
CANONICAL_BEATS = ("HOOK / OPEN LOOP", "DEVELOPMENT", "RE-HOOK", "PAYOFF")


def evaluate_editorial_plan(plan: dict[str, Any]) -> dict[str, Any]:
    """Return a transparent advisory score and diagnostic list for a plan."""
    video = plan.get("video") if isinstance(plan, dict) else {}
    video = video if isinstance(video, dict) else {}
    scenes = video.get("scenes") if isinstance(video.get("scenes"), list) else []
    graphic = plan.get("graphic") if isinstance(plan, dict) else {}
    graphic = graphic if isinstance(graphic, dict) else {}

    checks: list[dict[str, Any]] = []

    def add(name: str, passed: bool, weight: int, message: str) -> None:
        checks.append({"name": name, "passed": bool(passed), "weight": weight, "message": message})

    add("four_scene_structure", len(scenes) == 4, 20,
        "The story uses exactly four scenes." if len(scenes) == 4 else "Expected four scenes for the intended story arc.")

    voiceovers = [str(scene.get("voiceover", "")).strip() for scene in scenes if isinstance(scene, dict)]
    complete_voiceovers = len(voiceovers) == 4 and all(voiceovers)
    add("voiceover_completeness", complete_voiceovers, 20,
        "All four scenes have narration." if complete_voiceovers else "One or more scenes lack narration.")

    prompts = [str(scene.get("image_prompt", "")).strip().lower() for scene in scenes if isinstance(scene, dict)]
    unique_prompts = len(prompts) == 4 and len(set(prompts)) == 4 and all(prompts)
    add("visual_prompt_distinction", unique_prompts, 15,
        "Scene visual prompts are distinct." if unique_prompts else "Visual prompts are missing or duplicated.")

    beats = [str(scene.get("beat", "")).strip().upper() for scene in scenes if isinstance(scene, dict)]
    correct_arc = len(beats) == 4 and beats == list(CANONICAL_BEATS)
    add("story_arc", correct_arc, 15,
        "Scenes follow Hook, Development, Re-hook, Payoff." if correct_arc else "Scene beat labels or order do not match the intended arc.")

    payoff = voiceovers[-1].lower() if voiceovers else ""
    actionable = any(cue in payoff for cue in ACTION_CUES)
    add("practical_payoff", actionable, 15,
        "The final narration suggests a concrete action." if actionable else "The final narration may need a specific, achievable action.")

    caption = str(plan.get("caption_video", "")).strip()
    caption_present = bool(caption)
    add("video_caption", caption_present, 15,
        "A video caption is present." if caption_present else "The video caption is missing.")

    score = sum(check["weight"] for check in checks if check["passed"])
    warnings = [check["message"] for check in checks if not check["passed"]]
    return {
        "score": score,
        "max_score": 100,
        "checks_passed": sum(check["passed"] for check in checks),
        "checks_total": len(checks),
        "status": "advisory",
        "warnings": warnings,
        "checks": checks,
    }
