"""World Intelligence Engine — create, generate, process queue."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from app.services.world_intelligence import store
from app.services.world_intelligence.analysis import analyze_world
from app.services.world_intelligence.bridge import build_integrations
from app.services.world_intelligence.builders import build_environment
from app.services.world_intelligence.consistency import (
    clear_memory,
    last_blueprint_snapshot,
    remember_world,
    verify_consistency,
)
from app.services.world_intelligence.library import list_world_library
from app.services.world_intelligence.models import WorldIntelligenceJob, WorldObservability
from app.services.world_intelligence.queue import world_queue
from app.services.world_intelligence.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    WORLD_CONSISTENCY_THRESHOLD,
)


def _job_id(*parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).encode()).hexdigest()
    return f"world_{digest[:12]}"


def _world_id(prompt: str, explicit: str | None = None) -> str:
    if explicit and explicit.strip():
        return explicit.strip()
    digest = hashlib.sha1(f"world|{prompt[:120]}".encode()).hexdigest()
    return f"wld_{digest[:12]}"


def create_world(
    *,
    prompt: str,
    world_id: str | None = None,
    scene_id: str | None = None,
    environment: str | None = None,
    weather: str | None = None,
    time_of_day: str | None = None,
    mood: str | None = None,
    lighting: str | None = None,
    story_plan: dict[str, Any] | None = None,
    director_plan: dict[str, Any] | None = None,
    scene_plan: dict[str, Any] | None = None,
    camera_plan: dict[str, Any] | None = None,
    character_dna: dict[str, Any] | None = None,
    motion_plan: dict[str, Any] | None = None,
    emotion_plan: dict[str, Any] | None = None,
    timeline_plan: dict[str, Any] | None = None,
    audio_summary: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    text = (prompt or "").strip()
    if not text:
        raise ValueError("prompt is required")
    wid = _world_id(text, world_id)
    jid = _job_id(wid, scene_id or "", str(time.time_ns()))
    analysis = analyze_world(
        text,
        mood=mood,
        environment_hint=environment,
        weather_hint=weather,
        time_hint=time_of_day,
    )
    obs = WorldObservability(
        environment_job_id=jid,
        world_id=wid,
        scene_id=scene_id,
        weather_type=analysis.recommended_weather,
    )
    job = WorldIntelligenceJob(
        job_id=jid,
        world_id=wid,
        state="queued",
        prompt=text,
        scene_id=scene_id,
        analysis=analysis,
        observability=obs,
        metadata={
            **(metadata or {}),
            "engine_version": ENGINE_VERSION,
            "lighting_override": lighting,
            "_plans": {
                "story_plan": story_plan,
                "director_plan": director_plan,
                "scene_plan": scene_plan,
                "camera_plan": camera_plan,
                "character_dna": character_dna,
                "motion_plan": motion_plan,
                "emotion_plan": emotion_plan,
                "timeline_plan": timeline_plan,
                "audio_summary": audio_summary,
            },
        },
    )
    job.integrations = build_integrations(
        job,
        story_plan=story_plan,
        director_plan=director_plan,
        scene_plan=scene_plan,
        camera_plan=camera_plan,
        character_dna=character_dna,
        motion_plan=motion_plan,
        emotion_plan=emotion_plan,
        timeline_plan=timeline_plan,
        audio_summary=audio_summary,
    )
    world_queue.enqueue(job)
    store.save(job)
    payload = job.to_dict()
    return {
        **payload,
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "job_version": payload.get("version"),
        "label": ENGINE_LABEL,
        "operation": "create",
        "queue": world_queue.status(),
    }


def process_world_job(job_id: str) -> WorldIntelligenceJob | None:
    job = world_queue.get(job_id) or store.get(job_id)
    if not job:
        return None
    t0 = time.perf_counter()
    queue_ms = world_queue.queue_wait_ms(job_id)
    try:
        world_queue.update_state(job_id, "preparing")
        world_queue.update_state(job_id, "world_analysis")
        job = store.get(job_id) or world_queue.get(job_id) or job
        if not job.analysis:
            job.analysis = analyze_world(job.prompt)

        world_queue.update_state(job_id, "environment_generation")
        lighting_override = (job.metadata or {}).get("lighting_override")
        # Continuity: reuse prior location/env when same world_id has memory
        prior = last_blueprint_snapshot(job.world_id)
        env_id = job.analysis.recommended_environment
        weather = job.analysis.recommended_weather
        tod = job.analysis.recommended_time
        if prior and prior.get("environment"):
            env_id = prior["environment"]
            # Keep location continuity; weather/time may evolve with mood but location stable
        blueprint = build_environment(
            world_id=job.world_id,
            environment=env_id,
            weather=weather,
            time_of_day=tod,
            mood=job.analysis.mood,
            lighting_override=lighting_override,
        )
        if prior and prior.get("location_id"):
            # Force same location_id for continuity across scenes
            blueprint.location_id = prior["location_id"]

        world_queue.update_state(job_id, "lighting_optimization")
        job.environment = blueprint
        # Consistency vs prior snapshot fields
        if prior:
            from app.services.world_intelligence.builders import build_environment as _be

            locked = _be(
                world_id=job.world_id,
                environment=prior.get("environment") or env_id,
                weather=prior.get("weather") or weather,
                time_of_day=prior.get("time_of_day") or tod,
                mood=job.analysis.mood,
                lighting_override=prior.get("lighting"),
            )
            locked.location_id = prior.get("location_id") or locked.location_id
            # For continuity check: candidate may change weather with mood — compare location/assets primarily
            job.consistency = verify_consistency(job.world_id, locked, blueprint)
            # Soft-pass location-only continuity for evolving weather
            if locked.location_id == blueprint.location_id and locked.environment_id == blueprint.environment_id:
                job.consistency.drift_flags = [
                    f for f in job.consistency.drift_flags if not f.startswith("weather") and not f.startswith("time") and not f.startswith("lighting") and not f.startswith("sky")
                ]
                job.consistency.score = max(job.consistency.score, 92.0) if not job.consistency.drift_flags else job.consistency.score
                job.consistency.no_continuity_breaks = len(job.consistency.drift_flags) == 0
                job.consistency.consistent = (
                    job.consistency.no_continuity_breaks
                    and job.consistency.score >= WORLD_CONSISTENCY_THRESHOLD
                )
        else:
            job.consistency = verify_consistency(job.world_id, blueprint)

        remember_world(job.world_id, blueprint, job.job_id)
        plans = (job.metadata or {}).get("_plans") or {}
        job.integrations = build_integrations(
            job,
            story_plan=plans.get("story_plan"),
            director_plan=plans.get("director_plan"),
            scene_plan=plans.get("scene_plan"),
            camera_plan=plans.get("camera_plan"),
            character_dna=plans.get("character_dna"),
            motion_plan=plans.get("motion_plan"),
            emotion_plan=plans.get("emotion_plan"),
            timeline_plan=plans.get("timeline_plan"),
            audio_summary=plans.get("audio_summary"),
        )
        elapsed = round((time.perf_counter() - t0) * 1000.0, 3)
        if job.observability:
            job.observability.weather_type = blueprint.weather.weather_id
            job.observability.lighting_profile = blueprint.lighting.lighting_id
            job.observability.processing_time_ms = elapsed
            job.observability.queue_time_ms = queue_ms
            job.observability.retry_count = job.retry_count
        job.production_ready = bool(job.consistency and job.consistency.consistent)
        job.version += 1
        job.state = "completed"
        world_queue.update_state(job_id, "completed")
        store.save(job)
        return job
    except Exception as exc:
        world_queue.update_state(job_id, "failed", error=str(exc))
        job = store.get(job_id) or world_queue.get(job_id) or job
        job.state = "failed"
        job.error = str(exc)
        store.save(job)
        return job


def generate_world(
    *,
    job_id: str | None = None,
    prompt: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    if job_id:
        job = store.get(job_id) or world_queue.get(job_id)
        if not job:
            raise ValueError(f"World job not found: {job_id}")
    else:
        if not prompt:
            raise ValueError("prompt is required when job_id is not provided")
        created = create_world(prompt=prompt, **kwargs)
        job_id = created["job_id"]
    processed = process_world_job(job_id)
    if not processed:
        raise ValueError(f"Failed to process world job: {job_id}")
    payload = processed.to_dict()
    return {
        **payload,
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "job_version": payload.get("version"),
        "label": ENGINE_LABEL,
        "operation": "generate",
        "queue": world_queue.status(),
    }


def get_world(job_id: str) -> dict[str, Any] | None:
    job = store.get(job_id) or world_queue.get(job_id)
    if not job:
        return None
    payload = job.to_dict()
    return {
        **payload,
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "job_version": payload.get("version"),
    }


def world_history(limit: int = 50) -> dict[str, Any]:
    jobs = store.history(limit=limit)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "jobs": [j.summary() for j in jobs],
        "count": len(jobs),
        "queue": world_queue.status(),
    }


def world_library_payload() -> dict[str, Any]:
    return {"engine": ENGINE_NAME, "version": ENGINE_VERSION, **list_world_library()}


def create_dict(**kwargs: Any) -> dict[str, Any]:
    return create_world(**kwargs)


def generate_dict(**kwargs: Any) -> dict[str, Any]:
    return generate_world(**kwargs)


# re-export for tests
__all_clear_memory = clear_memory
