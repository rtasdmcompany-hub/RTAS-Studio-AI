"""Module 8 — Auto Improvement Engine (intent-preserving)."""

from __future__ import annotations

from app.services.intelligence.cinematic_models import (
    AutoImprovementResult,
    CinematicQualityScore,
    VisualStylePlan,
)
from app.services.intelligence.models import PromptIntelligenceResult


def auto_improve_production(
    *,
    original_prompt: str,
    current_enhanced_prompt: str,
    intelligence: PromptIntelligenceResult,
    visual: VisualStylePlan,
    quality: CinematicQualityScore,
    threshold: float = 0.72,
) -> AutoImprovementResult:
    if quality.overall >= threshold:
        return AutoImprovementResult(
            applied=False,
            improvements=[],
            enhanced_prompt=current_enhanced_prompt,
            intent_preserved=True,
        )

    improvements: list[str] = []
    parts = [current_enhanced_prompt.rstrip(".")]

    if quality.prompt_quality < 0.7:
        parts.append("Clarify subject action and clear hero moment.")
        improvements.append("prompt_clarity")
    if quality.camera < 0.7:
        parts.append(f"Camera language: {visual.camera_language}.")
        improvements.append("camera_language")
    if quality.lighting < 0.7:
        parts.append(f"Lighting: {visual.lighting}. Palette: {', '.join(visual.color_palette[:3])}.")
        improvements.append("lighting_palette")
    if quality.emotion < 0.7:
        parts.append(f"Emotional through-line: {intelligence.emotion}.")
        improvements.append("emotion_throughline")
    if quality.scene_continuity < 0.7:
        parts.append("Keep location, wardrobe, and time-of-day continuous across scenes.")
        improvements.append("continuity_guard")
    if quality.character_consistency < 0.7:
        parts.append("Preserve exact character identity and wardrobe in every shot.")
        improvements.append("identity_lock")

    parts.append(f"Look reference: {visual.reference_look}.")
    improvements.append("reference_look")

    # Never replace the original user text — only append production guidance.
    if original_prompt and original_prompt not in parts[0]:
        # Ensure original intent string remains present.
        parts.insert(0, original_prompt.rstrip("."))
        improvements.append("anchor_original_intent")

    return AutoImprovementResult(
        applied=True,
        improvements=improvements,
        enhanced_prompt=" ".join(parts),
        intent_preserved=True,
    )
