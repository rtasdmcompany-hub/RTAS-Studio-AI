"""Voice Generation Engine — TTS planning + queue orchestration."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.voice_generation.export import build_export
from app.services.voice_generation.models import (
    VoiceControls,
    VoiceGenerationJob,
    VoiceObservability,
)
from app.services.voice_generation.observability import (
    elapsed_ms,
    log_voice_event,
    start_timer,
)
from app.services.voice_generation.presets import get_voice
from app.services.voice_generation.quality import estimate_duration_sec, score_quality
from app.services.voice_generation.queue import voice_queue
from app.services.voice_generation.ssml import build_ssml
from app.services.voice_generation import store
from app.services.voice_generation.validation import validate_generate_request
from app.services.voice_generation.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION


def _job_id(text: str, voice_id: str, language: str) -> str:
    digest = hashlib.sha1(f"{text}|{voice_id}|{language}|{ENGINE_VERSION}".encode()).hexdigest()
    return f"voicejob_{digest[:10]}"


def generate_voice(
    text: str,
    *,
    language: str | None = "en",
    voice_id: str | None = None,
    gender: str | None = "female",
    speed: float = 1.0,
    pitch: float = 0.0,
    volume: float = 1.0,
    pause_ms: int = 0,
    pronunciation_hints: dict[str, str] | None = None,
    provider: str = "simulation",
    enqueue: bool = True,
    auto_process: bool = True,
    parent_audio_job_id: str | None = None,
    parent_generation_id: str | None = None,
) -> VoiceGenerationJob:
    validation = validate_generate_request(
        text=text,
        language=language,
        voice_id=voice_id,
        gender=gender,
        speed=speed,
        pitch=pitch,
        volume=volume,
        pause_ms=pause_ms,
    )
    if not validation.ok:
        raise ValueError("; ".join(validation.errors))

    t0 = start_timer()
    preset = get_voice(validation.voice_id)
    controls = VoiceControls(
        speed=float(speed),
        pitch=float(pitch),
        volume=float(volume),
        pause_ms=int(pause_ms),
        pronunciation_hints=dict(pronunciation_hints or {}),
    )
    ssml = build_ssml(
        text.strip(),
        language=validation.language,
        voice_id=preset.voice_id,
        controls=controls,
    )
    duration = estimate_duration_sec(text, controls)
    quality = score_quality(
        text=text,
        language=validation.language,
        controls=controls,
        has_ssml=True,
    )
    job_id = _job_id(text.strip(), preset.voice_id, validation.language)
    processing_ms = elapsed_ms(t0)

    events = [
        log_voice_event(
            "voice_generate_start",
            voice_job_id=job_id,
            voice_model=preset.provider_model,
            language=validation.language,
        )
    ]

    job = VoiceGenerationJob(
        job_id=job_id,
        engine=ENGINE_NAME,
        version=ENGINE_VERSION,
        text=text.strip(),
        language=validation.language,
        voice_id=preset.voice_id,
        gender=preset.gender,
        state="queued",
        controls=controls,
        ssml=ssml,
        estimated_duration_sec=duration,
        quality=quality,
        export=build_export(job_id, ready=False),
        observability=VoiceObservability(
            voice_job_id=job_id,
            voice_model=preset.provider_model,
            language=validation.language,
            duration_sec=duration,
            processing_time_ms=processing_ms,
            queue_time_ms=0.0,
            log_events=events,
        ),
        metadata={
            "warnings": validation.warnings,
            "style": preset.style,
            "sample_rate": preset.sample_rate,
            "engine_label": ENGINE_LABEL,
            # Never store provider secrets
            "provider_secret_exposed": False,
        },
        provider=provider,
        parent_audio_job_id=parent_audio_job_id,
        parent_generation_id=parent_generation_id,
        production_ready=False,
    )

    # Simulation asset hint (no binary synthesis / no secrets)
    job.asset_url = f"/media/outputs/{job_id}.wav"

    store.put_job(job)

    if enqueue:
        voice_queue.enqueue(job)
        q_ms = voice_queue.queue_wait_ms(job_id)
        job.observability.queue_time_ms = round(q_ms, 3)
        store.put_job(job)

    if auto_process:
        job = process_voice_job(job_id) or job

    events.append(
        log_voice_event(
            "voice_generate_complete",
            voice_job_id=job_id,
            voice_model=preset.provider_model,
            language=validation.language,
            duration_sec=duration,
            processing_time_ms=job.observability.processing_time_ms,
            queue_time_ms=job.observability.queue_time_ms,
            retry_count=job.retry_count,
            state=job.state,
        )
    )
    job.observability.log_events = events
    store.put_job(job)
    return job


def process_voice_job(job_id: str) -> VoiceGenerationJob | None:
    job = store.get_job(job_id) or voice_queue.get(job_id)
    if not job:
        return None

    voice_queue.update_state(job_id, "preparing")
    job.state = "preparing"
    store.put_job(job)

    voice_queue.update_state(job_id, "generating")
    job.state = "generating"
    store.put_job(job)

    # Simulation "synthesis" success path
    job.export = build_export(job_id, ready=True)
    job.production_ready = job.quality.overall >= 0.7 and bool(job.ssml)
    voice_queue.update_state(job_id, "completed")
    job.state = "completed"
    job.queue_position = None
    store.put_job(job)

    log_voice_event(
        "voice_job_processed",
        voice_job_id=job_id,
        voice_model=job.observability.voice_model,
        language=job.language,
        duration_sec=job.estimated_duration_sec,
        processing_time_ms=job.observability.processing_time_ms,
        queue_time_ms=job.observability.queue_time_ms,
        retry_count=job.retry_count,
        state=job.state,
    )
    return job


def generate_voice_dict(text: str, **kwargs: Any) -> dict[str, Any]:
    job = generate_voice(text, **kwargs)
    return {
        "job": job.to_dict(),
        "summary": job.summary(),
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
    }


def get_job(job_id: str) -> VoiceGenerationJob | None:
    return store.get_job(job_id) or voice_queue.get(job_id)
