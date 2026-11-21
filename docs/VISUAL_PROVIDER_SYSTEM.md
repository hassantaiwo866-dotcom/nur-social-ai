# Visual provider system

## Purpose
Nūr's visual pipeline must use topic-matched, high-quality visual material rather than treating a generated text prompt as a finished scene. This document records the provider layer and its operational safeguards.

## Available provider adapters
- **Google Gemini image generation**: opt-in image generation using `GEMINI_API_KEY`. The default image model is `gemini-3.1-flash-lite-image`; override with `GEMINI_IMAGE_MODEL`. Image generation is a paid API capability; the provider adapter never runs merely because a text-generation key exists. Enable it deliberately in workflow configuration before production use.
- **Pixabay photographs and video**: optional stock media using `PIXABAY_API_KEY`. Search results are downloaded, not hotlinked. Photo dimensions are validated with Pillow. Video streams are checked with ffprobe. Attribution metadata and the Pixabay Content License reference are recorded for human review.
- **Wikimedia Commons**: existing image source remains available with its existing licence-screening rules.
- **Nūr motion graphics**: generated locally with Pillow/FFmpeg for explanatory sequences and branded transitions; these are not presented as photography or footage.

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


## Free visual model integration (initial)

- `free_visual_models.py` adds Agnes Image 2.5 Flash and Agnes Video 2.5 Flash adapters. Image generation is 1K portrait. Video is 720P, 4–12 seconds, async with bounded polling.
- Free-only allowlisting blocks other model IDs. Video requires `AGNES_FREE_VIDEO_CONFIRMED=yes` because the $0 offer is promotional and may change; verify it in your account before running. No paid fallback exists.
- The planned third model (Replicate MiniMax Video-01) is recorded but disabled because free trial access is not guaranteed. It is not called.
- These adapters are not yet wired into production scene/poster selection; tests use mocked provider responses. Next step: connect opt-in image generation as a fallback and AI video only when stock video misses, with one-video-per-day cap.


## Production integration — Agnes free visual models

- `AGNES_API_KEY` is an optional Actions secret. Image model opt-in uses the `ENABLE_AGNES_IMAGE_GENERATION` repository variable and the allowlisted `agnes-image-2.5-flash` model. It is used as an image fallback before Pixabay/Commons/local art.
- Video model opt-in uses `ENABLE_AGNES_VIDEO_GENERATION` and `AGNES_FREE_VIDEO_CONFIRMED=yes`; only `agnes-video-2.5-flash`, 720P, 4 seconds is allowed. It is attempted only if Pixabay did not return a usable clip and is capped at one generated video per batch day.
- `NUR_FREE_ONLY=true` is passed in production. Gemini image generation (paid) is blocked under this default; no paid provider fallback is invoked.
- Video free pricing is promotional. Verify current $0 price in the provider console before enabling; if uncertain, keep it off. Provider adapters use mocked tests only and live API output has not been verified.
- Replicate MiniMax Video-01 is the planned third model but remains disabled; trial credits are not a guaranteed free service. No integration can charge through this pipeline.
