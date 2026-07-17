"""Integration bridges — DNA, Face Lock, Motion, Camera, Voice, Audio, Story, Director, Timeline."""

from __future__ import annotations

from typing import Any

from app.services.emotion_intelligence.models import EmotionIntelligenceJob


def _face_ref(character_id: str | None) -> str | None:
    if not character_id:
        return None
    try:
        from app.services.face_lock import get_identity

        identity = get_identity(character_id)
        if identity:
            return identity.get("face_embedding_ref")
    except Exception:
        pass
    return None


def _dna_fp(character_id: str | None) -> str | None:
    if not character_id:
        return None
    try:
        from app.services.character_generation.engine import get_character

        record = get_character(character_id)
        if record and record.dna:
            return record.dna.fingerprint
    except Exception:
        pass
    return None


def build_integrations(
    job: EmotionIntelligenceJob,
    *,
    director_plan: dict[str, Any] | None = None,
    story_plan: dict[str, Any] | None = None,
    motion_plan: dict[str, Any] | None = None,
    camera_plan: dict[str, Any] | None = None,
    voice_plan: dict[str, Any] | None = None,
    audio_summary: dict[str, Any] | None = None,
    timeline_plan: dict[str, Any] | None = None,
) -> dict[str, Any]:
    cid = job.character_id
    return {
        "character_dna": {
            "character_id": cid,
            "dna_fingerprint": _dna_fp(cid),
            "linked": bool(_dna_fp(cid)),
        },
        "face_lock": {
            "face_embedding_ref": _face_ref(cid),
            "linked": bool(_face_ref(cid)),
            "identity_preserved": True,
        },
        "motion_engine": {
            "linked": bool(motion_plan),
            "sync_body_performance": True,
            "plan_id": (motion_plan or {}).get("job_id"),
        },
        "camera_engine": {
            "linked": bool(camera_plan),
            "emotion_framing": job.profile.primary_emotion if job.profile else None,
            "plan_id": (camera_plan or {}).get("job_id"),
        },
        "voice_engine": {
            "linked": bool(voice_plan),
            "emotion_style": job.profile.primary_emotion if job.profile else None,
        },
        "audio_engine": {
            "linked": bool(audio_summary),
            "dialogue_emotion_sync": True,
        },
        "story_engine": {
            "linked": bool(story_plan),
            "story_emotion": job.analysis.story_emotion if job.analysis else None,
        },
        "director_engine": {
            "linked": bool(director_plan),
            "plan_id": (director_plan or {}).get("plan_id") or (director_plan or {}).get("job_id"),
        },
        "timeline_engine": {
            "linked": bool(timeline_plan) or len(job.timeline) > 0,
            "emotion_events": len(job.timeline),
        },
    }
