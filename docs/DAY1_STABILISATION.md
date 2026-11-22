# Day 1 — provider and media resilience

## Scope
Addresses the 21 November 2026 Actions failures: fixed model IDs returning HTTP 404, and Pollinations returning HTTP 402 after the local editorial fallback had succeeded.

## Text providers
Order remains Gemini → Groq → local editorial fallback. Gemini is queried through the authenticated `v1beta/models` catalogue and filtered for `generateContent`; Groq uses its authenticated `/openai/v1/models` catalogue. Configured `GEMINI_MODEL`/`GROQ_MODEL` values are preferences only and are used only when listed. Otherwise the code selects an available Gemini Flash model or an available preferred Groq model, then a deterministic sorted choice. Diagnostics are bounded and never print credentials.

Catalogue presence does not guarantee quota or successful inference. A real Actions run is still required to verify account access.

## Image sourcing
Pollinations and Pexels are not dependencies. Pexels' official API page and Help Centre currently state that new API key issuance is paused. Nūr does not require or request a Pexels key: https://www.pexels.com/api/

1. Wikimedia Commons is the external image source.
2. Commons results require a licence URL and identified CC0, public-domain, CC BY or CC BY-SA licence. NC/ND and declared restrictions are rejected.
3. Downloads are validated with Pillow, checked for minimum dimensions, cropped and encoded as JPEG.
4. Assets are not intentionally reused in one run. Provider, asset ID, creator, source page and licence are recorded in `output/latest_post.json`.
5. If Commons is unavailable or no acceptable image is found, the pipeline generates original Nūr-coloured editorial artwork locally using Pillow. It is recorded as `illustration_not_photograph`, with original-artwork metadata. It is not represented as a stock photograph.

Commons metadata can be incomplete or unreliable, particularly for multi-licensed works. This is a screening step, not legal advice. Human review must inspect the original file page, licence terms, attribution, watermarking, privacy/personality and trademark issues. Local illustrations also require human review for composition and relevance.

## Workflow and safeguards
No Pexels secret is needed. Existing local editorial fallback, branded graphic, four-scene video, voiceover and QA flow remain. QA still requires human review. Telegram retains `NUR_APPROVED=yes` and passing QA. No automatic social publishing is added.

## Verification
Unit tests cover model discovery/preference, Commons licence screening and local illustration fallback. A full Actions run with real text-provider secrets remains necessary to verify account access, quota, live Commons sourcing or local fallback, media assembly and final QA.

## 22 November 2026 — provider output/model failure recovery

- The latest production log showed Gemini's catalogue returning `gemini-2.5-flash`, while inference rejected it for the account and recommended `gemini-3.8-flash`. Discovery now prefers that recommended model when it is listed, then `gemini-3.0-flash`, before older Flash choices.
- Editorial-plan validation now fills missing image/video captions from the generated headline, subtext, video title and scene voiceovers. This prevents an otherwise complete Groq plan from being discarded solely because `caption_image` was omitted.
- This is defensive compatibility; it does not guarantee either provider's quota or model access. Live workflow verification remains required.


## 22 November 2026 — media assembly and provider resilience

- Normalize scene beat labels to the required four-beat sequence based on scene position, while retaining provider scene content. This prevents noncanonical wording from rejecting an otherwise valid plan.
- Shorten inference timeouts to connect/read bounds so a provider timeout moves promptly to the next provider.
- Set the moving accent drawbox to evaluate expressions per frame, enabling its time-based horizontal animation.
- Lower the voice low-pass cutoff to 11 kHz to stay below Nyquist for 24 kHz voice tracks.
- This addresses the errors observed in production run #37; full media generation still requires a fresh Actions run.


## 22 November 2026 — run #39 FFmpeg compatibility and payoff repair

- Removed unsupported `eval=frame` from FFmpeg's `drawbox` filter. The time-based x expression remains; no unsupported filter option is passed.
- Added deterministic payoff repair when a generated final scene lacks a practical action. The original voiceover is preserved and a concise, non-shaming next step is appended before validation.
- Gemini read timeouts remain provider-side failures; the existing Groq/local fallback remains active.
- Added regression coverage for payoff repair. CI and a real FFmpeg render are required before claiming production success.


## 22 November 2026 — run #40 still-image render compatibility

- Run #40 reached the local illustration fallback after Pixabay and Wikimedia were unavailable, then failed in the still-image FFmpeg renderer.
- The emerald accent used time/width expressions that are not portable across FFmpeg filter builds. Both still-image and stock-video renderers share this accent helper.
- Replaced moving x expressions with alternating fixed coordinates. This intentionally prioritizes reliable rendering over the accent's animation; the emerald brand element remains visible.
- External media failures remain recoverable: the local original-illustration fallback is expected to carry production forward. A full workflow run is still required to verify rendering and artifact upload.
