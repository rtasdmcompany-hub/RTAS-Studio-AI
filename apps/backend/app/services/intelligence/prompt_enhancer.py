"""Module 2 — Prompt Enhancer (never changes user intent)."""

from __future__ import annotations

from app.services.intelligence.models import (
    PromptEnhancementResult,
    PromptIntelligenceResult,
)


def enhance_prompt(
    prompt: str,
    intelligence: PromptIntelligenceResult,
) -> PromptEnhancementResult:
    original = (prompt or "").strip()
    if not original:
        return PromptEnhancementResult(
            original_prompt="",
            enhanced_prompt="",
            improvements=["empty_prompt"],
            intent_preserved=True,
        )

    improvements: list[str] = []
    parts = [original.rstrip(".")]

    # Clarity / consistency without replacing subject matter.
    if intelligence.lighting and "light" not in original.lower():
        parts.append(f"Lighting: {intelligence.lighting}.")
        improvements.append("added_lighting_clarity")

    if intelligence.emotion and intelligence.emotion not in original.lower():
        parts.append(f"Emotional tone: {intelligence.emotion}.")
        improvements.append("added_emotion_consistency")

    if intelligence.cinematic_genre:
        parts.append(
            f"Cinematic genre: {intelligence.cinematic_genre.replace('_', ' ')}."
        )
        improvements.append("added_genre_anchor")

    # Realism / generation quality cues (non-destructive).
    quality_cues = [
        "high detail",
        "coherent motion",
        "natural skin texture" if intelligence.style == "real" else "clean stylization",
        "stable composition",
    ]
    parts.append("Quality: " + ", ".join(quality_cues) + ".")
    improvements.append("added_generation_quality_cues")

    if intelligence.camera_requirements:
        parts.append(
            "Camera: " + ", ".join(intelligence.camera_requirements[:3]) + "."
        )
        improvements.append("added_camera_clarity")

    enhanced = " ".join(parts)
    return PromptEnhancementResult(
        original_prompt=original,
        enhanced_prompt=enhanced,
        improvements=improvements,
        intent_preserved=True,
    )
