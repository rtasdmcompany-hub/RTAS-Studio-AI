"""Module 9 — Master AI Plan assembler."""

from __future__ import annotations

from typing import Any

from app.services.intelligence.cinematic_models import (
    AutoImprovementResult,
    CinematicQualityScore,
    CinematicReasoning,
    EmotionMap,
    MasterAIPlan,
    MusicPlan,
    SoundDesignPlan,
    VisualStylePlan,
    VoicePlan,
)


def build_master_ai_plan(
    *,
    reasoning: CinematicReasoning,
    visual: VisualStylePlan,
    emotion_map: EmotionMap,
    music: MusicPlan,
    voice: VoicePlan,
    sound: SoundDesignPlan,
    quality: CinematicQualityScore,
    auto_improvement: AutoImprovementResult,
    character_memory: list[dict[str, Any]],
    scene_plan: list[dict[str, Any]],
    shot_plan: list[dict[str, Any]],
    camera_plan: list[dict[str, Any]],
    timeline: dict[str, Any],
    export_plan: dict[str, Any],
    director_plan: dict[str, Any],
    continuity: dict[str, Any],
) -> MasterAIPlan:
    summary = (
        f"{reasoning.logline} | look={visual.reference_look} | "
        f"emotion={emotion_map.arc} | score={quality.overall}"
    )
    lighting_plan = {
        "lighting": visual.lighting,
        "color_palette": visual.color_palette,
        "contrast": visual.contrast,
        "mood": visual.mood,
        "film_stock_style": visual.film_stock_style,
    }
    return MasterAIPlan(
        project_summary=summary,
        story_analysis=reasoning.to_dict(),
        character_memory=character_memory,
        scene_plan=scene_plan,
        shot_plan=shot_plan,
        camera_plan=camera_plan,
        lighting_plan=lighting_plan,
        music_plan=music.to_dict(),
        voice_plan=voice.to_dict(),
        sound_plan=sound.to_dict(),
        timeline=timeline,
        quality_report=quality.to_dict(),
        export_plan=export_plan,
        visual_style=visual.to_dict(),
        emotion_map=emotion_map.to_dict(),
        director_plan=director_plan,
        continuity=continuity,
        auto_improvement=auto_improvement.to_dict(),
    )
