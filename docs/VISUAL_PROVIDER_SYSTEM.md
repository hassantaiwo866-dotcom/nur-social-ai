# Visual provider system

## Purpose
Nūr's visual pipeline must use topic-matched, high-quality visual material rather than treating a generated text prompt as a finished scene. This document records the provider layer and its operational safeguards.

## Available provider adapters
- **Google Gemini image generation**: opt-in image generation using `GEMINI_API_KEY`. The default image model is `gemini-3.1-flash-lite-image`; override with `GEMINI_IMAGE_MODEL`. Image generation is a paid API capability; the provider adapter never runs merely because a text-generation key exists. Enable it deliberately in workflow configuration before production use.
- **Pixabay photographs and video**: optional stock media using `PIXABAY_API_KEY`. Search results are downloaded, not hotlinked. Photo dimensions are validated with Pillow. Video streams are checked with ffprobe. Attribution metadata and the Pixabay Content License reference are recorded for human review.
- **Wikimedia Commons**: existing image source remains available with its existing licence-screening rules.
- **Nūr motion graphics**: generated locally with Pillow/FFmpeg for explanatory sequences and branded transitions; these are not presented as photography or footage.
- **Agnes AI (under investigation; not currently integrated)**: Agnes publishes an OpenAI-compatible image/video API. Its current public materials identify `agnes-image-2.5-flash` and `agnes-video-2.5-flash`; an independent free-tier tracker reports both as free, while Agnes's own model reference explicitly describes the video Flash price as a limited-time `$0/sec` promotion. Do not treat this as a guaranteed daily allowance. Confirm the current model price and free-key access in the Agnes Platform console before sending production requests.

## Per-scene source selection

The editorial plan now chooses a preferred visual source for each scene:

- `stock_video`: attempt a licensed Pixabay video clip for that scene only.
- `generated_still`: prefer the explicitly enabled image-generation path; if unavailable, use the existing Wikimedia/local fallback chain. Do not silently substitute a Pixabay stock photograph.
- `stock_photo`: use the licensed stock-photo path; do not call image-generation providers for this preference.
- `designed_visual`: create an original local Nūr illustration without calling an external visual provider.

Older plans receive a balanced four-scene default mix of stock video, generated still, stock video and designed visual. Explicit scene choices override these defaults. If a requested stock-video clip is unavailable, the scene falls back to the still-image chain; it does not repeat the stock-video search.

The source preference and actual asset provenance are different facts. The production manifest records editorial direction, while the asset attribution registry records the provider and media type actually used. A generated-still preference may still fall back to Wikimedia or a local illustration if no generation provider is enabled.

## Quality and safety rules
- Select the source per scene according to the story; stock footage is neither a blanket default nor prohibited.
- Prefer real, relevant footage when it is the most truthful and useful way to show the scene.
- Prefer generated or designed visuals when a coherent fictional scene, specific visual metaphor or original composition is more appropriate.
- Never label an AI image as a photograph captured by a human.
- Keep source, creator, asset ID, licence and source page in the media manifest where supplied.
- Reject undersized, invalid or unplayable assets.
- Human review remains mandatory for composition, representation, rights, privacy, watermarking and relevance.
- Missing optional keys must not break the production workflow. They must not silently trigger a paid generation request.
- No public publishing is performed by this provider layer.

## Character continuity limitations

Recurring fictional characters may be declared in `video.characters` and referenced by stable IDs in each scene's `character_ids`. Their same visual description is reused in prompts, and the production run manifest records the character references.

This is **text-guided continuity only**. Current visual providers do not receive character reference images through this pipeline, so matching identity across generated scenes is not guaranteed. Separate stock clips cannot guarantee the same performer. The manifest records this limitation and flags scenes where a recurring character is assigned to stock footage or photography. Do not describe this capability as reference-based or guaranteed until a provider adapter and rendered tests support it.

## API cost note
Gemini image generation has no free tier in the current published Gemini Developer API pricing. The 1K Gemini 3.1 Flash Lite Image output is listed at approximately USD 0.0336 per image, excluding input and any additional processing. Confirm current pricing and billing before enabling it. See https://ai.google.dev/gemini-api/docs/pricing.

## Current integration status
Per-scene source preferences are now connected to the scene-generation pipeline on the cinematic direction feature branch. Provider adapters remain independently tested, and a real end-to-end rendered output has not yet been reviewed for this change. Adapter tests do not establish that the user's API credentials, account billing, stock search results or production assets are working.

Composition, depth and typography preferences are recorded per scene. Prompt direction can guide composition and depth, but dedicated animated bento rendering, glass/3D compositing and the hyperbold typography renderer remain future implementation work. The current renderer does not yet fully realise those treatments.


## Cloudflare Workers AI — free-plan image generation

- Agnes is not currently integrated. It remains a candidate pending a verified free-key smoke test and a check of current model pricing in the platform console. Do not infer that every Agnes model is free: `agnes-video-2.5` is listed as paid, while `agnes-video-2.5-flash` is the temporary free-price candidate. Replicate/MiniMax remains excluded.
- The only currently integrated visual AI API is Cloudflare Workers AI FLUX.1 Schnell: `@cf/black-forest-labs/flux-1-schnell`. Agnes investigation does not change production provider selection yet.
- Cloudflare documents a shared allowance of 10,000 Neurons per day on Workers Free, resetting at 00:00 UTC. Workers Free rejects requests after the allowance is exhausted. Workers Paid can bill usage above the free allocation, so Nūr requires the account to remain on **Workers Free**; do not enable this integration on Workers Paid.
- The model is priced at 4.80 Neurons per 512x512 tile plus 9.60 Neurons per inference step. Nūr requests four steps and limits generation to five images per Python process. Actual daily output depends on image dimensions and other Workers AI use in the same account.
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
- Current Nūr status: Agnes adapter and production calls are not present. Do not restore/enable them until an account's free access and $0 model pricing have been checked and a minimal test has succeeded without payment details or billing exposure.
- Next validation: user creates an Agnes account/key privately; check the model price and key type in the platform console; test one image and one 4-second 720P video, record sanitized status/usage only, and stop on any payment-required or non-zero-price response. Never ask the user to paste the key into chat or commit it.
