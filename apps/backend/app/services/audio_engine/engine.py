"""AudioEngine — central orchestration for Phase 4 audio production."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.audio_engine.ambient import build_ambient_clips
from app.services.audio_engine.exporter import build_export_package
from app.services.audio_engine.metadata import build_metadata
from app.services.audio_engine.models import AudioEnginePlan
from app.services.audio_engine.music import build_music_clips
from app.services.audio_engine.observability import (
    build_observability,
    elapsed_ms,
    log_event,
    start_timer,
)
from app.services.audio_engine.queue import audio_queue
from app.services.audio_engine.sfx import build_sfx_clips
from app.services.audio_engine import store
from app.services.audio_engine.timeline import build_timeline, timeline_duration_sec
from app.services.audio_engine.validator import validate_audio_plan
from app.services.audio_engine.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION
from app.services.audio_engine.voice import build_voice_clips


def _job_id(prompt: str, parent: str | None = None) -> str:
    seed = f"{prompt}|{parent or ''}|{ENGINE_VERSION}"
    return f"audioeng_{hashlib.sha1(seed.encode()).hexdigest()[:10]}"


def build_audio_engine_plan(
    prompt: str,
    *,
    audio_director: dict[str, Any] | None = None,
    lip_sync: dict[str, Any] | None = None,
    provider: str = "simulation",
    enqueue: bool = True,
    auto_process: bool = True,
    parent_generation_id: str | None = None,
) -> AudioEnginePlan:
    """Build a modular audio production plan; optionally queue and process it."""
    t0 = start_timer()
    events: list[dict[str, Any]] = []
    job_id = _job_id(prompt, parent_generation_id)

    events.append(
        log_event(
            "audio_plan_start",
            generation_id=parent_generation_id,
            job_id=job_id,
            provider=provider,
        )
    )

    voice = build_voice_clips(prompt, audio_director)
    music = build_music_clips(prompt, audio_director)
    ambient = build_ambient_clips(prompt, audio_director)
    sfx = build_sfx_clips(prompt, audio_director)

    if lip_sync and not voice:
        cues = lip_sync.get("viseme_timeline") or lip_sync.get("cues") or []
        if cues:
            voice = build_voice_clips(prompt or "Spoken dialogue", audio_director)

    duration = timeline_duration_sec(voice, music, ambient, sfx)
    timeline = build_timeline(voice, music, ambient, sfx)
    validation = validate_audio_plan(
        prompt=prompt,
        voice=voice,
        music=music,
        ambient=ambient,
        sfx=sfx,
        duration_sec=duration,
    )
    metadata = build_metadata(job_id, duration_sec=duration, voice=voice, version=1)
    export = build_export_package(job_id, validation=validation)
    duration_ms = elapsed_ms(t0)

    plan = AudioEnginePlan(
        job_id=job_id,
        engine=ENGINE_NAME,
        version=ENGINE_VERSION,
        prompt=prompt.strip(),
        state="queued",
        voice_clips=voice,
        music_clips=music,
        ambient_clips=ambient,
        sfx_clips=sfx,
        timeline=timeline,
        metadata=metadata,
        validation=validation,
        export=export,
        observability=build_observability(
            generation_id=parent_generation_id,
            provider=provider,
            queue_time_ms=0.0,
            duration_ms=duration_ms,
            events=events,
            errors=list(validation.issues),
        ),
        parent_generation_id=parent_generation_id,
        production_ready=validation.passed and export.ready,
    )

    store.put_plan(plan)

    if enqueue:
        audio_queue.enqueue(plan)
        q_ms = audio_queue.queue_wait_ms(job_id)
        plan.observability.queue_time_ms = round(q_ms, 3)
        plan.observability.latency_ms = round(q_ms + duration_ms, 3)
        store.put_plan(plan)

    if auto_process:
        plan = process_audio_job(plan.job_id) or plan

    events.append(
        log_event(
            "audio_plan_complete",
            generation_id=parent_generation_id,
            job_id=job_id,
            provider=provider,
            duration_ms=duration_ms,
            queue_time_ms=plan.observability.queue_time_ms,
            latency_ms=plan.observability.latency_ms,
            production_ready=plan.production_ready,
            state=plan.state,
            engine=ENGINE_LABEL,
        )
    )
    plan.observability.log_events = events
    store.put_plan(plan)
    return plan


def process_audio_job(job_id: str) -> AudioEnginePlan | None:
    """Advance one job through preparing → generating → processing → terminal."""
    plan = store.get_plan(job_id) or audio_queue.get(job_id)
    if not plan:
        return None

    audio_queue.update_state(job_id, "preparing")
    plan.state = "preparing"
    store.put_plan(plan)

    audio_queue.update_state(job_id, "generating")
    plan.state = "generating"
    store.put_plan(plan)

    audio_queue.update_state(job_id, "processing")
    plan.state = "processing"
    store.put_plan(plan)

    if plan.validation.passed:
        audio_queue.update_state(job_id, "completed")
        plan.state = "completed"
        plan.queue_position = None
        plan.production_ready = True
    else:
        audio_queue.update_state(
            job_id,
            "failed",
            error="; ".join(plan.validation.issues) or "validation_failed",
        )
        plan.state = "failed"
        plan.queue_position = None
        plan.production_ready = False

    store.put_plan(plan)
    log_event(
        "audio_job_processed",
        generation_id=plan.parent_generation_id,
        job_id=job_id,
        provider=plan.observability.provider,
        state=plan.state,
        production_ready=plan.production_ready,
    )
    return plan


def build_audio_engine_dict(prompt: str, **kwargs: Any) -> dict[str, Any]:
    plan = build_audio_engine_plan(prompt, **kwargs)
    return {
        "plan": plan.to_dict(),
        "summary": plan.summary(),
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
    }


def get_plan(job_id: str) -> AudioEnginePlan | None:
    return store.get_plan(job_id) or audio_queue.get(job_id)
