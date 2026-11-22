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
