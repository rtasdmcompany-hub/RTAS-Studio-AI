"""
Bridge Prompt Understanding → legacy PromptIntelligenceResult.

Keeps Character Memory, AI Director, and Story Continuity compatible by
preserving the existing intelligence contract while enriching fields.
"""

from __future__ import annotations

from app.services.intelligence.models import PromptIntelligenceResult
from app.services.intelligence.prompt_understanding.lexicon import CATEGORY_TO_LEGACY
from app.services.intelligence.prompt_understanding.models import (
    CinematicPromptUnderstanding,
)

_EMOTION_TO_LEGACY: dict[str, str] = {
    "Sad": "somber",
    "Lonely": "somber",
    "Melancholy": "somber",
    "Hope": "inspiring",
    "Joy": "joyful",
    "Victory": "joyful",
    "Fear": "dramatic",
    "Suspense": "dramatic",
    "Action": "dramatic",
    "Anger": "dramatic",
    "Romance": "calm",
    "Calm": "calm",
}

_STYLE_FROM_CATEGORY: dict[str, str] = {
    "Anime": "cartoon",
    "3D Animation": "cartoon",
    "Talking Avatar": "avatar",
}


def to_prompt_intelligence(
    understanding: CinematicPromptUnderstanding,
    *,
    language: str = "en",
    style_hint: str | None = None,
    duration_hint: int | None = None,
) -> PromptIntelligenceResult:
    legacy_cat, legacy_genre = CATEGORY_TO_LEGACY.get(
        understanding.category, ("story", "narrative")
    )
    primary_emotion = understanding.emotion[0] if understanding.emotion else "Calm"
    emotion = _EMOTION_TO_LEGACY.get(primary_emotion, "inspiring")

    style = style_hint or _STYLE_FROM_CATEGORY.get(understanding.category, "real")

    camera_requirements = list(
        dict.fromkeys([*understanding.camera, *understanding.movement])
    )
    lighting = ", ".join(understanding.lighting) if understanding.lighting else "natural balanced"

    estimated = duration_hint if duration_hint and duration_hint > 0 else 15
    if understanding.category in ("Trailer", "YouTube Shorts", "TikTok", "Instagram Reel"):
        estimated = min(estimated, 30) if duration_hint else 15
    elif understanding.category in ("Short Film", "Movie Scene"):
        estimated = max(estimated, 30) if not duration_hint else estimated

    missing: list[str] = []
    if len(understanding.raw_prompt) < 12:
        missing.append("prompt_too_short")
    if understanding.subject_count >= 1 and "face" not in understanding.raw_prompt.lower():
        missing.append("subject_identity_unclear")

    return PromptIntelligenceResult(
        language=language,
        category=legacy_cat,
        style=style,
        emotion=emotion,
        camera_requirements=camera_requirements,
        lighting=lighting,
        cinematic_genre=legacy_genre,
        estimated_duration_seconds=int(estimated),
        missing_information=missing,
        confidence=understanding.confidence,
    )
