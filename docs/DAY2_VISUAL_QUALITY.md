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


## Day 6 — scene-specific transitions and emerald branding\n\n- Video assembly accepts a transition per scene boundary, with an explicit allowlist of FFmpeg xfade transitions. Unsupported values safely fall back to fade.\n- The story plan's transition metadata is passed to the final assembly rather than ignored. The closing card uses a restrained fade.\n- Nūr primary emerald `#0B5D3B` remains the signature graphic colour; source footage is not recoloured to green.\n- The transition system currently supports fades, wipes, slides, smooth slides and circle-open. Avoid overusing flashy transitions; the editorial default remains a fade.\n

## Day 7 — voice-led audio polish

- Narration segments receive a restrained voice chain: high-pass rumble removal, low-pass harshness control, compression, loudness normalization and short fades at the segment edges.
- Scene narration is concatenated sequentially, not crossfaded over the next speaker line. Video transitions remain independent.
- The final audio is trimmed to the crossfaded video duration and normalized to a social-video target. No synthetic ambient tone or paid music source is introduced.
- This is technical audio processing, not a substitute for listening to every generated voice track. Check clipping, pronunciation, pacing and naturalness during Telegram review.


## Day 8 — animated editorial motion accents

- Each rendered scene now receives a short, moving emerald accent line. It travels across the masthead rule for documentary scenes and the paper caption zone for collage styles.
- Direction alternates by scene to prevent repeated motion. The accent is time-limited and remains a small graphic detail, not a persistent distraction.
- Stock-video and still-image scene renderers both use the motion accent filter. Source footage retains its natural colour.
- Motion is rendered through FFmpeg; manual review is required for placement, visual collisions and timing on the final output.


## Day 8 — animated editorial motion accents

- A travelling emerald line animates across the masthead rule in documentary scenes and across the paper caption zone in collage scenes.
- Its direction alternates by scene, and the motion naturally exits the frame after a short duration; it is not a persistent animated distraction.
- Both stock-video and still-image renders apply the accent in FFmpeg. Stock footage retains natural colour.
- Review placement and timing on actual outputs before publication; the automated test validates filter construction, not visual aesthetics.

## Day 2 implementation — scene-directed camera motion

- Still-image scenes now consume the editorial plan's `movement` field instead of always using the same alternating crop drift.
- Supported restrained presets: slow push in, gentle lateral drift, subtle tilt down, slow pull back, slow forward tracking, gentle pan left and gentle pan right.
- Unknown movement descriptions safely fall back to an alternating lateral drift.
- This improves connection between scene direction and motion while retaining the same image provider, FFmpeg renderer and no-cost local pipeline.
- Tests validate generated FFmpeg crop expressions for two directions. CI is required before considering the implementation verified.


## Day 2 implementation — scene-aware prompt composition

- Generation prompts preserve the editorial subject/action while adding premium documentary realism, deliberate focal hierarchy, realistic natural light and camera texture, vertical 9:16 framing, and overlay-safe negative space.
- Generation prompts prohibit embedded text, logos, watermarks, UI, collage/poster layouts, artificial green tint and staged stock-photo poses.
- Scene camera direction, movement and story beat are supplied to image-generation providers where available.
- Stock-library searches use concise subject/action keywords rather than long cinematic instructions, improving query relevance and reducing noise.
- The new `visual_prompting.py` module is deterministic and local-only. It makes no API calls and does not alter provider enablement, pricing, licensing or fallback behavior.
- Unit tests cover subject preservation, composition constraints, empty prompts, stock-query shortening and fallback terms.


## Day 2 implementation — four-scene visual continuity

- Added a deterministic scene-sequence director for the four story beats: opening, development, re-hook and payoff.
- Image-generation prompts now receive a scene-position instruction: establish the human subject and visual world, continue with the next believable moment, renew attention through a meaningful framing/detail change, then resolve with a grounded action.
- Continuity is guidance, not a forced same-person/same-location rule. It explicitly allows the story to change setting or subject when the editorial plan requires it.
- Existing scene prompts, camera directions, movement, provider selection, stock search and licensed-asset fallbacks remain intact.
- The module is local-only and introduces no API calls, credentials, dependencies or generation costs.
- Unit tests cover the ordered four-beat arc, non-standard scene counts, invalid indices and prompt integration.
- Automated tests verify deterministic instructions, not whether generated scenes actually look continuous. Inspect the resulting four-scene video before publication.


## Day 6 — transition safety verification

- The existing editor supports per-boundary FFmpeg transitions, normalizes the `soft_cut` alias to `fade`, and falls back to `fade` for unsupported transition names.
- Added tests verifying unsupported names do not reach FFmpeg, the alias is normalized, and segments shorter than the configured transition are rejected before FFmpeg is invoked.
- This stage hardens existing transition functionality; it does not add new visual transition effects or alter editorial choices.
- CI verification pending.


## Day 7 — voiceover filter duration safety

- Voiceover finishing already includes high/low-pass filtering, compression, loudness normalization and short fades.
- Added finite-duration validation to prevent invalid FFmpeg filter values from NaN or infinity. Negative/very short durations retain a safe minimum of 0.25 seconds.
- Regression tests cover negative and non-finite durations.
- No additional audio provider, music service, dependency or cost was introduced. Automated verification pending.


## Day 8 — animated emerald accent

- Replaced the static accent rule with a restrained horizontal travel animation using FFmpeg's per-frame drawbox expression.
- Alternates travel direction across scenes; cinematic-documentary and collage styles retain their respective vertical positions.
- Motion duration is bounded; invalid values use a safe default.
- Regression tests verify direction, colour, style position and duration handling. Visual appearance still requires inspection of an actual render.
- No new dependency, API, credential or cost.


### Animated brand accent expression correction

The FFmpeg `drawbox` x-expression now uses explicit addition for rightward travel and subtraction for leftward travel. This avoids emitting a redundant `+-1*` expression and keeps the filter expression aligned with the directional regression tests. The animation remains bounded by the existing duration clamp.
