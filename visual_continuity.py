"""Deterministic visual continuity direction for Nūr's four-scene story arc.

No network access, media generation, or provider calls are made here.
"""
from __future__ import annotations

SCENE_DIRECTIONS = (
    "OPEN: establish the story's human subject and environment immediately; begin close enough to feel personal, with a clear visual question.",
    "DEVELOP: remain in the same visual world where the story allows; show a believable next action or consequence, not a disconnected stock image.",
    "RE-HOOK: preserve the story's visual identity but change shot scale, angle, or meaningful detail to create a fresh point of attention.",
    "PAYOFF: resolve the visual idea with a grounded action or calmer composition; make the final image feel like the natural next moment, not an unrelated inspirational scene.",
)


def scene_sequence_direction(scene_index: int, scene_count: int = 4) -> str:
    """Return a stable continuity instruction for a scene's position in the story."""
    count = max(1, int(scene_count))
    index = int(scene_index)
    if index < 0 or index >= count:
        raise ValueError("scene_index must identify a scene within scene_count")
    if count == 4:
        return SCENE_DIRECTIONS[index]
    if index == 0:
        return "Establish the story's human subject and visual world immediately."
    if index == count - 1:
        return "Resolve the visual idea with a grounded action or calm concluding composition."
    if index == count // 2:
        return "Introduce a meaningful visual change while preserving the established story identity."
    return "Continue the same visual world and show the next believable moment in the story."
