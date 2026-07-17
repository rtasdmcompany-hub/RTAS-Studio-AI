"""Integration bridges — DNA, Face Lock, Director, Scene, Camera, Timeline, Audio."""

from __future__ import annotations

from typing import Any

from app.services.character_motion.models import CharacterMotionJob


def build_integrations(
    job: CharacterMotionJob,
    *,
    director_plan: dict[str, Any] | None = None,
    scene_plan: dict[str, Any] | None = None,
    camera_plan: dict[str, Any] | None = None,
    timeline_plan: dict[str, Any] | None = None,
    audio_summary: dict[str, Any] | None = None,
) -> dict[str, Any]:
    profile = job.profile
    return {
        "character_dna": {
            "character_id": job.character_id,
            "dna_fingerprint": profile.dna_fingerprint if profile else None,
            "linked": bool(profile and profile.dna_fingerprint),
        },
        "face_lock": {
            "face_identity_ref": profile.face_identity_ref if profile else None,
            "linked": bool(profile and profile.face_identity_ref),
            "identity_preserved": True,
        },
        "director_engine": {
            "linked": bool(director_plan),
            "plan_id": (director_plan or {}).get("plan_id") or (director_plan or {}).get("job_id"),
            "emotion": job.emotion,
        },
        "scene_planner": {
            "linked": bool(scene_plan),
            "scene_count": len((scene_plan or {}).get("scenes") or []),
        },
        "camera_engine": {
            "linked": bool(camera_plan),
            "plan_id": (camera_plan or {}).get("job_id") or (camera_plan or {}).get("plan_id"),
            "follow_character_motion": True,
        },
        "timeline_engine": {
            "linked": bool(timeline_plan) or len(job.timeline) > 0,
            "motion_events": len(job.timeline),
            "total_duration_sec": job.duration_sec,
        },
        "audio_engine": {
            "linked": bool(audio_summary),
            "dialogue_sync": True,
            "lip_motion_ready": "talking" in job.actions or "laughing" in job.actions,
        },
        "motion_intelligence": {
            "compatible": True,
            "locomotion_actions": [a for a in job.actions if a in ("walking", "running")],
        },
    }
