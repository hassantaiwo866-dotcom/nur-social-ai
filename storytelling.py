"""Audience connection and story-quality guidance for Nūr short-form content.

Pure local prompt composition. It does not make provider calls or assert app features.
"""
from __future__ import annotations

SCENE_AUDIENCE_DIRECTIONS = (
    "RECOGNITION: begin with a specific, relatable human moment; avoid generic motivational openings.",
    "TENSION: show the real friction, thought, or consequence without exaggerating or shaming the viewer.",
    "REFRAME: introduce a compassionate perspective or useful insight that changes how the viewer sees the situation.",
    "ACTION: resolve with one small, concrete, user-controlled step the viewer can try now.",
)

AUDIENCE_CONNECTION_RULES = (
    "Build one coherent human story across all four scenes, not four disconnected inspirational images.",
    "Use concrete everyday details and natural language that viewers could recognise in their own lives.",
    "The emotional movement should be recognition, tension, reframe, then practical action.",
    "Keep the viewer's dignity and agency intact. Never frame them as broken, weak, dirty, or a failure.",
    "Do not rely on guilt, fear, shame, fabricated statistics, exaggerated promises, or manipulative cliffhangers.",
    "Show Nūr's value through the helpful idea or practical action; do not force a brand mention into every scene.",
    "Keep the payoff specific enough to do immediately and small enough to feel achievable.",
)


def build_audience_connection_direction() -> str:
    """Return stable editorial guidance for AI-generated story plans."""
    lines = ["AUDIENCE CONNECTION AND STORY QUALITY:"]
    lines.extend(f"- {rule}" for rule in AUDIENCE_CONNECTION_RULES)
    lines.append("FOUR-SCENE EMOTIONAL ARC:")
    lines.extend(f"- Scene {index + 1}: {direction}" for index, direction in enumerate(SCENE_AUDIENCE_DIRECTIONS))
    return "\n".join(lines)
