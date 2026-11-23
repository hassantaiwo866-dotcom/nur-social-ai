# Manual production preview

## Purpose

This workflow creates one Nūr media package for private human review. It is separate from the normal CI workflow and does not publish to social platforms or send Telegram messages.

## Where to find it

After this change is merged into the repository's default branch:

1. Open the repository's **Actions** tab.
2. Select **Nūr production preview**.
3. Select **Run workflow**.
4. Keep the source branch as `day9/output-validation`.
5. Tick the confirmation checkbox and start the run.
6. Open the completed run and download the `nur-production-preview-...` artifact.

The workflow is manually triggered only. It does not run on every push.

## Cost and provider safeguards

The workflow deliberately does not pass repository API secrets into the generation process. It explicitly disables Gemini image generation, Cloudflare Workers AI and Agnes video generation, and supplies empty Gemini, Groq, Pixabay, Cloudflare and Agnes credentials.

The intended generation path is:

- Built-in local editorial fallback (no text-generation API call).
- Wikimedia Commons with the existing licence screening, or locally generated Nūr illustration if Commons cannot provide a suitable image.
- Edge TTS for narration.
- Local Pillow and FFmpeg rendering and QA.

This prevents the workflow from intentionally invoking the configured paid or quota-limited AI provider adapters. It does **not** guarantee that the overall run has no cost: GitHub Actions usage is subject to the repository owner's included minutes and billing limits. Wikimedia Commons and Edge TTS require network access and may be unavailable or rate-limited. The generator currently has no local text-to-speech fallback, so an Edge TTS failure will fail the run.

Do not add API keys to this workflow unless a separate, explicit cost review and approval has been completed. In particular, do not enable Gemini image generation, Cloudflare Workers AI or Agnes video merely to make a failed run continue.

## Verification and review

The workflow compiles the checked-out source and runs the unit-test suite before generation. It then runs `python nur_generator.py` once and uploads the `output/` directory as a seven-day Actions artifact, even if generation fails partway through.

A green workflow run and passing automated QA do not establish that the media is ready to publish. Download and inspect the poster, full video, captions, source/licence metadata and run manifest on a phone. Check factual accuracy, image rights, visual quality, audio pronunciation and Nūr's non-shaming philosophy. Public publishing remains a separate, human-approved action.

## Source branch

The initial workflow is restricted to `day9/output-validation`, the branch containing the current Day 9/10 output-validation work. It does not silently switch to another branch. The normal `Nūr Social AI checks` workflow remains the push/pull-request CI workflow; this preview workflow is not a replacement for CI.
