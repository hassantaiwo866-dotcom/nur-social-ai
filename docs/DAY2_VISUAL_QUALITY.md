# Day 2 — editorial visual quality

## Objective
Improve the generated social media package without replacing the existing provider, image-sourcing, voiceover, rendering or human-approval architecture.

## Changes
- Scene caption panels now use four deliberate layouts rather than repeating one identical bottom panel. Text alignment and panel width vary by scene while preserving Nūr's forest, ivory and muted-gold palette.
- Caption text is measured and reduced in size when necessary. If it still cannot fit within three lines, generation stops with a clear error instead of silently clipping the message.
- Each scene receives a restrained slow zoom and alternating camera drift during FFmpeg rendering, so adjacent scenes do not all move in the same direction.
- Editorial-plan validation requires four distinct scene image prompts. QA repeats this check before the output is marked as passed.
- Added unit tests for the four scene layouts and vertical scene-frame rendering.

## Preserved safeguards
- Gemini → Groq → local editorial fallback remains unchanged.
- Wikimedia Commons licence screening and local original-illustration fallback remain unchanged.
- Generated content is not automatically published. Human review and the existing Telegram approval gate remain mandatory.
- Automated QA does not certify visual taste, source rights, factual accuracy, voice quality or publication readiness.

## Verification status
The source changes and unit tests are committed to the stabilisation branch. GitHub Actions must pass on the resulting head commit before Day 2 is considered technically verified. The generated output still needs human visual and audio review.

---

# Day 3 — photographic finishing and cinematic assembly

## Objective
Raise the minimum visual standard of the existing editorial pipeline without introducing a new paid API, weakening licence screening, or making generated illustrations look like photographs.

## Changes
- All selected source photographs receive restrained finishing: EXIF orientation correction, tonal balancing, modest colour/contrast adjustment and sharpening. No scene details are fabricated.
- Video scenes use one consistent editorial system: a restrained masthead, clear scene label, open lower-third typography, readable contrast and a four-part progress marker. This replaces the inconsistent caption-panel layouts.
- Scene joins use short video fades and audio crossfades rather than abrupt concatenation.
- The synthetic multi-tone ambient drone is removed from the final mix. Voiceover remains the primary audio; this avoids presenting a cheap synthetic tone as a music bed.
- Original local artwork remains clearly recorded as illustration, not photography. It receives the same finishing pipeline.

## Safeguards
- Wikimedia Commons licence screening and attribution remain in place.
- No external image or music API, extra credential, or paid service is introduced.
- Human visual, factual, rights and audio review remains required. Automated tests cannot certify that an image is beautiful, appropriate or correctly licensed.

## Verification
Unit tests cover photo processing, vertical frame dimensions and caption overflow. CI must pass on the resulting commit. A fresh generated package must still be inspected on a phone before publication.
