# Day 2 — editorial visual quality

## Objective
Improve the generated social media package without replacing the existing provider, image-sourcing, voiceover, rendering or human-approval architecture.

## Changes
- Scene caption panels now use four deliberate layouts rather than repeating one identical bottom panel. Text alignment and panel width vary by scene while preserving Nūr's forest, ivory and muted-gold palette.
- Caption text is measured and reduced in size when necessary. If it still cannot fit within three lines, generation stops with a clear error instead of silently clipping the message.
- Each scene receives a restrained, slow zoom treatment during FFmpeg rendering.
- Editorial-plan validation requires four distinct scene image prompts. QA repeats this check before the output is marked as passed.
- Added unit tests for the four scene layouts and vertical scene-frame rendering.

## Preserved safeguards
- Gemini → Groq → local editorial fallback remains unchanged.
- Wikimedia Commons licence screening and local original-illustration fallback remain unchanged.
- Generated content is not automatically published. Human review and the existing Telegram approval gate remain mandatory.
- Automated QA does not certify visual taste, source rights, factual accuracy, voice quality or publication readiness.

## Verification status
The source changes and unit tests are committed to the stabilisation branch. GitHub Actions must pass on the resulting head commit before Day 2 is considered technically verified. The generated output still needs human visual and audio review.
