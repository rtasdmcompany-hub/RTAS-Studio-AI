"""Module 5 — Voice Planner (narration planning only)."""

from __future__ import annotations

from app.services.intelligence.cinematic_models import VoicePlan
from app.services.intelligence.models import PromptIntelligenceResult


def plan_voice(
    prompt: str,
    intelligence: PromptIntelligenceResult,
) -> VoicePlan:
    lower = (prompt or "").lower()
    gender = "neutral"
    if any(w in lower for w in ("she", "her", "woman", "female")):
        gender = "female"
    elif any(w in lower for w in ("he", "him", "man", "male")):
        gender = "male"

    tone = "warm authoritative"
    if intelligence.emotion == "calm":
        tone = "soft reassuring"
    elif intelligence.emotion == "dramatic":
        tone = "intense measured"
    elif intelligence.category == "business":
        tone = "confident modern"

    language = intelligence.language
    accent = "neutral"
    if language == "ur":
        accent = "south-asian"
        language = "ur"

    return VoicePlan(
        gender=gender,
        age="adult",
        tone=tone,
        emotion=intelligence.emotion,
        speed="moderate",
        pauses=["before key claim", "after emotional line"],
        emphasis=["brand / hero line", "closing call-to-action"],
        language=language,
        accent=accent,
    )
