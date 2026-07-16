"""
Real AI Intelligence + Director + Cinematic Brain pipeline.

Plans the full production before any generation provider is called.
"""

from __future__ import annotations

import logging
from typing import Any

from app.services.intelligence.ai_director import direct_production
from app.services.intelligence.auto_improvement import auto_improve_production
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
from app.services.intelligence.prompt_understanding import understand_prompt
from app.services.intelligence.quality_checker import check_plan_quality
from app.services.intelligence.scene_breakdown import (
    build_production_breakdown,
    to_legacy_plans,
)
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
    # Director-grade prompt parse first — feeds all downstream planners.
    understanding = understand_prompt(prompt, category_hint=category_hint)
    intelligence = analyze_prompt(
        prompt,
        category_hint=category_hint,
        style_hint=style_hint,
        duration_hint=duration_hint,
        understanding=understanding,
    )
    enhancement = enhance_prompt(prompt, intelligence)
    # Fold cinematic cues into the enhanced prompt without changing intent.
    cue_bits = [
        f"Time: {understanding.time}.",
        f"Weather: {understanding.weather}.",
        f"Environment: {understanding.environment}.",
        f"Lighting: {', '.join(understanding.lighting)}.",
        f"Palette: {', '.join(understanding.color_palette)}.",
        f"Camera: {', '.join(understanding.camera)}.",
        f"Lens: {understanding.lens}.",
        f"Mood: {understanding.mood}.",
    ]
    enhancement.enhanced_prompt = (
        f"{enhancement.enhanced_prompt} {' '.join(cue_bits)}"
    ).strip()
    enhancement.improvements = list(enhancement.improvements) + [
        "cinematic_prompt_understanding"
    ]

    # Sprint 5 — plan the production like a film team before provider calls.
    reasoning = reason_about_project(prompt, intelligence)
    visual = plan_visual_style(prompt, intelligence)

    # Character Memory first so scene breakdown can name the lead.
    characters = build_character_memories(
        prompt,
        style_hint=style_hint or intelligence.style,
        reference_image_urls=reference_image_urls,
        character_count_hint=character_count_hint or understanding.subject_count,
    )
    lead_name = characters[0].character_id if characters else "lead subject"

    # Sprint 6 — Scene Breakdown & Shot Generation Engine.
    breakdown = build_production_breakdown(
        prompt,
        understanding=understanding,
        intelligence=intelligence,
        character_name=lead_name,
    )
    scenes, cameras, shots = to_legacy_plans(breakdown)

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
        prompt_understanding=understanding.production_instructions(),
        scene_breakdown=breakdown.to_dict(),
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
    if isinstance(draft.production_package, dict):
        draft.production_package["scene_breakdown"] = breakdown.to_dict()

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
    if isinstance(draft.master_ai_plan, dict):
        draft.master_ai_plan["prompt_understanding"] = (
            understanding.production_instructions()
        )
        draft.master_ai_plan["scene_breakdown"] = breakdown.to_dict()

    logger.info(
        "cinematic_brain score=%.3f look=%s category=%s characters=%s scenes=%s shots=%s auto_improve=%s",
        cinematic_quality.overall,
        visual.reference_look,
        understanding.category,
        len(characters),
        len(scenes),
        len(shots),
        auto_fix.applied,
    )
    return draft


def run_intelligence_pipeline_dict(prompt: str, **kwargs: Any) -> dict[str, Any]:
    return run_intelligence_pipeline(prompt, **kwargs).to_dict()
