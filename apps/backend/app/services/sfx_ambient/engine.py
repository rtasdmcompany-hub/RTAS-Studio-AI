"""Sound Effects & Ambient Audio Engine."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.sfx_ambient import store
from app.services.sfx_ambient.cache import cache_set
from app.services.sfx_ambient.library import (
    ambient_catalog_payload,
    index_job,
    library_payload,
    sfx_catalog_payload,
)
from app.services.sfx_ambient.layering import build_layers, build_timeline_events
from app.services.sfx_ambient.models import JobKind, SfxJob, SfxObservability
from app.services.sfx_ambient.observability import elapsed_ms, log_sfx_event, start_timer
from app.services.sfx_ambient.queue import sfx_queue
from app.services.sfx_ambient.validation import validate_generate_request
from app.services.sfx_ambient.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PROVIDER_SIMULATION,
)
from app.services.sfx_ambient.video_bridge import adapt_from_video_context


def _job_id(kind: str, categories: list[str], duration: float, scene_id: str | None) -> str:
    digest = hashlib.sha1(
        f"{kind}|{','.join(categories)}|{duration}|{scene_id or ''}|{ENGINE_VERSION}".encode()
    ).hexdigest()
    return f"sfxjob_{digest[:10]}"


def generate_sfx_ambient(
    *,
    kind: JobKind = "scene",
    categories: list[str] | None = None,
    category: str | None = None,
    duration_sec: float | None = None,
    volume: float | None = None,
    loop: bool | None = None,
    fade_in_sec: float | None = None,
    fade_out_sec: float | None = None,
    environment: str | None = None,
    provider: str = "simulation",
    enqueue: bool = True,
    auto_process: bool = True,
    prompt: str | None = None,
    audio_director: dict[str, Any] | None = None,
    video_engine: dict[str, Any] | None = None,
    director: dict[str, Any] | None = None,
    scenes: list[dict[str, Any]] | None = None,
    music_summary: dict[str, Any] | None = None,
    camera_motion: dict[str, Any] | str | None = None,
    parent_audio_job_id: str | None = None,
    parent_music_job_id: str | None = None,
    parent_video_job_id: str | None = None,
    parent_generation_id: str | None = None,
    scene_id: str | None = None,
) -> SfxJob:
    adapted = adapt_from_video_context(
        prompt=prompt,
        audio_director=audio_director,
        video_engine=video_engine,
        director=director,
        scenes=scenes,
        music_summary=music_summary,
        camera_motion=camera_motion,
        explicit_categories=categories,
        explicit_environment=environment,
    )
    validation = validate_generate_request(
        categories=categories or adapted["categories"],
        category=category,
        duration_sec=duration_sec if duration_sec is not None else adapted["duration_sec"],
        volume=volume if volume is not None else adapted["volume"],
        fade_in_sec=fade_in_sec,
        fade_out_sec=fade_out_sec,
        loop=loop,
        kind=kind,
    )
    if not validation.ok:
        raise ValueError("; ".join(validation.errors))

    t0 = start_timer()
    env_profile = adapted["environment_profile"]
    sid = scene_id or adapted.get("scene_id")
    job_id = _job_id(kind, validation.categories, validation.duration_sec, sid)

    layers = build_layers(
        validation.categories,
        duration_sec=validation.duration_sec,
        base_volume=validation.volume,
        loop=validation.loop,
        fade_in_sec=validation.fade_in_sec,
        fade_out_sec=validation.fade_out_sec,
        job_id=job_id,
    )
    events = build_timeline_events(layers, scene_id=sid, job_id=job_id)
    processing_ms = elapsed_ms(t0)

    events_log = [
        log_sfx_event(
            "sfx_generate_start",
            sfx_job_id=job_id,
            scene_id=sid,
            environment=env_profile.environment,
        )
    ]

    job = SfxJob(
        job_id=job_id,
        engine=ENGINE_NAME,
        version=ENGINE_VERSION,
        state="queued",
        kind=kind,
        categories=validation.categories,
        environment=env_profile,
        layers=layers,
        timeline_events=events,
        observability=SfxObservability(
            sfx_job_id=job_id,
            scene_id=sid,
            environment=env_profile.environment,
            duration_sec=validation.duration_sec,
            processing_time_ms=processing_ms,
            queue_time_ms=0.0,
            provider=PROVIDER_SIMULATION if provider == "simulation" else provider,
            asset_usage=[],
            log_events=events_log,
        ),
        duration_sec=validation.duration_sec,
        volume=validation.volume,
        loop=validation.loop,
        fade_in_sec=validation.fade_in_sec,
        fade_out_sec=validation.fade_out_sec,
        asset_url=f"/media/sfx/{job_id}/mix.wav",
        preview_url=f"/media/sfx/{job_id}/preview.wav",
        provider=provider,
        parent_audio_job_id=parent_audio_job_id,
        parent_music_job_id=parent_music_job_id,
        parent_video_job_id=parent_video_job_id,
        parent_generation_id=parent_generation_id,
        scene_id=sid,
        metadata={
            "warnings": validation.warnings,
            "engine_label": ENGINE_LABEL,
            "provider_secret_exposed": False,
            "camera_motion": adapted.get("camera_motion"),
            "story_beat": adapted.get("story_beat"),
            "mood": env_profile.mood,
        },
    )

    store.put_job(job)

    if enqueue:
        sfx_queue.enqueue(job)
        job.observability.queue_time_ms = round(sfx_queue.queue_wait_ms(job_id), 3)
        store.put_job(job)

    if auto_process:
        job = process_sfx_job(job_id) or job

    events_log.append(
        log_sfx_event(
            "sfx_generate_complete",
            sfx_job_id=job_id,
            scene_id=sid,
            environment=env_profile.environment,
            duration_sec=job.duration_sec,
            processing_time_ms=job.observability.processing_time_ms,
            queue_time_ms=job.observability.queue_time_ms,
            retry_count=job.retry_count,
            state=job.state,
        )
    )
    job.observability.log_events = events_log
    store.put_job(job)
    cache_set(f"sfx:{job_id}", job.summary())
    return job


def process_sfx_job(job_id: str) -> SfxJob | None:
    job = store.get_job(job_id) or sfx_queue.get(job_id)
    if not job:
        return None

    t0 = start_timer()
    sfx_queue.update_state(job_id, "preparing")
    job.state = "preparing"
    store.put_job(job)

    sfx_queue.update_state(job_id, "searching")
    job.state = "searching"
    store.put_job(job)

    sfx_queue.update_state(job_id, "generating")
    job.state = "generating"
    store.put_job(job)

    sfx_queue.update_state(job_id, "layering")
    job.state = "layering"
    store.put_job(job)

    ids = index_job(job)
    job.observability.asset_usage = ids
    job.production_ready = len(job.layers) > 0 and bool(job.timeline_events)
    job.observability.processing_time_ms = elapsed_ms(t0)

    sfx_queue.update_state(job_id, "completed")
    job.state = "completed"
    job.queue_position = None
    store.put_job(job)

    log_sfx_event(
        "sfx_job_processed",
        sfx_job_id=job_id,
        scene_id=job.scene_id,
        environment=job.environment.environment,
        duration_sec=job.duration_sec,
        processing_time_ms=job.observability.processing_time_ms,
        queue_time_ms=job.observability.queue_time_ms,
        retry_count=job.retry_count,
        state=job.state,
        asset_usage=len(ids),
    )
    return job


def generate_sfx(**kwargs: Any) -> SfxJob:
    kwargs.setdefault("kind", "sfx")
    return generate_sfx_ambient(**kwargs)


def generate_ambient(**kwargs: Any) -> SfxJob:
    kwargs.setdefault("kind", "ambient")
    kwargs.setdefault("loop", True)
    return generate_sfx_ambient(**kwargs)


def generate_sfx_dict(**kwargs: Any) -> dict[str, Any]:
    job = generate_sfx(**kwargs)
    return {
        "job": job.to_dict(),
        "summary": job.summary(),
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
    }


def generate_ambient_dict(**kwargs: Any) -> dict[str, Any]:
    job = generate_ambient(**kwargs)
    return {
        "job": job.to_dict(),
        "summary": job.summary(),
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
    }


def generate_scene_audio_dict(**kwargs: Any) -> dict[str, Any]:
    kwargs.setdefault("kind", "scene")
    job = generate_sfx_ambient(**kwargs)
    return {
        "job": job.to_dict(),
        "summary": job.summary(),
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
    }


def get_job(job_id: str) -> SfxJob | None:
    return store.get_job(job_id) or sfx_queue.get(job_id)


__all__ = [
    "generate_sfx_ambient",
    "generate_sfx",
    "generate_ambient",
    "generate_sfx_dict",
    "generate_ambient_dict",
    "generate_scene_audio_dict",
    "process_sfx_job",
    "get_job",
    "library_payload",
    "sfx_catalog_payload",
    "ambient_catalog_payload",
]
