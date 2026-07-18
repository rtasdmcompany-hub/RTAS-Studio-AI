"""Integration bridges for director / auto filmmaker."""

from __future__ import annotations

from typing import Any

from app.services.director_intelligence.models import DirectorIntelligenceJob


def build_integrations(
    job: DirectorIntelligenceJob,
    *,
    ai_brain: dict[str, Any] | None = None,
    story_plan: dict[str, Any] | None = None,
    character_dna: dict[str, Any] | None = None,
    motion_plan: dict[str, Any] | None = None,
    camera_plan: dict[str, Any] | None = None,
    emotion_plan: dict[str, Any] | None = None,
    world_plan: dict[str, Any] | None = None,
    audio_summary: dict[str, Any] | None = None,
    timeline_plan: dict[str, Any] | None = None,
    export_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    plan = job.production_plan
    return {
        "ai_brain": {"linked": bool(ai_brain), "intent": (ai_brain or {}).get("intent")},
        "story_engine": {
            "linked": bool(story_plan) or bool(job.analysis),
            "genre": job.analysis.genre if job.analysis else None,
            "structure": plan.story_structure if plan else None,
        },
        "character_dna": {
            "linked": bool(character_dna),
            "character_id": (character_dna or {}).get("character_id"),
            "assignments": plan.character_assignments if plan else {},
        },
        "motion_engine": {"linked": bool(motion_plan), "plan_id": (motion_plan or {}).get("job_id")},
        "camera_engine": {
            "linked": bool(camera_plan) or bool(plan),
            "angles": (plan.camera_plan.get("angles") if plan else None),
        },
        "emotion_engine": {
            "linked": bool(emotion_plan) or bool(job.analysis),
            "journey": job.analysis.emotional_journey if job.analysis else None,
        },
        "world_engine": {
            "linked": bool(world_plan) or bool(plan),
            "environments": list((plan.environment_assignments or {}).values()) if plan else [],
        },
        "audio_engine": {
            "linked": bool(audio_summary) or bool(plan),
            "music_cues": (plan.audio_plan.get("music_cues") if plan else None),
        },
        "timeline_engine": {
            "linked": bool(timeline_plan) or bool(plan),
            "runtime_sec": plan.total_runtime_sec if plan else None,
        },
        "export_engine": {
            "linked": bool(export_plan) or bool(plan),
            "export": plan.export_plan if plan else None,
        },
    }
