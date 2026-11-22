# Day 2 — final visual-quality verification

## Scope

This closeout adds regression coverage for the Day 2 visual system already present on `stabilise/day-1-provider-media-resilience`. It does not replace the renderer, prompt composer, provider chain, media licensing checks, or human approval workflow.

## Existing implementation verified by source inspection

- Scene-directed still-image camera movement.
- Scene-aware image-generation prompts and concise stock-search queries.
- Four-beat visual continuity guidance (open, develop, re-hook, payoff).
- Vertical 1080×1920 scene frames and transparent overlays.
- Documentary and tactile/hybrid collage presentation paths.
- Nūr primary emerald graphic rule and caption overflow rejection.

## Automated workflow

Added `.github/workflows/day2-visual-tests.yml` to install the pinned project requirements and run the complete unittest suite on pull requests targeting the stabilisation branch. It can also be run manually with `workflow_dispatch`.

## Final regression coverage added

`tests/test_day2_visual_closeout.py` checks:

1. Collage frame and overlay output dimensions, image mode, and emerald masthead rule.
2. Rejection of captions that cannot fit within the three-line limit.
3. Integration of the four-scene continuity direction into a payoff generation prompt.

These tests are deterministic and local-only. They do not call Gemini, Groq, Pixabay, Cloudflare, Telegram, or any paid service.

## Completion criteria

Day 2 is technically complete when the new tests and the repository's existing test suite pass on the merged stabilisation branch.

A separate human review is still required before publication. Inspect a fresh generated 9:16 video and its poster on a phone for visual coherence, text legibility, source relevance, colour consistency, audio clarity, and transition quality. Automated tests cannot certify aesthetic quality, factual accuracy, source rights, or publication readiness.

## Safeguards preserved

- No new API, credential, dependency, or paid generation service.
- Original illustrations remain identified as illustrations, not photographs.
- External media sourcing and licence screening remain unchanged.
- Human review and the existing Telegram approval gate remain mandatory.
- No automatic social publishing is introduced.
