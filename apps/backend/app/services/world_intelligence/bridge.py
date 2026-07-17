"""Integration bridges for world generation."""

from __future__ import annotations

from typing import Any

from app.services.world_intelligence.models import WorldIntelligenceJob


def build_integrations(
    job: WorldIntelligenceJob,
    *,
    story_plan: dict[str, Any] | None = None,
    director_plan: dict[str, Any] | None = None,
    scene_plan: dict[str, Any] | None = None,
    camera_plan: dict[str, Any] | None = None,
    character_dna: dict[str, Any] | None = None,
    motion_plan: dict[str, Any] | None = None,
    emotion_plan: dict[str, Any] | None = None,
    timeline_plan: dict[str, Any] | None = None,
    audio_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    env = job.environment
    return {
        "story_engine": {"linked": bool(story_plan), "mood": job.analysis.mood if job.analysis else None},
        "director_engine": {
            "linked": bool(director_plan),
            "plan_id": (director_plan or {}).get("plan_id") or (director_plan or {}).get("job_id"),
        },
        "scene_planner": {
            "linked": bool(scene_plan) or bool(job.scene_id),
            "scene_id": job.scene_id,
        },
        "camera_engine": {
            "linked": bool(camera_plan),
            "environment": env.environment_id if env else None,
            "plan_id": (camera_plan or {}).get("job_id"),
        },
        "character_dna": {
            "linked": bool(character_dna),
            "character_id": (character_dna or {}).get("character_id"),
        },
        "motion_engine": {"linked": bool(motion_plan), "plan_id": (motion_plan or {}).get("job_id")},
        "emotion_engine": {
            "linked": bool(emotion_plan),
            "weather_mood_sync": env.weather.mood_sync if env else None,
        },
        "timeline_engine": {"linked": bool(timeline_plan), "world_id": job.world_id},
        "audio_engine": {
            "linked": bool(audio_summary),
            "ambience_hint": env.weather.weather_id if env else None,
        },
    }
