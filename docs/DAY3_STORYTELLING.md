# Day 3 — storytelling and visual direction

## Goal
Short videos become coherent micro-stories rather than four disconnected scenes. Default progression: Hook/Open Loop → Development → Re-hook → Payoff.

## Story rules
- Scene 1 begins with curiosity, relatable tension or a useful counterpoint. No logo intro.
- Scene 2 develops the idea with concrete context.
- Scene 3 changes perspective or adds a detail to renew interest.
- Scene 4 resolves the central question and offers a compassionate, practical action.
- No shame, guilt, fear, fabricated statistics or manipulative cliffhangers.
- A natural loop is optional; clarity and truthful payoff come first.

## Visual styles
- cinematic_documentary: calm premium real-world footage/photography (default).
- tactile_editorial_collage: selective torn-paper, marker, paper texture and editorial cutout elements.
- hybrid_documentary_collage: documentary base with restrained tactile overlays.
Do not force collage into every scene. Preserve Nūr forest green, warm ivory and muted gold. Avoid clutter. Selective stop-motion-like overlay motion is an option, not a blanket frame-rate change.

## Scene metadata
Each scene includes voiceover, on-screen text, image prompt, camera direction, movement, asset type, transition and sound-effect direction. Defaults keep older provider responses compatible.

## Visual treatment integration
The renderer now supports a restrained tactile caption treatment for the collage and hybrid styles: warm-ivory paper panels with imperfect cut edges and a marker-like gold accent. Documentary style retains the original clean caption system. The paper treatment is rendered for both still scenes and transparent video overlays. This is a first implementation of the style—not a full scrapbook animation system; Polaroid frames, torn-paper scene transitions, animated marker strokes, paper texture and dedicated tactile sound libraries remain future work.

## Verification
Prompt and local validation enforce story structure and scene direction. Unit tests validate accepted/rejected plans. This does not verify actual visual quality, pacing, sound design, provider availability or collage rendering; generated media still needs human review.
