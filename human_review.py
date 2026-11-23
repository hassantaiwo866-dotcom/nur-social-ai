"""Human review checklist data for Nūr generated media packages."""
from __future__ import annotations

REVIEW_ITEMS = (
    {
        "id": "visual_relevance",
        "label": "Visual relevance and story continuity",
        "question": "Do scenes depict the narration, feel coherent, and avoid distracting repetition?",
        "required": True,
    },
    {
        "id": "mobile_legibility",
        "label": "Mobile text legibility",
        "question": "Are captions and overlays readable on a phone without clipping?",
        "required": True,
    },
    {
        "id": "audio_clarity",
        "label": "Audio and narration",
        "question": "Is narration clear, natural, correctly pronounced, and free from clipping or distracting sound?",
        "required": True,
    },
    {
        "id": "audience_sensitivity",
        "label": "Audience dignity and sensitivity",
        "question": "Does the content respect the audience and avoid shame, guilt, fear, humiliation, and manipulation?",
        "required": True,
    },
    {
        "id": "factual_accuracy",
        "label": "Factual and product-claim accuracy",
        "question": "Are statements factual, and are all Nūr feature claims verified against the current app?",
        "required": True,
    },
    {
        "id": "practical_value",
        "label": "Practical value and payoff",
        "question": "Does the ending offer a clear, realistic, user-controlled next step?",
        "required": True,
    },
    {
        "id": "rights_attribution",
        "label": "Source rights and attribution",
        "question": "Have source pages, licence terms, attribution, and any required restrictions been reviewed?",
        "required": True,
    },
    {
        "id": "brand_consistency",
        "label": "Brand consistency",
        "question": "Does the content follow Nūr's identity and spell the brand correctly?",
        "required": True,
    },
)

REVIEW_DECISIONS = ("pending", "approved", "needs_revision", "rejected")


def build_human_review_checklist() -> dict:
    """Return a fresh, uncompleted checklist for the package."""
    return {
        "status": "pending",
        "decision": "pending",
        "reviewer_notes": "",
        "items": [
            {**item, "status": "pending", "notes": ""}
            for item in REVIEW_ITEMS
        ],
        "approval_required_before_publishing": True,
    }
