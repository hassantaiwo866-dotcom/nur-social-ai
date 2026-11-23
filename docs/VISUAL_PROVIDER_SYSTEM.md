# Visual provider system

## Purpose
Nūr's visual pipeline must use topic-matched, high-quality visual material rather than treating a generated text prompt as a finished scene. This document records the provider layer and its operational safeguards.

## Available provider adapters
- **Google Gemini image generation**: opt-in image generation using `GEMINI_API_KEY`. The default image model is `gemini-3.1-flash-lite-image`; override with `GEMINI_IMAGE_MODEL`. Image generation is a paid API capability; the provider adapter never runs merely because a text-generation key exists. Enable it deliberately in workflow configuration before production use.
- **Pixabay photographs and video**: optional stock media using `PIXABAY_API_KEY`. Search results are downloaded, not hotlinked. Photo dimensions are validated with Pillow. Video streams are checked with ffprobe. Attribution metadata and the Pixabay Content License reference are recorded for human review.
- **Wikimedia Commons**: existing image source remains available with its existing licence-screening rules.
- **Nūr motion graphics**: generated locally with Pillow/FFmpeg for explanatory sequences and branded transitions; these are not presented as photography or footage.
- **Agnes AI (under investigation; not currently integrated)**: Agnes publishes an OpenAI-compatible image/video API. Its current public materials identify `agnes-image-2.5-flash` and `agnes-video-2.5-flash`; an independent free-tier tracker reports both as free, while Agnes's own model reference explicitly describes the video Flash price as a limited-time `$0/sec` promotion. Do not treat this as a guaranteed daily allowance. Confirm the current model price and free-key access in the Agnes Platform console before sending production requests.

## Quality and safety rules
- Prefer real, relevant portrait footage for story-driven video when a suitable clip is available.
- Prefer AI-generated images when the desired scene is unavailable in stock libraries or would otherwise be visually incoherent.
- Never label an AI image as a photograph captured by a human.
- Keep source, creator, asset ID, licence and source page in the media manifest where supplied.
- Reject undersized, invalid or unplayable assets.
- Human review remains mandatory for composition, representation, rights, privacy, watermarking and relevance.
- Missing optional keys must not break the production workflow. They must not silently trigger a paid generation request.
- No public publishing is performed by this provider layer.

## API cost note
Gemini image generation has no free tier in the current published Gemini Developer API pricing. The 1K Gemini 3.1 Flash Lite Image output is listed at approximately USD 0.0336 per image, excluding input and any additional processing. Confirm current pricing and billing before enabling it. See https://ai.google.dev/gemini-api/docs/pricing.

## Current integration status
The provider adapters are implemented and unit-tested independently. The next integration step is to connect provider selection to the editorial poster and scene renderer, then inspect actual outputs on a phone. Adapter tests do not establish that the user's API credentials, account billing, stock search results or production assets are working.


## Cloudflare Workers AI — free-plan image generation

- Agnes Video 2.5 Flash has a separate gated adapter on this feature branch; it is not an automatic fallback and is not yet connected to production scene assembly. The paid `agnes-video-2.5` model is explicitly excluded. Replicate/MiniMax remains excluded.
- The Cloudflare adapter on this feature branch adds FLUX.2 Klein 4B (`@cf/black-forest-labs/flux-2-klein-4b`) as the image-generation path used by the cinematic generator. FLUX.1 Schnell remains available as a separately callable legacy adapter; it is not an automatic fallback. Agnes video is a separate provider adapter.
- Cloudflare documents a shared allowance of 10,000 Neurons per day on Workers Free, resetting at 00:00 UTC. Workers Free rejects requests after the allowance is exhausted. Workers Paid can bill usage above the free allocation, so Nūr requires the account to remain on **Workers Free**; do not enable this integration on Workers Paid.
- Legacy FLUX.1 Schnell is priced at 4.80 Neurons per 512x512 tile plus 9.60 Neurons per inference step. Its existing adapter requests four steps. FLUX.2 Klein 4B has separate pricing documented below. Both share the five-image per-process cap; actual daily output depends on dimensions and other Workers AI use in the same account.
- The API is disabled by default. After account verification, configure Actions secrets `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN`, then repository variables `CLOUDFLARE_FREE_PLAN_CONFIRMED=yes` and `ENABLE_CLOUDFLARE_IMAGE_GENERATION=true`.
- The adapter validates returned images, enforces the five-image process cap and has no paid fallback. On provider error or quota exhaustion, the generator continues to Pixabay, Wikimedia Commons and original local illustration.
- Adapter tests use mocked responses only. No live account, API token, quota or generated output has been verified.

Official references:
- Pricing and daily allocation: https://developers.cloudflare.com/workers-ai/platform/pricing/
- FLUX.1 Schnell model and REST API: https://developers.cloudflare.com/workers-ai/models/flux-1-schnell/
- API limits and exhausted-quota error: https://developers.cloudflare.com/workers-ai/platform/errors/


## Agnes AI investigation — 21 November 2026

- Agnes's official site currently advertises a Free API and lists Image 2.5 Flash and Video 2.5 Flash among its model family. Its official integration skill documents `agnes-image-2.5-flash` at `POST /v1/images/generations` and `agnes-video-2.5-flash` at `POST /v1/videos`, with video polling via `video_id` and `model_name`.
- The official model reference says Video 2.5 Flash is 720P and has a limited-time `$0/sec` promotion. The standard `agnes-video-2.5` is paid. Promotions can change; confirm in the authenticated platform console immediately before use.
- Public Agnes reference tables show free/default image request-rate limits by resolution (1K: 20 executable RPM; 2K: 10; 3K: 1; 4K: 1) and free/default video at 1 executable RPM. These are rate limits, not a published daily generation allowance. No reliable free-tier daily image/video quota was found in the public official material reviewed.
- An independent free-tier tracker checked 6 November 2026 reports free access to `agnes-image-2.5-flash` and temporary free access to `agnes-video-2.5-flash`, no card required, with video limited to about one effective request per minute. This is secondary evidence, not a guarantee or contract.
- API base: `https://apihub.agnes-ai.com/v1`; auth: `Authorization: Bearer <AGNES_API_KEY>`. Official integration instructions: https://github.com/AgnesAI-Labs/skills/tree/main/agnes-ai-models. Official site: https://agnes-ai.com/.
- Current Nūr status: `agnes_video.py` implements one-video text-to-video creation, polling by `video_id` + `model_name`, and MP4 download. It is disabled unless both `ENABLE_AGNES_VIDEO_GENERATION=true` and `AGNES_VIDEO_FREE_PRICE_CONFIRMED=yes` are set, and `AGNES_API_KEY` is present. It has a one-video process cap, defaults to 4 seconds, fixes output at 720P, and never selects the paid model or retries a paid route. The confirmation variable is an operator attestation, not an automated billing guarantee.
- Tests mock the HTTP API. They verify the model allowlist, opt-in, free-price gate, request cap, polling and basic MP4 validation. They do not verify the user's API key, account eligibility, price, quota, queue availability, or real generated video.
- The adapter is not wired into `nur_generator.py` yet. Before production wiring or a live request, verify the exact model price is still $0.00 in the authenticated Agnes Platform console and confirm the existing key has free access. Stop if payment is required or any non-zero price appears. Never ask the user to paste the key into chat or commit it.


## FLUX.2 Klein 4B integration — feature branch

- Model: `@cf/black-forest-labs/flux-2-klein-4b`; endpoint uses Cloudflare Workers AI REST API.
- The Klein REST endpoint requires multipart form data, including when no reference images are supplied. The adapter sends prompt, width and height as multipart fields.
- Klein uses a fixed four-step inference process; Nūr does not send a configurable `steps` field.
- Supports up to four reference images. Each reference image must be smaller than 512x512. The adapter validates this locally before making a request.
- Output dimensions are bounded to 256–1920px per side. Nūr's current photo pipeline enforces at least 512px per side to meet its image validation rules.
- The existing Cloudflare opt-in, explicit Workers Free confirmation, credential checks and five-image per-process cap are shared with FLUX.1 Schnell. The adapter never attempts paid fallback. If generation fails or the shared Workers AI free allowance is exhausted, the pipeline continues through its existing stock/local-illustration fallbacks.
- The adapter is disabled by default. Existing repository secrets `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN` are required, along with repository variables `CLOUDFLARE_FREE_PLAN_CONFIRMED=yes` and `ENABLE_CLOUDFLARE_IMAGE_GENERATION=true`.
- Unit tests use mocked HTTP responses. They do not verify the live Cloudflare credentials, actual account quota, generated image quality or production cost. A live smoke test requires a deliberate, separately approved generation.
- Pricing is not zero-cost per image: the current Cloudflare pricing table lists Klein 4B at 5.37 Neurons per 512x512 input tile and 26.05 Neurons per 512x512 output tile. Workers Free includes a shared daily 10,000-Neuron allowance. Check current account usage before enabling production runs.

Official references:
- FLUX.2 Klein 4B API and multipart/reference-image requirements: https://developers.cloudflare.com/workers-ai/models/flux-2-klein-4b/
- Workers AI pricing and free allowance: https://developers.cloudflare.com/workers-ai/platform/pricing/


## Agnes Video 2.5 Flash adapter — feature branch

- Model allowlist: `agnes-video-2.5-flash` only. The paid `agnes-video-2.5` model is never selected.
- Create endpoint: `POST https://apihub.agnes-ai.com/v1/videos`; poll endpoint: `GET https://apihub.agnes-ai.com/agnesapi?video_id=<VIDEO_ID>&model_name=agnes-video-2.5-flash`.
- The request is text-to-video, one output, 720P, 9:16 by default, and 4 seconds by default. The supported duration range is 4–12 seconds.
- The adapter is disabled by default and requires `ENABLE_AGNES_VIDEO_GENERATION=true`, `AGNES_VIDEO_FREE_PRICE_CONFIRMED=yes`, and the existing `AGNES_API_KEY` secret. Optional `AGNES_BASE_URL` must use HTTPS and end in `/v1`.
- The free-price confirmation is deliberately manual. Agnes currently describes the Flash price as a limited-time $0/sec promotion; promotions, access, rate limits, and queue availability can change. A successful API key or mocked test does not prove that a user's account is free.
- A hard cap allows one video per Python process. The adapter does not automatically retry video creation, switch to the paid model, or fall back to another paid provider. It polls the asynchronous task and downloads only a secure HTTPS MP4 result.
- Unit tests use mocked responses only. No live Agnes API request or video generation has been performed. The adapter is not connected to production scene assembly yet.

Official references:
- Agnes integration skill: https://github.com/AgnesAI-Labs/skills/tree/main/agnes-ai-models
- Agnes model catalogue: https://github.com/AgnesAI-Labs/skills/blob/main/agnes-ai-models/references/model_catalog.md
- Agnes platform: https://platform.agnes-ai.com/
