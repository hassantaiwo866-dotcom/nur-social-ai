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
- The 4:5 social graphic is now photo-led: a large rounded hero image, restrained Nūr masthead, strong headline hierarchy and a clean editorial footer replace the smaller inset-photo layout.
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


## Day 4 — multi-source visual production

- Added an optional visual-provider layer for Gemini image generation and Pixabay photo/video retrieval.
- The poster and still-image scenes can use Gemini-generated imagery only when `ENABLE_GEMINI_IMAGE_GENERATION=true`; the existing Gemini text key alone does not trigger image generation.
- Pixabay can supply both photographs and portrait video clips through the optional `PIXABAY_API_KEY` secret. Video downloads are checked with ffprobe before use.
- Scene rendering now prefers actual portrait video footage when a usable Pixabay clip is returned. It places Nūr typography on a transparent overlay and uses the existing voiceover as the scene audio. If no clip is available, it falls back through the image-provider chain.
- All external assets retain source and attribution metadata for manual review.

### Required configuration
- Add `PIXABAY_API_KEY` as an Actions secret to enable stock photo/video retrieval.
- Set the Actions repository variable `ENABLE_GEMINI_IMAGE_GENERATION` to `true` only after confirming Gemini API billing. It is off by default.
- No new provider key is required for Gemini image generation; the existing `GEMINI_API_KEY` is reused.

### Limits
- Pixabay search may not return a suitable portrait clip for every scene. The renderer falls back to still imagery.
- Generated image and stock footage quality still require human inspection. Automated tests verify integration mechanics, not artistic quality or legal clearance.


## Nūr primary colour standard — Day 5

- Emerald green `#0B5D3B` is the primary brand colour across generated media. It is used for scene masthead rules, caption accents, progress markers and closing-card backgrounds.
- Deep forest `#064E3B` is a secondary depth colour, not a replacement for the primary emerald.
- Warm ivory `#F5F0E1`, charcoal `#1C1C1C` and muted gold `#D4AF37` remain supporting colours.
- Photography and footage retain natural colour. Green is carried by graphic identity, overlays and motion design—not by indiscriminately tinting source footage.
- Poster layout remains photo-led; green is used as a restrained editorial accent rather than a large colour wash.
