# Nūr Social AI

Prelaunch editorial media pipeline for Nūr: privacy-first self-control, protection, recovery and personal growth, communicated without shame, guilt or fear.

## Pipeline
- Editorial plan: Gemini → Groq → built-in local fallback.
- Models are discovered from each configured account's live model catalogue. `GEMINI_MODEL` and `GROQ_MODEL` are preferences used only when listed by that account.
- Visuals: optional Pexels first, then Wikimedia Commons with licence screening and recorded attribution.
- Production: branded editorial graphic, four-scene vertical video, Edge TTS voiceover and FFmpeg assembly.
- Human review remains mandatory. Telegram publishing retains its explicit `NUR_APPROVED=yes` gate and passing-QA requirement.

## GitHub Actions secrets
- `GEMINI_API_KEY` — optional text provider.
- `GROQ_API_KEY` — optional fallback text provider.
- `PEXELS_API_KEY` — optional image provider. Commons is attempted if absent or unavailable.

Keep credentials in repository Actions secrets, never source files. At least one text provider key is recommended.

## Local run
Python 3.11, FFmpeg and ffprobe are required.

```bash
python -m pip install -r requirements.txt
python nur_generator.py
```

Generated media is written to `output/`. Actions uploads it as an artifact for review; generation does not publish automatically.

## Image rights and review
Commons metadata can be incomplete or unreliable. The pipeline accepts only identified CC0, public-domain, CC BY or CC BY-SA licences with a licence URL and skips declared restrictions. Attribution is recorded, but humans must inspect the original file page and conditions. Pexels source and photographer are also recorded. No automated source guarantees freedom from watermarks, personality, privacy or trademark concerns.

See [Day 1 stabilisation notes](docs/DAY1_STABILISATION.md).
