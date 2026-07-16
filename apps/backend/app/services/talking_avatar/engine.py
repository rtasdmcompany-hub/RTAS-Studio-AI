"""
Talking Avatar Engine.

Face animation, lip sync, head/eye/idle motion, emotion, reference face lock,
Character Memory + Director + timeline integration.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.services.talking_avatar.emotion import resolve_emotion
from app.services.talking_avatar.face_lock import build_face_lock
from app.services.talking_avatar.models import (
    AvatarProviderRequest,
    TalkingAvatarJob,
)
from app.services.talking_avatar.prompts import build_avatar_prompt
from app.services.talking_avatar.store import (
    append_history,
    get_job as store_get_job,
    history_for_job,
    save_job,
)
from app.services.talking_avatar.timeline import (
    build_avatar_timeline,
    estimate_runtime,
)

logger = logging.getLogger(__name__)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _job_id(parent: str | None, prompt: str) -> str:
    seed = f"{parent or ''}|{prompt}|{uuid4().hex[:8]}"
    return f"avatar_{hashlib.sha1(seed.encode()).hexdigest()[:10]}"


def build_talking_avatar_job(
    *,
    prompt: str,
    character_memory: list[dict[str, Any]] | None = None,
    director_plan: dict[str, Any] | None = None,
    audio_director: dict[str, Any] | None = None,
    timeline: dict[str, Any] | None = None,
    reference_face_url: str | None = None,
    dialogue: str | None = None,
    emotion_hint: str | None = None,
    duration_hint: float | None = None,
    identity_strength: float = 0.9,
    natural_motion: bool = True,
    parent_generation_id: str | None = None,
) -> TalkingAvatarJob:
    chars = list(character_memory or [])
    face_lock = build_face_lock(
        chars,
        reference_face_url=reference_face_url,
        identity_strength=identity_strength,
    )
    emotion = resolve_emotion(
        prompt=prompt,
        audio_director=audio_director,
        director_plan=director_plan,
        emotion_hint=emotion_hint,
    )
    runtime = estimate_runtime(
        duration_hint=duration_hint,
        audio_director=audio_director,
        timeline=timeline,
    )
    director_notes = list((director_plan or {}).get("director_notes") or [])
    # Director integration — talking-head emphasis
    if director_plan:
        rhythm = director_plan.get("cinematic_rhythm")
        if rhythm:
            director_notes.append(f"Rhythm: {rhythm}")
        if director_plan.get("transition_style"):
            director_notes.append(f"Transitions: {director_plan['transition_style']}")

    avatar_tl = build_avatar_timeline(
        runtime_seconds=runtime,
        character_id=face_lock.character_id,
        emotion=emotion,
        audio_director=audio_director,
        dialogue=dialogue or prompt,
        natural_motion=natural_motion,
    )

    job_id = _job_id(parent_generation_id, prompt)
    compiled = build_avatar_prompt(
        prompt=prompt,
        face_lock=face_lock,
        emotion=emotion,
        director_notes=director_notes,
        character=chars[0] if chars else None,
        natural_motion=natural_motion,
    )
    provider_req = AvatarProviderRequest(
        request_id=f"{job_id}_talk",
        job_id=job_id,
        prompt=compiled,
        duration_seconds=avatar_tl.runtime_seconds,
        face_reference_url=face_lock.reference_face_url,
        audio_hint=(
            "voice_timeline"
            if (audio_director or {}).get("voice_timeline")
            else None
        ),
        emotion=emotion,
        identity_strength=face_lock.identity_strength,
        arguments={
            "lip_sync_cues": len(avatar_tl.lip_sync),
            "blink_cues": len(avatar_tl.blinks),
            "natural_motion": natural_motion,
        },
        metadata={
            "face_lock": face_lock.to_dict(),
            "timeline_summary": {
                "lip_sync": len(avatar_tl.lip_sync),
                "head_motion": len(avatar_tl.head_motion),
                "eye_contact": len(avatar_tl.eye_contact),
                "blinks": len(avatar_tl.blinks),
                "smiles": len(avatar_tl.smiles),
                "idle": len(avatar_tl.idle_motion),
            },
        },
    )

    state = "ready" if face_lock.face_locked else "planned"
    if not avatar_tl.lip_sync:
        state = "failed"

    return TalkingAvatarJob(
        job_id=job_id,
        parent_generation_id=parent_generation_id,
        prompt=prompt,
        state=state,  # type: ignore[arg-type]
        face_lock=face_lock,
        timeline=avatar_tl,
        emotion=emotion,
        natural_motion=natural_motion,
        director_notes=director_notes,
        character_memory=chars,
        provider_request=provider_req,
        created_at=_now(),
        metadata={
            "engine": "talking_avatar",
            "version": "1.0",
            "supports": [
                "face_animation",
                "lip_sync",
                "head_motion",
                "eye_contact",
                "emotion",
                "idle_motion",
                "blink",
                "smile",
                "natural_motion",
                "reference_face_lock",
            ],
        },
    )


def register_job(job: TalkingAvatarJob) -> TalkingAvatarJob:
    save_job(job)
    append_history(job.job_id, "job_created", detail=job.summary())
    append_history(
        job.job_id,
        "face_lock",
        detail=job.face_lock.to_dict(),
    )
    append_history(
        job.job_id,
        "timeline_ready",
        detail={
            "runtime_seconds": job.timeline.runtime_seconds,
            "lip_sync": len(job.timeline.lip_sync),
            "blinks": len(job.timeline.blinks),
            "smiles": len(job.timeline.smiles),
        },
    )
    return job


def build_and_register(**kwargs: Any) -> TalkingAvatarJob:
    job = build_talking_avatar_job(**kwargs)
    return register_job(job)


def get_job(job_id: str) -> dict[str, Any] | None:
    job = store_get_job(job_id)
    return job.to_dict() if job else None


def get_job_history(job_id: str) -> list[dict[str, Any]]:
    return history_for_job(job_id)


def build_talking_avatar_dict(**kwargs: Any) -> dict[str, Any]:
    job = build_and_register(**kwargs)
    return {
        "job": job.to_dict(),
        "summary": job.summary(),
        "timeline": job.timeline.to_dict(),
        "faceLock": job.face_lock.to_dict(),
        "providerPayload": (
            job.provider_request.to_provider_payload() if job.provider_request else None
        ),
        "history": get_job_history(job.job_id),
    }
