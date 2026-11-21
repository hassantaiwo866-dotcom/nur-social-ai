# Nūr Social AI

Prelaunch editorial media pipeline for Nūr: privacy-first self-control, protection, recovery and personal growth, communicated without shame, guilt or fear.

## Pipeline
- Editorial plan: Gemini → Groq → built-in local fallback.
- Models are discovered from each configured account's live model catalogue. `GEMINI_MODEL` and `GROQ_MODEL` are preferences used only when listed by that account.
- Visuals: Wikimedia Commons with licence screening and recorded attribution; a built-in original editorial illustration is the no-key fallback.
- Production: photo-led editorial poster, graded source photography, consistent vertical scene design, Edge TTS voiceover and FFmpeg crossfade assembly.
- Human review remains mandatory. Telegram publishing retains its explicit `NUR_APPROVED=yes` gate and passing-QA requirement.

## GitHub Actions secrets
- `GEMINI_API_KEY` — optional text provider.
- `GROQ_API_KEY` — optional fallback text provider.
- `TELEGRAM_BOT_TOKEN` — optional bot token used only for private review delivery.
- `TELEGRAM_REVIEW_CHAT_ID` — optional dedicated review chat ID; if omitted, the existing `TELEGRAM_CHAT_ID` is reused.

Keep credentials in repository Actions secrets, never source files. At least one text provider key is recommended.

## Local run
Python 3.11, FFmpeg and ffprobe are required.

```bash
python -m pip install -r requirements.txt
python nur_generator.py
```

Generated media is written to `output/`. Actions uploads it as an artifact and, when both Telegram review secrets are configured, sends the image and video to the configured private review chat. This preview path is separate from public publishing. The existing `telegram_publisher.py` still requires `NUR_APPROVED=yes` and passing QA.

## Image rights and review
Commons metadata can be incomplete or unreliable. The pipeline accepts only identified CC0, public-domain, CC BY or CC BY-SA licences with a licence URL and skips declared restrictions. Attribution is recorded, but humans must inspect the original file page and conditions. If Commons cannot provide a suitable image, the pipeline creates original Nūr-branded artwork locally; it is explicitly labelled as an illustration, not a photograph.

See [Day 1 stabilisation notes](docs/DAY1_STABILISATION.md), [Day 2 visual quality notes](docs/DAY2_VISUAL_QUALITY.md) and [private Telegram review setup](docs/TELEGRAM_PRIVATE_REVIEW.md).
