"""
Real AI Intelligence Pipeline orchestrator.

AI Input → Prompt Intelligence → Enhancer → Scene → Camera → Shot
→ Quality Checker → Export Pipeline → (feeds Generation Queue)
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.intelligence.camera_planner import plan_cameras
from app.services.intelligence.export_pipeline import plan_export
from app.services.intelligence.models import (
    IntelligencePipelineResult,
    QualityCheckResult,
)
from app.services.intelligence.prompt_enhancer import enhance_prompt
from app.services.intelligence.prompt_intelligence import analyze_prompt
from app.services.intelligence.quality_checker import check_plan_quality
from app.services.intelligence.scene_planner import plan_scenes
from app.services.intelligence.shot_planner import plan_shots

logger = logging.getLogger(__name__)


def run_intelligence_pipeline(
    prompt: str,
    *,
    category_hint: str | None = None,
    style_hint: str | None = None,
    duration_hint: int | None = None,
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
    export = plan_export(intelligence)

    draft = IntelligencePipelineResult(
        intelligence=intelligence,
        enhancement=enhancement,
        scenes=scenes,
        cameras=cameras,
        shots=shots,
        quality=QualityCheckResult(passed=True, score=1.0),
        export=export,
    )
    draft.quality = check_plan_quality(draft)

    logger.info(
        "intelligence_pipeline language=%s category=%s scenes=%s shots=%s quality=%s",
        draft.intelligence.language,
        draft.intelligence.category,
        len(draft.scenes),
        len(draft.shots),
        draft.quality.passed,
    )
    return draft


def run_intelligence_pipeline_dict(prompt: str, **kwargs: Any) -> dict[str, Any]:
    return run_intelligence_pipeline(prompt, **kwargs).to_dict()
