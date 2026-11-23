# Nūr Social AI

Prelaunch editorial media pipeline for Nūr: privacy-first self-control, protection, recovery and personal growth, communicated without shame, guilt or fear.

## Pipeline
- Editorial plan: Gemini → Groq → built-in local fallback.
- Models are discovered from each configured account's live model catalogue. `GEMINI_MODEL` and `GROQ_MODEL` are preferences used only when listed by that account.
- Visuals: optional Cloudflare Workers AI FLUX.1 Schnell imagery on a confirmed Workers Free account, optional Pixabay stock photos/video, Wikimedia Commons with licence screening, and locally rendered motion graphics. Paid Gemini image generation remains disabled in free-only mode. Real Pixabay portrait footage is preferred for scenes when available; still imagery remains a fallback. Provider adapters are documented in `docs/VISUAL_PROVIDER_SYSTEM.md`.
- Production: photo-led editorial poster, graded source photography, consistent vertical scene design, Edge TTS voiceover and FFmpeg crossfade assembly.
- Human review remains mandatory. Telegram publishing retains its explicit `NUR_APPROVED=yes` gate and passing-QA requirement.

## GitHub Actions secrets
- `GEMINI_API_KEY` — optional text provider.
- `GROQ_API_KEY` — optional fallback text provider.
- `PIXABAY_API_KEY` — optional stock photograph and portrait-video search.
- `CLOUDFLARE_ACCOUNT_ID` and `CLOUDFLARE_API_TOKEN` — optional Cloudflare Workers AI image generation credentials.
- `TELEGRAM_BOT_TOKEN` — optional bot token used only for private review delivery.
- `TELEGRAM_REVIEW_CHAT_ID` — optional dedicated review chat ID; if omitted, the existing `TELEGRAM_CHAT_ID` is reused.

Keep credentials in repository Actions secrets, never source files. Cloudflare image generation is disabled by default. To use it, keep the account on the **Workers Free plan**, add the two Cloudflare values above as Actions secrets, then set repository variables `CLOUDFLARE_FREE_PLAN_CONFIRMED=yes` and `ENABLE_CLOUDFLARE_IMAGE_GENERATION=true`. The pipeline allows at most five FLUX.1 Schnell images per Python run and never switches to a paid provider. Do not use a Workers Paid account for this free-only setup. Gemini image generation remains paid and disabled in the normal free-only workflow. At least one text provider key is recommended.

## Local run
Python 3.11, FFmpeg and ffprobe are required.

```bash
python -m pip install -r requirements.txt
python nur_generator.py
```

Generated media is written to `output/`. Actions uploads it as an artifact and, when both Telegram review secrets are configured, sends the image and video to the configured private review chat. This preview path is separate from public publishing. The existing `telegram_publisher.py` still requires `NUR_APPROVED=yes` and passing QA.

## Image rights and review
Commons metadata can be incomplete or unreliable. The pipeline accepts only identified CC0, public-domain, CC BY or CC BY-SA licences with a licence URL and skips declared restrictions. Attribution is recorded, but humans must inspect the original file page and conditions. If Commons cannot provide a suitable image, the pipeline creates original Nūr-branded artwork locally; it is explicitly labelled as an illustration, not a photograph.

See [visual provider system](docs/VISUAL_PROVIDER_SYSTEM.md), [Day 1 stabilisation notes](docs/DAY1_STABILISATION.md), [Day 2 visual quality notes](docs/DAY2_VISUAL_QUALITY.md) and [private Telegram review setup](docs/TELEGRAM_PRIVATE_REVIEW.md).


## Day 4 — direct image-to-video handoff

The Day 4 feature branch sends a Nūr-generated scene image to Agnes Video 2.5 Flash as inline Base64 in the `first_frame` field (`mode: img2video`). No temporary hosting, public URL, storage subscription, or R2 credentials are required. Existing stock-video footage remains preferred; Agnes is optional and local FFmpeg still-motion remains the fallback.

Live use remains disabled until configured. It requires the existing `AGNES_API_KEY` secret and explicit opt-in plus confirmation that the Flash model is currently $0. No paid model fallback is permitted. Images are limited to 10 MiB and PNG/JPEG/WebP. The API receives image bytes directly; no image hosting is created. Tests use mocked requests only; no live Agnes generation has been performed.


## Day 5 — canonical brand tokens

Nūr Media's graphic palette is centralized in `brand_tokens.py`: primary emerald `#0B5D3B`, deep forest `#064E3B`, near-black `#080808`, warm ivory `#F5F0E1`, muted gold `#D4AF37`, earth bronze `#A68A64`, and charcoal `#1C1C1C`. Photography and video retain natural colour; brand colour is used in overlays, type and graphic accents.
