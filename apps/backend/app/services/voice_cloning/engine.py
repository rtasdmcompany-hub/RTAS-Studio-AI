"""Voice Cloning & Character Voice Engine — clone / train / assign."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.voice_cloning import store
from app.services.voice_cloning.cache import cache_invalidate, cache_set
from app.services.voice_cloning.character_bridge import (
    age_to_group,
    assign_clone_to_character,
    profile_from_character_memory,
)
from app.services.voice_cloning.fingerprint import build_fingerprint, verify_speaker
from app.services.voice_cloning.models import (
    CloneObservability,
    CloneQuality,
    SpeakerProfile,
    VoiceCloneJob,
)
from app.services.voice_cloning.observability import (
    elapsed_ms,
    log_clone_event,
    start_timer,
)
from app.services.voice_cloning.quality import score_clone_quality
from app.services.voice_cloning.queue import clone_queue
from app.services.voice_cloning.security import (
    AuthContext,
    assert_ownership,
    audit_log,
    build_auth_context,
)
from app.services.voice_cloning.validation import validate_clone_reference
from app.services.voice_cloning.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PROVIDER_SIMULATION,
)


def _clone_id(reference_url: str, owner_id: str | None, character_id: str | None) -> str:
    digest = hashlib.sha1(
        f"{reference_url}|{owner_id or ''}|{character_id or ''}|{ENGINE_VERSION}".encode()
    ).hexdigest()
    return f"voiceclone_{digest[:10]}"


def _speaker_id(clone_id: str) -> str:
    return f"speaker_{clone_id.replace('voiceclone_', '')}"


def clone_voice(
    reference_url: str,
    *,
    owner_id: str | None = None,
    character_id: str | None = None,
    language: str = "en",
    accent: str = "neutral",
    speaking_style: str = "natural",
    emotion_profile: str = "calm",
    gender: str = "unspecified",
    age_group: str | None = None,
    duration_sec: float | None = None,
    sample_rate: int | None = None,
    file_type: str | None = None,
    mime_type: str | None = None,
    quality_hint: float | None = None,
    lock_voice: bool = False,
    provider: str = "simulation",
    enqueue: bool = True,
    auto_process: bool = True,
    parent_generation_id: str | None = None,
    parent_video_job_id: str | None = None,
    auth: AuthContext | None = None,
    skip_duplicate_check: bool = False,
) -> VoiceCloneJob:
    auth_ctx = auth or build_auth_context(owner_id=owner_id, backend_secret_ok=True)
    known = set() if skip_duplicate_check else store.known_checksums()
    validation = validate_clone_reference(
        reference_url,
        duration_sec=duration_sec,
        sample_rate=sample_rate,
        file_type=file_type,
        mime_type=mime_type,
        quality_hint=quality_hint,
        known_checksums=known,
    )
    if not validation.ok:
        raise ValueError("; ".join(validation.errors))

    t0 = start_timer()
    clone_id = _clone_id(reference_url.strip(), owner_id, character_id)
    fingerprint = build_fingerprint(
        reference_url=reference_url.strip(),
        checksum=validation.checksum,
        sample_rate=validation.sample_rate,
        duration_sec=validation.duration_sec,
    )
    speaker_ok = verify_speaker(fingerprint)
    age = age_group or age_to_group(None)
    speaker = SpeakerProfile(
        speaker_id=_speaker_id(clone_id),
        owner_id=owner_id,
        gender=gender,
        age_group=age,
        language=(language or "en").lower().split("-")[0],
        accent=accent or "neutral",
        speaking_style=speaking_style or "natural",
        emotion_profile=emotion_profile or "calm",
        fingerprint=fingerprint,
        locked=lock_voice,
        version=1,
        metadata={"engine": ENGINE_LABEL},
    )
    quality = score_clone_quality(
        fingerprint=fingerprint,
        reference_quality=validation.quality_hint,
        speaker_verified=speaker_ok,
        locked=lock_voice,
    )
    processing_ms = elapsed_ms(t0)
    events = [
        log_clone_event(
            "voice_clone_start",
            clone_id=clone_id,
            character_id=character_id,
            provider=provider,
        )
    ]

    job = VoiceCloneJob(
        clone_id=clone_id,
        engine=ENGINE_NAME,
        version=ENGINE_VERSION,
        state="queued",
        owner_id=owner_id,
        character_id=character_id,
        reference_url=reference_url.strip(),
        reference_checksum=validation.checksum,
        language=speaker.language,
        accent=speaker.accent,
        speaking_style=speaker.speaking_style,
        emotion_profile=speaker.emotion_profile,
        gender=gender,
        age_group=age,
        speaker=speaker,
        fingerprint=fingerprint,
        quality=quality,
        observability=CloneObservability(
            clone_id=clone_id,
            character_id=character_id,
            voice_version=1,
            training_duration_ms=0.0,
            processing_time_ms=processing_ms,
            queue_time_ms=0.0,
            provider=PROVIDER_SIMULATION if provider == "simulation" else provider,
            quality_score=quality.overall,
            log_events=events,
        ),
        voice_locked=lock_voice,
        voice_version=1,
        preview_url=f"/media/previews/{clone_id}.wav",
        asset_url=f"/media/clones/{clone_id}.wav",
        provider=provider,
        parent_generation_id=parent_generation_id,
        parent_video_job_id=parent_video_job_id,
        metadata={
            "warnings": validation.warnings,
            "file_type": validation.file_type,
            "sample_rate": validation.sample_rate,
            "duration_sec": validation.duration_sec,
            "engine_label": ENGINE_LABEL,
            "provider_secret_exposed": False,
            "auth": auth_ctx.to_dict(),
        },
    )

    store.put_clone(job)
    audit_log(
        "clone_created",
        clone_id=clone_id,
        character_id=character_id,
        owner_id=owner_id,
        detail={"quality": quality.overall},
    )

    if enqueue:
        clone_queue.enqueue(job)
        job.observability.queue_time_ms = round(clone_queue.queue_wait_ms(clone_id), 3)
        store.put_clone(job)

    if auto_process:
        job = process_clone_job(clone_id) or job

    if character_id and job.state == "completed":
        assign_clone_to_character(
            character_id,
            clone_id,
            lock=lock_voice,
            language=job.language,
            accent=job.accent,
            speaking_style=job.speaking_style,
            emotion_profile=job.emotion_profile,
            gender=job.gender,
            age_group=job.age_group,
            preview_url=job.preview_url,
            speaker_id=speaker.speaker_id,
        )

    events.append(
        log_clone_event(
            "voice_clone_complete",
            clone_id=clone_id,
            character_id=character_id,
            voice_version=job.voice_version,
            training_duration_ms=job.observability.training_duration_ms,
            processing_time_ms=job.observability.processing_time_ms,
            queue_time_ms=job.observability.queue_time_ms,
            retry_count=job.retry_count,
            provider=job.observability.provider,
            quality_score=job.quality.overall,
            state=job.state,
        )
    )
    job.observability.log_events = events
    store.put_clone(job)
    cache_set(f"clone:{clone_id}", job.summary())
    return job


def process_clone_job(clone_id: str) -> VoiceCloneJob | None:
    job = store.get_clone(clone_id) or clone_queue.get(clone_id)
    if not job:
        return None

    t0 = start_timer()
    clone_queue.update_state(clone_id, "preparing")
    job.state = "preparing"
    store.put_clone(job)

    clone_queue.update_state(clone_id, "training")
    job.state = "training"
    store.put_clone(job)

    train_ms = elapsed_ms(t0)
    job.observability.training_duration_ms = train_ms
    job.training_history.append(
        {
            "version": job.voice_version,
            "training_duration_ms": train_ms,
            "provider": job.provider,
            "quality": job.quality.overall,
        }
    )

    clone_queue.update_state(clone_id, "processing")
    job.state = "processing"
    store.put_clone(job)

    # Simulation success — never touch provider secrets
    job.production_ready = (
        job.quality.overall >= 0.7 and job.quality.speaker_verified and bool(job.fingerprint)
    )
    clone_queue.update_state(clone_id, "completed")
    job.state = "completed"
    job.queue_position = None
    job.observability.processing_time_ms = elapsed_ms(t0)
    job.observability.quality_score = job.quality.overall
    store.put_clone(job)

    log_clone_event(
        "voice_clone_processed",
        clone_id=clone_id,
        character_id=job.character_id,
        voice_version=job.voice_version,
        training_duration_ms=job.observability.training_duration_ms,
        processing_time_ms=job.observability.processing_time_ms,
        queue_time_ms=job.observability.queue_time_ms,
        retry_count=job.retry_count,
        provider=job.observability.provider,
        quality_score=job.quality.overall,
        state=job.state,
    )
    return job


def retrain_clone(
    clone_id: str,
    *,
    reference_url: str | None = None,
    owner_id: str | None = None,
    auth: AuthContext | None = None,
    auto_process: bool = True,
) -> VoiceCloneJob:
    job = store.get_clone(clone_id) or clone_queue.get(clone_id)
    if not job:
        raise ValueError(f"Clone '{clone_id}' not found")

    auth_ctx = auth or build_auth_context(owner_id=owner_id or job.owner_id, backend_secret_ok=True)
    assert_ownership(job.owner_id, auth_ctx)

    if job.voice_locked and reference_url and reference_url != job.reference_url:
        # Identity lock: allow retrain on same identity only via train endpoint bump
        pass

    url = (reference_url or job.reference_url).strip()
    validation = validate_clone_reference(
        url,
        duration_sec=job.metadata.get("duration_sec"),
        sample_rate=job.metadata.get("sample_rate"),
        file_type=job.metadata.get("file_type"),
        known_checksums=set(),  # retrain may reuse sample
    )
    if not validation.ok:
        raise ValueError("; ".join(validation.errors))

    fingerprint = build_fingerprint(
        reference_url=url,
        checksum=validation.checksum,
        sample_rate=validation.sample_rate,
        duration_sec=validation.duration_sec,
    )
    speaker_ok = verify_speaker(fingerprint)
    job.reference_url = url
    job.reference_checksum = validation.checksum
    job.fingerprint = fingerprint
    if job.speaker:
        job.speaker.fingerprint = fingerprint
        job.speaker.version += 1
    job.voice_version += 1
    job.observability.voice_version = job.voice_version
    job.quality = score_clone_quality(
        fingerprint=fingerprint,
        reference_quality=validation.quality_hint,
        speaker_verified=speaker_ok,
        locked=job.voice_locked,
    )
    job.state = "queued"
    job.production_ready = False
    store.put_clone(job)
    clone_queue.enqueue(job)
    audit_log(
        "clone_retrain",
        clone_id=clone_id,
        character_id=job.character_id,
        owner_id=job.owner_id,
        detail={"voice_version": job.voice_version},
    )
    cache_invalidate(f"clone:{clone_id}")
    if auto_process:
        job = process_clone_job(clone_id) or job
    return job


def lock_clone_voice(clone_id: str, *, locked: bool = True, owner_id: str | None = None) -> VoiceCloneJob:
    job = store.get_clone(clone_id)
    if not job:
        raise ValueError(f"Clone '{clone_id}' not found")
    assert_ownership(job.owner_id, build_auth_context(owner_id=owner_id, backend_secret_ok=True))
    job.voice_locked = locked
    if job.speaker:
        job.speaker.locked = locked
    store.put_clone(job)
    if job.character_id:
        profile = store.get_character(job.character_id)
        if profile:
            profile.voice_locked = locked
            store.put_character(profile)
    audit_log("voice_lock", clone_id=clone_id, character_id=job.character_id, owner_id=job.owner_id)
    return job


def switch_character_voice(
    character_id: str,
    clone_id: str,
    *,
    lock: bool = False,
) -> Any:
    return assign_clone_to_character(character_id, clone_id, lock=lock)


def clone_voice_dict(reference_url: str, **kwargs: Any) -> dict[str, Any]:
    job = clone_voice(reference_url, **kwargs)
    return {
        "clone": job.to_dict(),
        "summary": job.summary(),
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
    }


def get_clone(clone_id: str) -> VoiceCloneJob | None:
    return store.get_clone(clone_id) or clone_queue.get(clone_id)


def preview_clone(clone_id: str) -> dict[str, Any]:
    job = get_clone(clone_id)
    if not job:
        raise ValueError(f"Clone '{clone_id}' not found")
    return {
        "clone_id": clone_id,
        "preview_url": job.preview_url,
        "asset_url": job.asset_url,
        "voice_version": job.voice_version,
        "quality": job.quality.to_dict(),
        "state": job.state,
    }


# Re-export helpers used by routes / orchestrator
__all__ = [
    "clone_voice",
    "clone_voice_dict",
    "process_clone_job",
    "retrain_clone",
    "lock_clone_voice",
    "switch_character_voice",
    "get_clone",
    "preview_clone",
    "assign_clone_to_character",
    "profile_from_character_memory",
]
