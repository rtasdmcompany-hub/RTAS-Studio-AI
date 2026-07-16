"""
Real AI Intelligence + Director pipeline.

AI Input → Prompt Intelligence → Enhancer → Scene → Camera → Shot
→ Character Memory → Consistency → Director → Continuity → Timeline
→ Quality Checker → Export / Production Package
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.intelligence.ai_director import direct_production
from app.services.intelligence.camera_planner import plan_cameras
from app.services.intelligence.character_memory import build_character_memories
from app.services.intelligence.cinematic_timeline import build_cinematic_timeline
from app.services.intelligence.consistency_engine import (
    apply_consistency_to_scenes,
    apply_consistency_to_shots,
    build_consistency_report,
)
from app.services.intelligence.export_pipeline import plan_export
from app.services.intelligence.models import (
    IntelligencePipelineResult,
    QualityCheckResult,
)
from app.services.intelligence.production_export import build_production_package
from app.services.intelligence.prompt_enhancer import enhance_prompt
from app.services.intelligence.prompt_intelligence import analyze_prompt
from app.services.intelligence.quality_checker import check_plan_quality
from app.services.intelligence.scene_planner import plan_scenes
from app.services.intelligence.shot_planner import plan_shots
from app.services.intelligence.story_continuity import build_continuity_state

logger = logging.getLogger(__name__)


def run_intelligence_pipeline(
    prompt: str,
    *,
    category_hint: str | None = None,
    style_hint: str | None = None,
    duration_hint: int | None = None,
    reference_image_urls: list[str] | None = None,
    character_count_hint: int | None = None,
    allow_wardrobe_change: bool = False,
) -> IntelligencePipelineResult:
    intelligence = analyze_prompt(
        prompt,
        category_hint=category_hint,
        style_hint=style_hint,
        duration_hint=duration_hint,
    )
    enhancement = enhance_prompt(prompt, intelligence)
    scenes = plan_scenes(enhancement.enhanced_prompt or prompt, intelligence)
    cameras = plan_cameras(scenes, intelligence)
    shots = plan_shots(scenes, cameras)

    # Sprint 4 — Character Memory + Director stack
    characters = build_character_memories(
        prompt,
        style_hint=style_hint or intelligence.style,
        reference_image_urls=reference_image_urls,
        character_count_hint=character_count_hint,
    )
    consistency = build_consistency_report(
        characters,
        user_allows_wardrobe_change=allow_wardrobe_change,
    )
    scenes = apply_consistency_to_scenes(scenes, characters)
    shots = apply_consistency_to_shots(shots, characters)
    director = direct_production(scenes, shots, intelligence)
    continuity = build_continuity_state(prompt, intelligence, scenes, characters)
    timeline = build_cinematic_timeline(scenes, shots, characters, director)
    export = plan_export(intelligence)

    draft = IntelligencePipelineResult(
        intelligence=intelligence,
        enhancement=enhancement,
        scenes=scenes,
        cameras=cameras,
        shots=shots,
        quality=QualityCheckResult(passed=True, score=1.0),
        export=export,
        character_memory=[c.to_dict() for c in characters],
        consistency=consistency.to_dict(),
        continuity=continuity.to_dict(),
        director_plan=director.to_dict(),
        timeline=timeline.to_dict(),
    )
    draft.quality = check_plan_quality(draft)

    package = build_production_package(
        prompt=prompt,
        enhancement=enhancement,
        scenes=scenes,
        shots=shots,
        cameras=cameras,
        characters=characters,
        consistency=consistency,
        continuity=continuity,
        timeline=timeline,
        director=director,
        quality=draft.quality,
    )
    draft.production_package = package.to_dict()

    logger.info(
        "intelligence_pipeline language=%s characters=%s scenes=%s shots=%s timeline_nodes=%s quality=%s",
        draft.intelligence.language,
        len(characters),
        len(draft.scenes),
        len(draft.shots),
        len(timeline.nodes),
        draft.quality.passed,
    )
    return draft


def run_intelligence_pipeline_dict(prompt: str, **kwargs: Any) -> dict[str, Any]:
    return run_intelligence_pipeline(prompt, **kwargs).to_dict()
