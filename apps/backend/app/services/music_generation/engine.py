"""Music Generation & Composition Engine."""

from __future__ import annotations

import hashlib
from typing import Any

from app.services.music_generation import store
from app.services.music_generation.cache import cache_set
from app.services.music_generation.library import index_job, library_payload
from app.services.music_generation.models import MusicControls, MusicJob, MusicObservability
from app.services.music_generation.observability import elapsed_ms, log_music_event, start_timer
from app.services.music_generation.queue import music_queue
from app.services.music_generation.validation import validate_generate_request
from app.services.music_generation.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PROVIDER_SIMULATION,
)
from app.services.music_generation.video_bridge import adapt_from_video_context


def _job_id(genre: str, role: str, bpm: int, duration: float) -> str:
    digest = hashlib.sha1(
        f"{genre}|{role}|{bpm}|{duration}|{ENGINE_VERSION}".encode()
    ).hexdigest()
    return f"musicjob_{digest[:10]}"


def generate_music(
    *,
    genre: str | None = None,
    role: str | None = "background",
    title: str | None = None,
    bpm: int | None = None,
    key: str | None = None,
    mood: str | None = None,
    energy: float | None = None,
    intensity: float | None = None,
    duration_sec: float | None = None,
    instruments: list[str] | None = None,
    loop: bool | None = None,
    fade_in_sec: float | None = None,
    fade_out_sec: float | None = None,
    provider: str = "simulation",
    enqueue: bool = True,
    auto_process: bool = True,
    parent_audio_job_id: str | None = None,
    parent_video_job_id: str | None = None,
    parent_generation_id: str | None = None,
    scene_emotion: str | None = None,
    scene_duration_sec: float | None = None,
    camera_motion: str | None = None,
    story_beat: str | None = None,
    prompt: str | None = None,
    audio_director: dict[str, Any] | None = None,
    video_engine: dict[str, Any] | None = None,
    director: dict[str, Any] | None = None,
    scenes: list[dict[str, Any]] | None = None,
    character_memory: list[dict[str, Any]] | None = None,
) -> MusicJob:
    # Auto-adapt from video/director context when fields omitted
    adapted = adapt_from_video_context(
        prompt=prompt,
        audio_director=audio_director,
        video_engine=video_engine,
        director=director,
        scenes=scenes,
        character_memory=character_memory,
        camera_motion=camera_motion,
    )
    validation = validate_generate_request(
        genre=genre or adapted["genre"],
        role=role or adapted["role"],
        bpm=bpm,
        key=key,
        mood=mood or adapted.get("scene_emotion") or None,
        energy=energy if energy is not None else adapted["energy"],
        intensity=intensity if intensity is not None else adapted["intensity"],
        duration_sec=duration_sec if duration_sec is not None else adapted["duration_sec"],
        instruments=instruments,
        loop=loop if loop is not None else adapted["loop"],
        fade_in_sec=fade_in_sec,
        fade_out_sec=fade_out_sec,
    )
    if not validation.ok:
        raise ValueError("; ".join(validation.errors))

    t0 = start_timer()
    job_id = _job_id(
        validation.genre, validation.role, validation.bpm, validation.duration_sec
    )
    controls = MusicControls(
        bpm=validation.bpm,
        key=validation.key,
        mood=validation.mood,
        energy=validation.energy,
        intensity=validation.intensity,
        duration_sec=validation.duration_sec,
        instruments=list(validation.instruments),
        loop=validation.loop,
        fade_in_sec=validation.fade_in_sec,
        fade_out_sec=validation.fade_out_sec,
    )
    title_s = (title or f"RTAS {validation.genre.title()} {validation.role.title()}").strip()[:120]
    processing_ms = elapsed_ms(t0)
    events = [
        log_music_event(
            "music_generate_start",
            music_job_id=job_id,
            genre=validation.genre,
            bpm=validation.bpm,
            duration_sec=validation.duration_sec,
            mood=validation.mood,
            provider=provider,
        )
    ]

    job = MusicJob(
        job_id=job_id,
        engine=ENGINE_NAME,
        version=ENGINE_VERSION,
        state="queued",
        genre=validation.genre,
        role=validation.role,  # type: ignore[arg-type]
        title=title_s,
        controls=controls,
        observability=MusicObservability(
            music_job_id=job_id,
            genre=validation.genre,
            bpm=validation.bpm,
            duration_sec=validation.duration_sec,
            mood=validation.mood,
            processing_time_ms=processing_ms,
            queue_time_ms=0.0,
            provider=PROVIDER_SIMULATION if provider == "simulation" else provider,
            log_events=events,
        ),
        asset_url=f"/media/music/{job_id}.wav",
        preview_url=f"/media/music/previews/{job_id}.mp3",
        stem_urls={
            s: f"/media/music/stems/{job_id}_{s}.wav" for s in controls.stems
        },
        provider=provider,
        parent_audio_job_id=parent_audio_job_id,
        parent_video_job_id=parent_video_job_id,
        parent_generation_id=parent_generation_id,
        scene_emotion=scene_emotion or adapted.get("scene_emotion"),
        scene_duration_sec=scene_duration_sec or adapted.get("scene_duration_sec"),
        camera_motion=camera_motion or adapted.get("camera_motion"),
        story_beat=story_beat or adapted.get("story_beat"),
        metadata={
            "warnings": validation.warnings,
            "engine_label": ENGINE_LABEL,
            "provider_secret_exposed": False,
            "adapted_from_video": bool(video_engine or director or scenes),
        },
    )

    store.put_job(job)

    if enqueue:
        music_queue.enqueue(job)
        job.observability.queue_time_ms = round(music_queue.queue_wait_ms(job_id), 3)
        store.put_job(job)

    if auto_process:
        job = process_music_job(job_id) or job

    events.append(
        log_music_event(
            "music_generate_complete",
            music_job_id=job_id,
            genre=job.genre,
            bpm=job.controls.bpm,
            duration_sec=job.controls.duration_sec,
            mood=job.controls.mood,
            processing_time_ms=job.observability.processing_time_ms,
            queue_time_ms=job.observability.queue_time_ms,
            provider=job.observability.provider,
            retry_count=job.retry_count,
            state=job.state,
        )
    )
    job.observability.log_events = events
    store.put_job(job)
    cache_set(f"job:{job_id}", job.summary())
    return job


def process_music_job(job_id: str) -> MusicJob | None:
    job = store.get_job(job_id) or music_queue.get(job_id)
    if not job:
        return None

    t0 = start_timer()
    for state in ("preparing", "composing", "generating", "mixing"):
        music_queue.update_state(job_id, state)  # type: ignore[arg-type]
        job.state = state  # type: ignore[assignment]
        store.put_job(job)

    # Simulation mix success
    fade_in = min(job.controls.fade_in_sec, job.controls.duration_sec / 3)
    fade_out = min(job.controls.fade_out_sec, job.controls.duration_sec / 3)
    job.metadata["mix"] = {
        "fade_in_sec": fade_in,
        "fade_out_sec": fade_out,
        "loop": job.controls.loop,
        "stems": list(job.controls.stems),
    }
    job.production_ready = (
        job.controls.duration_sec >= 2.0
        and bool(job.controls.instruments)
        and bool(job.asset_url)
    )
    index_job(job)
    store.put_version(
        job_id,
        {
            "music_version": job.music_version,
            "genre": job.genre,
            "bpm": job.controls.bpm,
            "asset_url": job.asset_url,
            "summary": job.summary(),
        },
    )
    music_queue.update_state(job_id, "completed")
    job.state = "completed"
    job.queue_position = None
    job.observability.processing_time_ms = elapsed_ms(t0)
    store.put_job(job)

    log_music_event(
        "music_job_processed",
        music_job_id=job_id,
        genre=job.genre,
        bpm=job.controls.bpm,
        duration_sec=job.controls.duration_sec,
        mood=job.controls.mood,
        processing_time_ms=job.observability.processing_time_ms,
        queue_time_ms=job.observability.queue_time_ms,
        provider=job.observability.provider,
        retry_count=job.retry_count,
        state=job.state,
    )
    return job


def generate_music_dict(**kwargs: Any) -> dict[str, Any]:
    job = generate_music(**kwargs)
    return {
        "job": job.to_dict(),
        "summary": job.summary(),
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
    }


def get_job(job_id: str) -> MusicJob | None:
    return store.get_job(job_id) or music_queue.get(job_id)


def version_payload(job_id: str | None = None) -> dict[str, Any]:
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        "sprint": 4,
        "phase": "Phase 4",
        "job_versions": store.get_versions(job_id),
    }
