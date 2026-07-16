"""
Real AI Intelligence + Director + Cinematic Brain pipeline.

Plans the full production before any generation provider is called.
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.intelligence.ai_director import direct_production
from app.services.intelligence.auto_improvement import auto_improve_production
from app.services.intelligence.camera_planner import plan_cameras
from app.services.intelligence.character_memory import build_character_memories
from app.services.intelligence.cinematic_quality import score_cinematic_quality
from app.services.intelligence.cinematic_reasoning import reason_about_project
from app.services.intelligence.cinematic_timeline import build_cinematic_timeline
from app.services.intelligence.consistency_engine import (
    apply_consistency_to_scenes,
    apply_consistency_to_shots,
    build_consistency_report,
)
from app.services.intelligence.emotion_engine import build_emotion_map
from app.services.intelligence.export_pipeline import plan_export
from app.services.intelligence.master_ai_plan import build_master_ai_plan
from app.services.intelligence.models import (
    IntelligencePipelineResult,
    QualityCheckResult,
)
from app.services.intelligence.music_planner import plan_music
from app.services.intelligence.production_export import build_production_package
from app.services.intelligence.prompt_enhancer import enhance_prompt
from app.services.intelligence.prompt_intelligence import analyze_prompt
from app.services.intelligence.quality_checker import check_plan_quality
from app.services.intelligence.scene_planner import plan_scenes
from app.services.intelligence.shot_planner import plan_shots
from app.services.intelligence.sound_design_planner import plan_sound_design
from app.services.intelligence.story_continuity import build_continuity_state
from app.services.intelligence.visual_style_engine import plan_visual_style
from app.services.intelligence.voice_planner import plan_voice

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

    # Sprint 5 — plan the production like a film team before provider calls.
    reasoning = reason_about_project(prompt, intelligence)
    visual = plan_visual_style(prompt, intelligence)

    scenes = plan_scenes(enhancement.enhanced_prompt or prompt, intelligence)
    cameras = plan_cameras(scenes, intelligence)
    shots = plan_shots(scenes, cameras)

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
    emotion_map = build_emotion_map(scenes, intelligence)
    music = plan_music(intelligence, scenes, emotion_map)
    voice = plan_voice(prompt, intelligence)
    sound = plan_sound_design(prompt, intelligence, visual)
    export = plan_export(intelligence)

    cinematic_quality = score_cinematic_quality(
        prompt=prompt,
        enhanced_prompt=enhancement.enhanced_prompt,
        scenes=scenes,
        shots=shots,
        cameras=cameras,
        character_memory=[c.to_dict() for c in characters],
        continuity=continuity.to_dict(),
        visual_style=visual.to_dict(),
        emotion_map=emotion_map.to_dict(),
    )
    auto_fix = auto_improve_production(
        original_prompt=prompt,
        current_enhanced_prompt=enhancement.enhanced_prompt,
        intelligence=intelligence,
        visual=visual,
        quality=cinematic_quality,
    )
    if auto_fix.applied:
        enhancement.enhanced_prompt = auto_fix.enhanced_prompt
        enhancement.improvements = list(enhancement.improvements) + list(
            auto_fix.improvements
        )
        # Re-score after improvement pass.
        cinematic_quality = score_cinematic_quality(
            prompt=prompt,
            enhanced_prompt=enhancement.enhanced_prompt,
            scenes=scenes,
            shots=shots,
            cameras=cameras,
            character_memory=[c.to_dict() for c in characters],
            continuity=continuity.to_dict(),
            visual_style=visual.to_dict(),
            emotion_map=emotion_map.to_dict(),
        )

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
        cinematic_reasoning=reasoning.to_dict(),
        visual_style=visual.to_dict(),
        emotion_map=emotion_map.to_dict(),
        music_plan=music.to_dict(),
        voice_plan=voice.to_dict(),
        sound_plan=sound.to_dict(),
        cinematic_quality=cinematic_quality.to_dict(),
        auto_improvement=auto_fix.to_dict(),
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

    master = build_master_ai_plan(
        reasoning=reasoning,
        visual=visual,
        emotion_map=emotion_map,
        music=music,
        voice=voice,
        sound=sound,
        quality=cinematic_quality,
        auto_improvement=auto_fix,
        character_memory=draft.character_memory,
        scene_plan=[s.to_dict() for s in scenes],
        shot_plan=[s.to_dict() for s in shots],
        camera_plan=[c.to_dict() for c in cameras],
        timeline=timeline.to_dict(),
        export_plan=export.to_dict(),
        director_plan=director.to_dict(),
        continuity=continuity.to_dict(),
    )
    draft.master_ai_plan = master.to_dict()

    logger.info(
        "cinematic_brain score=%.3f look=%s characters=%s scenes=%s auto_improve=%s",
        cinematic_quality.overall,
        visual.reference_look,
        len(characters),
        len(scenes),
        auto_fix.applied,
    )
    return draft


def run_intelligence_pipeline_dict(prompt: str, **kwargs: Any) -> dict[str, Any]:
    return run_intelligence_pipeline(prompt, **kwargs).to_dict()
