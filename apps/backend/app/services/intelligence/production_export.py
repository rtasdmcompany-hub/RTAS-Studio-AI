"""Module 6 — Export complete AI production package JSON."""

from __future__ import annotations

from typing import Any

from app.services.intelligence.director_models import (
    CharacterMemory,
    ConsistencyReport,
    ContinuityState,
    CinematicTimeline,
    DirectorPlan,
    ProductionPackage,
)
from app.services.intelligence.models import (
    CameraPlan,
    PromptEnhancementResult,
    QualityCheckResult,
    ScenePlan,
    ShotPlan,
)


def build_production_package(
    *,
    prompt: str,
    enhancement: PromptEnhancementResult,
    scenes: list[ScenePlan],
    shots: list[ShotPlan],
    cameras: list[CameraPlan],
    characters: list[CharacterMemory],
    consistency: ConsistencyReport,
    continuity: ContinuityState,
    timeline: CinematicTimeline,
    director: DirectorPlan,
    quality: QualityCheckResult,
) -> ProductionPackage:
    return ProductionPackage(
        prompt=prompt,
        enhanced_prompt=enhancement.enhanced_prompt,
        scene_plan=[s.to_dict() for s in scenes],
        shot_plan=[s.to_dict() for s in shots],
        camera_plan=[c.to_dict() for c in cameras],
        character_memory=[c.to_dict() for c in characters],
        consistency=consistency.to_dict(),
        continuity=continuity.to_dict(),
        timeline=timeline.to_dict(),
        director_notes=list(director.director_notes),
        director_plan=director.to_dict(),
        quality_report=quality.to_dict(),
    )


def build_production_package_dict(**kwargs: Any) -> dict[str, Any]:
    return build_production_package(**kwargs).to_dict()
