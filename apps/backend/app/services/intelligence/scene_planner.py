"""Module 3 — Scene Planner (delegates to Scene Breakdown Engine)."""

from __future__ import annotations

from app.services.intelligence.models import (
    PromptIntelligenceResult,
    ScenePlan,
)
from app.services.intelligence.prompt_understanding import understand_prompt
from app.services.intelligence.scene_breakdown import (
    build_production_breakdown,
    to_legacy_plans,
)


def plan_scenes(
    prompt: str,
    intelligence: PromptIntelligenceResult,
) -> list[ScenePlan]:
    understanding = understand_prompt(prompt, category_hint=intelligence.category)
    breakdown = build_production_breakdown(
        prompt,
        understanding=understanding,
        intelligence=intelligence,
    )
    scenes, _, _ = to_legacy_plans(breakdown)
    return scenes
