"""Integration bridges for camera intelligence."""

from __future__ import annotations

from typing import Any

from app.services.camera_intelligence.models import CameraIntelligenceJob


def build_integrations(
    job: CameraIntelligenceJob,
    *,
    director_plan: dict[str, Any] | None = None,
    story_plan: dict[str, Any] | None = None,
    scene_plan: dict[str, Any] | None = None,
    character_dna: dict[str, Any] | None = None,
    motion_plan: dict[str, Any] | None = None,
    timeline_plan: dict[str, Any] | None = None,
    audio_summary: dict[str, Any] | None = None,
    export_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "director_engine": {
            "linked": bool(director_plan),
            "plan_id": (director_plan or {}).get("plan_id") or (director_plan or {}).get("job_id"),
        },
        "story_engine": {
            "linked": bool(story_plan),
            "progression": job.analysis.story_progression if job.analysis else None,
        },
        "scene_planner": {
            "linked": bool(scene_plan) or bool(job.scene_id),
            "scene_id": job.scene_id,
        },
        "character_dna": {
            "linked": bool(character_dna) or bool(job.character_ids),
            "character_ids": list(job.character_ids),
            "consistency_priority": True,
        },
        "motion_engine": {
            "linked": bool(motion_plan),
            "follow_subject": True,
            "job_id": (motion_plan or {}).get("job_id"),
        },
        "timeline_engine": {
            "linked": bool(timeline_plan) or len(job.timeline) > 0,
            "camera_events": len(job.timeline),
            "duration_sec": job.duration_sec,
        },
        "audio_engine": {
            "linked": bool(audio_summary),
            "dialogue_aware_framing": True,
        },
        "export_engine": {
            "linked": bool(export_plan),
            "ready_for_render": job.state == "completed",
        },
        "camera_motion_compat": {
            "compatible": True,
            "note": "Plans consumeable by camera_motion path engine",
        },
    }
