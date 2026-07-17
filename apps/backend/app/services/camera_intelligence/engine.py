"""Camera Intelligence Engine — plan, generate, process queue."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from app.services.camera_intelligence import store
from app.services.camera_intelligence.bridge import build_integrations
from app.services.camera_intelligence.library import get_preset, list_camera_library, resolve_shot
from app.services.camera_intelligence.models import (
    CameraIntelligenceJob,
    CameraObservability,
    CameraTimelineEvent,
)
from app.services.camera_intelligence.planning import (
    analyze_scene,
    build_shot,
    recommend_shot_sequence,
    scene_coverage,
)
from app.services.camera_intelligence.queue import camera_queue
from app.services.camera_intelligence.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION


def _job_id(*parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).encode()).hexdigest()
    return f"camintel_{digest[:12]}"


def plan_camera(
    *,
    prompt: str,
    scene_id: str | None = None,
    character_ids: list[str] | None = None,
    emotion: str | None = None,
    environment: str | None = None,
    shot_types: list[str] | None = None,
    preset: str | None = None,
    max_shots: int = 4,
    duration_sec: float | None = None,
    director_plan: dict[str, Any] | None = None,
    story_plan: dict[str, Any] | None = None,
    scene_plan: dict[str, Any] | None = None,
    character_dna: dict[str, Any] | None = None,
    motion_plan: dict[str, Any] | None = None,
    timeline_plan: dict[str, Any] | None = None,
    audio_summary: dict[str, Any] | None = None,
    export_plan: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    text = (prompt or "").strip()
    if not text:
        raise ValueError("prompt is required")
    chars = [c for c in (character_ids or []) if c]
    jid = _job_id(text[:80], scene_id or "", ",".join(chars), str(time.time_ns()))
    analysis = analyze_scene(text, character_ids=chars, emotion=emotion, environment=environment)

    preset_data = get_preset(preset)
    if shot_types:
        sequence = [resolve_shot(s) for s in shot_types]
    elif preset_data:
        sequence = [resolve_shot(s) for s in preset_data.get("shots") or []]
    else:
        sequence = recommend_shot_sequence(analysis, max_shots=max_shots)

    obs = CameraObservability(camera_job_id=jid, scene_id=scene_id)
    job = CameraIntelligenceJob(
        job_id=jid,
        state="queued",
        prompt=text,
        scene_id=scene_id,
        character_ids=chars,
        analysis=analysis,
        observability=obs,
        metadata={
            **(metadata or {}),
            "engine_version": ENGINE_VERSION,
            "requested_shots": sequence,
            "preset": preset,
            "_plans": {
                "director_plan": director_plan,
                "story_plan": story_plan,
                "scene_plan": scene_plan,
                "character_dna": character_dna,
                "motion_plan": motion_plan,
                "timeline_plan": timeline_plan,
                "audio_summary": audio_summary,
                "export_plan": export_plan,
            },
        },
    )
    if duration_sec and duration_sec > 0:
        job.duration_sec = float(duration_sec)
    job.integrations = build_integrations(
        job,
        director_plan=director_plan,
        story_plan=story_plan,
        scene_plan=scene_plan,
        character_dna=character_dna,
        motion_plan=motion_plan,
        timeline_plan=timeline_plan,
        audio_summary=audio_summary,
        export_plan=export_plan,
    )
    camera_queue.enqueue(job)
    store.save(job)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        "operation": "plan",
        **job.to_dict(),
        "queue": camera_queue.status(),
        "planned_shots": sequence,
    }


def process_camera_job(job_id: str) -> CameraIntelligenceJob | None:
    job = camera_queue.get(job_id) or store.get(job_id)
    if not job:
        return None
    t0 = time.perf_counter()
    queue_ms = camera_queue.queue_wait_ms(job_id)
    try:
        camera_queue.update_state(job_id, "preparing")
        camera_queue.update_state(job_id, "planning")
        camera_queue.update_state(job_id, "camera_analysis")
        job = store.get(job_id) or camera_queue.get(job_id) or job
        if not job.analysis:
            job.analysis = analyze_scene(job.prompt, character_ids=job.character_ids)

        camera_queue.update_state(job_id, "shot_generation")
        sequence = list((job.metadata or {}).get("requested_shots") or recommend_shot_sequence(job.analysis))
        n = max(1, len(sequence))
        total = job.duration_sec if job.duration_sec > 0 else None
        per = (total / n) if total else None
        shots = []
        timeline = []
        cursor = 0.0
        for i, st in enumerate(sequence):
            shot = build_shot(st, job.analysis, job_id=job.job_id, index=i, start_sec=cursor, duration_sec=per)
            shots.append(shot)
            timeline.append(
                CameraTimelineEvent(
                    event_id=f"evt_{shot.shot_id}",
                    start_sec=shot.start_sec,
                    end_sec=shot.end_sec,
                    shot_id=shot.shot_id,
                    shot_type=shot.shot_type,
                )
            )
            cursor = shot.end_sec

        job.shots = shots
        job.timeline = timeline
        job.duration_sec = round(cursor, 3)
        job.coverage = scene_coverage(shots, job.analysis)
        plans = (job.metadata or {}).get("_plans") or {}
        job.integrations = build_integrations(
            job,
            director_plan=plans.get("director_plan"),
            story_plan=plans.get("story_plan"),
            scene_plan=plans.get("scene_plan"),
            character_dna=plans.get("character_dna"),
            motion_plan=plans.get("motion_plan"),
            timeline_plan=plans.get("timeline_plan"),
            audio_summary=plans.get("audio_summary"),
            export_plan=plans.get("export_plan"),
        )
        elapsed = round((time.perf_counter() - t0) * 1000.0, 3)
        if job.observability:
            job.observability.processing_time_ms = elapsed
            job.observability.queue_time_ms = queue_ms
            job.observability.retry_count = job.retry_count
            job.observability.shot_type = shots[0].shot_type if shots else None
            job.observability.lens_used = shots[0].lens.lens_id if shots else None
            job.observability.scene_id = job.scene_id
        job.production_ready = bool(job.coverage.get("complete"))
        job.version += 1
        job.state = "completed"
        camera_queue.update_state(job_id, "completed")
        store.save(job)
        return job
    except Exception as exc:
        camera_queue.update_state(job_id, "failed", error=str(exc))
        job = store.get(job_id) or camera_queue.get(job_id) or job
        job.state = "failed"
        job.error = str(exc)
        store.save(job)
        return job


def generate_camera(
    *,
    job_id: str | None = None,
    prompt: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    if job_id:
        job = store.get(job_id) or camera_queue.get(job_id)
        if not job:
            raise ValueError(f"Camera job not found: {job_id}")
    else:
        if not prompt:
            raise ValueError("prompt is required when job_id is not provided")
        planned = plan_camera(prompt=prompt, **kwargs)
        job_id = planned["job_id"]
    processed = process_camera_job(job_id)
    if not processed:
        raise ValueError(f"Failed to process camera job: {job_id}")
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        "operation": "generate",
        **processed.to_dict(),
        "queue": camera_queue.status(),
    }


def get_camera(job_id: str) -> dict[str, Any] | None:
    job = store.get(job_id) or camera_queue.get(job_id)
    if not job:
        return None
    return {"engine": ENGINE_NAME, "version": ENGINE_VERSION, **job.to_dict()}


def camera_history(limit: int = 50) -> dict[str, Any]:
    jobs = store.history(limit=limit)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "jobs": [j.summary() for j in jobs],
        "count": len(jobs),
        "queue": camera_queue.status(),
    }


def camera_library_payload() -> dict[str, Any]:
    return {"engine": ENGINE_NAME, "version": ENGINE_VERSION, **list_camera_library()}


def plan_dict(**kwargs: Any) -> dict[str, Any]:
    return plan_camera(**kwargs)


def generate_dict(**kwargs: Any) -> dict[str, Any]:
    return generate_camera(**kwargs)
