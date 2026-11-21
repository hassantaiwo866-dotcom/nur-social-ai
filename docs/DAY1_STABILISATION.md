# Day 1 — provider and media resilience

## Scope
Addresses the 21 November 2026 Actions failures: fixed model IDs returning HTTP 404, and Pollinations returning HTTP 402 after the local editorial fallback had succeeded.

## Text providers
Order remains Gemini → Groq → local editorial fallback. Gemini is queried through the authenticated `v1beta/models` catalogue and filtered for `generateContent`; Groq uses its authenticated `/openai/v1/models` catalogue. Configured `GEMINI_MODEL`/`GROQ_MODEL` values are preferences only and are used only when listed. Otherwise the code selects an available Gemini Flash model or an available preferred Groq model, then a deterministic sorted choice. Diagnostics are bounded and never print credentials.

Catalogue presence does not guarantee quota or successful inference. A real Actions run is still required to verify account access.

## Image sourcing
Pollinations is removed after its HTTP 402 response.
1. Pexels is attempted when `PEXELS_API_KEY` is configured.
2. Wikimedia Commons is attempted when Pexels is absent or fails.
3. Commons requires a licence URL and identified CC0, public-domain, CC BY or CC BY-SA licence. NC/ND and declared restrictions are rejected.
4. Downloads are validated with Pillow, checked for minimum dimensions, cropped and encoded as JPEG.
5. Assets are not intentionally reused in one run. Provider, asset ID, creator/photographer, source page and licence are recorded in `output/latest_post.json`.
6. If no acceptable source is found, generation stops with a clear diagnostic.

Commons metadata can be incomplete or unreliable, particularly for multi-licensed works. This is a screening step, not legal advice. Human review must inspect the original file page, licence terms, attribution, watermarking, privacy/personality and trademark issues.

## Workflow and safeguards
`PEXELS_API_KEY` is optional; Commons is the no-key fallback. Secrets stay in GitHub Actions settings. Existing local editorial fallback, branded graphic, four-scene video, voiceover and QA flow remain. QA still requires human review. Telegram retains `NUR_APPROVED=yes` and passing QA. No automatic social publishing is added.

## Verification
Unit tests cover model discovery/preference and Commons licence screening. A full Actions run with real secrets remains necessary to verify account access, quota, image sourcing, media assembly and final QA.
