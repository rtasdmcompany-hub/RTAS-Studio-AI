"""Audio Timeline & Cinematic Synchronization Engine."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from app.services.audio_timeline import store
from app.services.audio_timeline.cache import cache_set
from app.services.audio_timeline.export import build_export_payload
from app.services.audio_timeline.models import (
    TimelineJob,
    TimelineObservability,
    TimelineVersion,
)
from app.services.audio_timeline.observability import elapsed_ms, log_timeline_event, start_timer
from app.services.audio_timeline.queue import timeline_queue
from app.services.audio_timeline.sync import run_synchronization
from app.services.audio_timeline.tracks import (
    build_default_tracks,
    build_layers,
    populate_tracks_from_sources,
    timeline_duration,
)
from app.services.audio_timeline.validation import validate_timeline_request
from app.services.audio_timeline.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PROVIDER_SIMULATION,
)


def _job_id(*parts: str) -> str:
    digest = hashlib.sha1(
        ("|".join(parts) + f"|{ENGINE_VERSION}").encode()
    ).hexdigest()
    return f"tljob_{digest[:10]}"


def _snapshot(job: TimelineJob) -> dict[str, Any]:
    return {
        "state": job.state,
        "track_count": len(job.tracks),
        "sync_accuracy": job.sync.sync_accuracy,
        "duration_sec": job.duration_sec,
        "timeline_version": job.timeline_version,
    }


def create_timeline(
    *,
    fps: float = 24.0,
    duration_sec: float | None = None,
    scenes: list[dict[str, Any]] | None = None,
    shots: list[dict[str, Any]] | None = None,
    lip_sync: dict[str, Any] | None = None,
    camera_plan: dict[str, Any] | None = None,
    audio_director: dict[str, Any] | None = None,
    voice_summary: dict[str, Any] | None = None,
    music_summary: dict[str, Any] | None = None,
    sfx_summary: dict[str, Any] | None = None,
    ambient_summary: dict[str, Any] | None = None,
    mix_summary: dict[str, Any] | None = None,
    localization_summary: dict[str, Any] | None = None,
    bpm: float = 96.0,
    snap_enabled: bool = True,
    auto_align: bool = True,
    locked: bool = False,
    provider: str = "simulation",
    enqueue: bool = True,
    auto_process: bool = True,
    parent_voice_job_id: str | None = None,
    parent_music_job_id: str | None = None,
    parent_sfx_job_id: str | None = None,
    parent_mix_job_id: str | None = None,
    parent_localization_job_id: str | None = None,
    parent_video_job_id: str | None = None,
    parent_generation_id: str | None = None,
) -> TimelineJob:
    validation = validate_timeline_request(
        fps=fps,
        duration_sec=duration_sec,
        scenes=scenes,
        snap_enabled=snap_enabled,
        auto_align=auto_align,
        locked=locked,
    )
    if not validation.ok:
        raise ValueError("; ".join(validation.errors))

    t0 = start_timer()
    scenes = scenes or []
    shots = shots or []
    resolved_duration = validation.duration_sec
    if resolved_duration <= 0:
        resolved_duration = max(
            4.0,
            float((voice_summary or {}).get("duration_sec") or 0) or 0.0,
            float((music_summary or {}).get("duration_sec") or 0) or 0.0,
            len(scenes) * 2.0 if scenes else 8.0,
        )

    job_id = _job_id(
        str(parent_generation_id or ""),
        str(len(scenes)),
        str(len(shots)),
        str(resolved_duration),
        str(validation.fps),
    )

    tracks = build_default_tracks()
    tracks = populate_tracks_from_sources(
        tracks,
        scenes=scenes,
        shots=shots,
        voice_summary=voice_summary,
        music_summary=music_summary,
        sfx_summary=sfx_summary,
        ambient_summary=ambient_summary,
        mix_summary=mix_summary,
        localization_summary=localization_summary,
        audio_director=audio_director,
        duration_sec=resolved_duration,
    )
    layers = build_layers(tracks)
    duration = timeline_duration(tracks, fallback=resolved_duration)

    beat_markers, sync = run_synchronization(
        tracks,
        fps=validation.fps,
        duration_sec=duration,
        scenes=scenes,
        shots=shots,
        lip_sync=lip_sync,
        camera_plan=camera_plan,
        bpm=bpm,
        snap_enabled=validation.snap_enabled,
        auto_align=validation.auto_align,
    )

    processing_ms = elapsed_ms(t0)
    events = [
        log_timeline_event(
            "timeline_create",
            timeline_id=job_id,
            scene_count=len(scenes),
            track_count=len(tracks),
            sync_accuracy=sync.sync_accuracy,
        )
    ]

    job = TimelineJob(
        job_id=job_id,
        engine=ENGINE_NAME,
        version=ENGINE_VERSION,
        state="queued",
        tracks=tracks,
        layers=layers,
        beat_markers=beat_markers,
        sync=sync,
        observability=TimelineObservability(
            timeline_id=job_id,
            scene_count=len(scenes),
            track_count=len(tracks),
            sync_accuracy=sync.sync_accuracy,
            processing_time_ms=processing_ms,
            queue_time_ms=0.0,
            provider=PROVIDER_SIMULATION if provider == "simulation" else provider,
            log_events=events,
        ),
        duration_sec=duration,
        fps=validation.fps,
        locked=validation.locked,
        snap_enabled=validation.snap_enabled,
        auto_align=validation.auto_align,
        production_ready=False,
        export_url=f"/media/timeline/{job_id}/master.json",
        master_timeline_url=f"/media/timeline/{job_id}/master.timeline",
        provider=provider,
        timeline_version=1,
        versions=[],
        history=[],
        parent_voice_job_id=parent_voice_job_id or (voice_summary or {}).get("job_id"),
        parent_music_job_id=parent_music_job_id or (music_summary or {}).get("job_id"),
        parent_sfx_job_id=parent_sfx_job_id or (sfx_summary or {}).get("job_id"),
        parent_mix_job_id=parent_mix_job_id or (mix_summary or {}).get("job_id"),
        parent_localization_job_id=parent_localization_job_id
        or (localization_summary or {}).get("job_id"),
        parent_video_job_id=parent_video_job_id,
        parent_generation_id=parent_generation_id,
        metadata={
            "bpm": bpm,
            "scenes": scenes,
            "shots": shots,
            "lip_sync": lip_sync,
            "camera_plan": camera_plan,
        },
    )
    job.versions.append(
        TimelineVersion(
            version=1,
            label="initial",
            snapshot=_snapshot(job),
            created_at=time.time(),
        )
    )
    job.history.append({"status": "queued", "snapshot": _snapshot(job), "ts": time.time()})

    store.save(job)
    store.append_history(
        {
            "timeline_id": job.job_id,
            "status": job.state,
            "sync_accuracy": job.sync.sync_accuracy,
            "track_count": len(job.tracks),
            "scene_count": job.sync.scene_count,
            "parent_generation_id": parent_generation_id,
            "snapshot": _snapshot(job),
        }
    )
    cache_set(job.job_id, job.summary())

    if enqueue:
        timeline_queue.enqueue(job)
        job.observability.queue_time_ms = round(timeline_queue.queue_wait_ms(job_id), 3)
        store.save(job)

    if auto_process:
        job = process_timeline_job(job_id) or job

    return job


def process_timeline_job(job_id: str) -> TimelineJob | None:
    job = store.get(job_id) or timeline_queue.get(job_id)
    if not job:
        return None

    t0 = start_timer()
    queue_ms = timeline_queue.queue_wait_ms(job_id)
    job.observability.queue_time_ms = max(job.observability.queue_time_ms, queue_ms)

    try:
        timeline_queue.update_state(job_id, "preparing")
        job.state = "preparing"
        job.history.append({"status": "preparing", "ts": time.time()})
        store.save(job)

        timeline_queue.update_state(job_id, "synchronizing")
        job.state = "synchronizing"
        job.history.append({"status": "synchronizing", "ts": time.time()})
        scenes = job.metadata.get("scenes") or []
        shots = job.metadata.get("shots") or []
        beat_markers, sync = run_synchronization(
            job.tracks,
            fps=job.fps,
            duration_sec=job.duration_sec,
            scenes=scenes if isinstance(scenes, list) else [],
            shots=shots if isinstance(shots, list) else [],
            lip_sync=job.metadata.get("lip_sync")
            if isinstance(job.metadata.get("lip_sync"), dict)
            else None,
            camera_plan=job.metadata.get("camera_plan")
            if isinstance(job.metadata.get("camera_plan"), dict)
            else None,
            bpm=float(job.metadata.get("bpm") or 96.0),
            snap_enabled=job.snap_enabled,
            auto_align=job.auto_align,
        )
        job.beat_markers = beat_markers
        job.sync = sync
        job.observability.sync_accuracy = sync.sync_accuracy
        job.observability.track_count = len(job.tracks)
        job.observability.scene_count = sync.scene_count
        store.save(job)

        timeline_queue.update_state(job_id, "optimizing")
        job.state = "optimizing"
        job.history.append({"status": "optimizing", "ts": time.time()})
        store.save(job)

        timeline_queue.update_state(job_id, "rendering")
        job.state = "rendering"
        job.history.append({"status": "rendering", "ts": time.time()})
        job.export_url = f"/media/timeline/{job.job_id}/master.json"
        job.master_timeline_url = f"/media/timeline/{job.job_id}/master.timeline"
        job.production_ready = sync.sync_accuracy >= 0.75
        job.timeline_version += 1
        job.versions.append(
            TimelineVersion(
                version=job.timeline_version,
                label="synced",
                snapshot=_snapshot(job),
                created_at=time.time(),
            )
        )
        store.save(job)

        timeline_queue.update_state(job_id, "completed")
        job.state = "completed"
        job.history.append(
            {"status": "completed", "snapshot": _snapshot(job), "ts": time.time()}
        )
        job.observability.processing_time_ms += elapsed_ms(t0)
        job.observability.log_events.append(
            log_timeline_event(
                "timeline_completed",
                timeline_id=job.job_id,
                sync_accuracy=job.sync.sync_accuracy,
                processing_time_ms=job.observability.processing_time_ms,
            )
        )
        store.save(job)
        store.append_history(
            {
                "timeline_id": job.job_id,
                "status": "completed",
                "sync_accuracy": job.sync.sync_accuracy,
                "track_count": len(job.tracks),
                "scene_count": job.sync.scene_count,
                "parent_generation_id": job.parent_generation_id,
                "snapshot": _snapshot(job),
            }
        )
        cache_set(job.job_id, job.summary())
        return job
    except Exception as exc:  # noqa: BLE001
        timeline_queue.update_state(job_id, "failed", error=str(exc))
        job.state = "failed"
        job.observability.errors.append(str(exc))
        job.history.append({"status": "failed", "error": str(exc), "ts": time.time()})
        store.save(job)
        return job


def sync_timeline(
    job_id: str | None = None,
    *,
    create_if_missing: bool = True,
    **create_kwargs: Any,
) -> TimelineJob:
    if job_id:
        existing = store.get(job_id) or timeline_queue.get(job_id)
        if existing:
            if existing.locked:
                return existing
            # Force re-sync
            existing.state = "retrying"
            timeline_queue.retry(existing.job_id)
            processed = process_timeline_job(existing.job_id)
            return processed or existing
        if not create_if_missing:
            raise ValueError(f"timeline not found: {job_id}")
    return create_timeline(**create_kwargs)


def export_timeline(job_id: str) -> dict[str, Any]:
    job = store.get(job_id) or timeline_queue.get(job_id)
    if not job:
        raise ValueError(f"timeline not found: {job_id}")
    if job.state != "completed":
        process_timeline_job(job_id)
        job = store.get(job_id) or job
    payload = build_export_payload(job)
    store.append_history(
        {
            "timeline_id": job.job_id,
            "status": "exported",
            "sync_accuracy": job.sync.sync_accuracy,
            "track_count": len(job.tracks),
            "scene_count": job.sync.scene_count,
            "parent_generation_id": job.parent_generation_id,
            "snapshot": _snapshot(job),
        }
    )
    return payload


def get_job(job_id: str) -> TimelineJob | None:
    return store.get(job_id) or timeline_queue.get(job_id)


def create_timeline_dict(**kwargs: Any) -> dict[str, Any]:
    return create_timeline(**kwargs).to_dict()


def sync_timeline_dict(**kwargs: Any) -> dict[str, Any]:
    return sync_timeline(**kwargs).to_dict()


def history_payload(
    *,
    limit: int = 50,
    parent_generation_id: str | None = None,
) -> dict[str, Any]:
    return {
        "items": store.history(limit=limit, parent_generation_id=parent_generation_id),
        "queue": timeline_queue.status(),
        "engine": ENGINE_LABEL,
    }
