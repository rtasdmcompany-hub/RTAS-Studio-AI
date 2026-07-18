"""Director Intelligence Engine — plan, generate, process queue."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from app.services.director_intelligence import store
from app.services.director_intelligence.analysis import analyze_story
from app.services.director_intelligence.bridge import build_integrations
from app.services.director_intelligence.memory import clear as clear_memory
from app.services.director_intelligence.memory import last_plan, remember_plan
from app.services.director_intelligence.models import DirectorIntelligenceJob, DirectorObservability
from app.services.director_intelligence.planner import build_production_plan
from app.services.director_intelligence.queue import director_queue
from app.services.director_intelligence.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PLANNING_ACCURACY_THRESHOLD,
)


def _job_id(*parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).encode()).hexdigest()
    return f"dir_{digest[:12]}"


def _project_id(prompt: str, explicit: str | None = None) -> str:
    if explicit and explicit.strip():
        return explicit.strip()
    digest = hashlib.sha1(f"proj|{prompt[:120]}".encode()).hexdigest()
    return f"proj_{digest[:12]}"


def plan_director(
    *,
    prompt: str,
    project_id: str | None = None,
    format_type: str | None = None,
    genre: str | None = None,
    runtime_sec: float | None = None,
    audience: str | None = None,
    characters: list[str] | None = None,
    ai_brain: dict[str, Any] | None = None,
    story_plan: dict[str, Any] | None = None,
    character_dna: dict[str, Any] | None = None,
    motion_plan: dict[str, Any] | None = None,
    camera_plan: dict[str, Any] | None = None,
    emotion_plan: dict[str, Any] | None = None,
    world_plan: dict[str, Any] | None = None,
    audio_summary: dict[str, Any] | None = None,
    timeline_plan: dict[str, Any] | None = None,
    export_plan: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    text = (prompt or "").strip()
    if not text:
        raise ValueError("prompt is required")
    pid = _project_id(text, project_id)
    jid = _job_id(pid, str(time.time_ns()))
    analysis = analyze_story(
        text,
        format_hint=format_type,
        genre_hint=genre,
        runtime_hint=runtime_sec,
        audience_hint=audience,
    )
    obs = DirectorObservability(director_job_id=jid, project_id=pid)
    job = DirectorIntelligenceJob(
        job_id=jid,
        project_id=pid,
        state="queued",
        prompt=text,
        analysis=analysis,
        observability=obs,
        metadata={
            **(metadata or {}),
            "engine_version": ENGINE_VERSION,
            "characters": list(characters or []),
            "_plans": {
                "ai_brain": ai_brain,
                "story_plan": story_plan,
                "character_dna": character_dna,
                "motion_plan": motion_plan,
                "camera_plan": camera_plan,
                "emotion_plan": emotion_plan,
                "world_plan": world_plan,
                "audio_summary": audio_summary,
                "timeline_plan": timeline_plan,
                "export_plan": export_plan,
            },
        },
    )
    job.integrations = build_integrations(
        job,
        ai_brain=ai_brain,
        story_plan=story_plan,
        character_dna=character_dna,
        motion_plan=motion_plan,
        camera_plan=camera_plan,
        emotion_plan=emotion_plan,
        world_plan=world_plan,
        audio_summary=audio_summary,
        timeline_plan=timeline_plan,
        export_plan=export_plan,
    )
    director_queue.enqueue(job)
    store.save(job)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        "operation": "plan",
        **job.to_dict(),
        "queue": director_queue.status(),
    }


def process_director_job(job_id: str) -> DirectorIntelligenceJob | None:
    job = director_queue.get(job_id) or store.get(job_id)
    if not job:
        return None
    t0 = time.perf_counter()
    queue_ms = director_queue.queue_wait_ms(job_id)
    try:
        director_queue.update_state(job_id, "preparing")
        director_queue.update_state(job_id, "story_analysis")
        job = store.get(job_id) or director_queue.get(job_id) or job
        if not job.analysis:
            job.analysis = analyze_story(job.prompt)

        # Continuity: prefer prior format/structure if same project
        prior = last_plan(job.project_id)
        if prior and prior.get("format_type") and not (job.metadata or {}).get("format_override"):
            # keep analysis format aligned with memory when present
            if job.analysis.format_type != prior["format_type"]:
                job.analysis.notes.append(f"memory_format={prior['format_type']}")

        director_queue.update_state(job_id, "production_planning")
        characters = list((job.metadata or {}).get("characters") or [])
        plan = build_production_plan(
            project_id=job.project_id,
            prompt=job.prompt,
            analysis=job.analysis,
            characters=characters or None,
        )

        director_queue.update_state(job_id, "scene_directing")
        job.production_plan = plan
        job.accuracy_score = plan.accuracy_score
        job.production_ready = plan.accuracy_score >= PLANNING_ACCURACY_THRESHOLD

        plans = (job.metadata or {}).get("_plans") or {}
        job.integrations = build_integrations(
            job,
            ai_brain=plans.get("ai_brain"),
            story_plan=plans.get("story_plan"),
            character_dna=plans.get("character_dna"),
            motion_plan=plans.get("motion_plan"),
            camera_plan=plans.get("camera_plan"),
            emotion_plan=plans.get("emotion_plan"),
            world_plan=plans.get("world_plan"),
            audio_summary=plans.get("audio_summary"),
            timeline_plan=plans.get("timeline_plan"),
            export_plan=plans.get("export_plan"),
        )
        remember_plan(job.project_id, plan.to_dict(), job.job_id)

        elapsed = round((time.perf_counter() - t0) * 1000.0, 3)
        if job.observability:
            job.observability.scene_count = len(plan.scenes)
            job.observability.shot_count = plan.shot_count
            job.observability.runtime_sec = plan.total_runtime_sec
            job.observability.processing_time_ms = elapsed
            job.observability.queue_time_ms = queue_ms
            job.observability.retry_count = job.retry_count
        job.version += 1
        job.state = "completed"
        director_queue.update_state(job_id, "completed")
        store.save(job)
        return job
    except Exception as exc:
        director_queue.update_state(job_id, "failed", error=str(exc))
        job = store.get(job_id) or director_queue.get(job_id) or job
        job.state = "failed"
        job.error = str(exc)
        store.save(job)
        return job


def generate_director(
    *,
    job_id: str | None = None,
    prompt: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    if job_id:
        job = store.get(job_id) or director_queue.get(job_id)
        if not job:
            raise ValueError(f"Director job not found: {job_id}")
    else:
        if not prompt:
            raise ValueError("prompt is required when job_id is not provided")
        created = plan_director(prompt=prompt, **kwargs)
        job_id = created["job_id"]
    processed = process_director_job(job_id)
    if not processed:
        raise ValueError(f"Failed to process director job: {job_id}")
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        "operation": "generate",
        **processed.to_dict(),
        "queue": director_queue.status(),
    }


def get_director(job_id: str) -> dict[str, Any] | None:
    job = store.get(job_id) or director_queue.get(job_id)
    if not job:
        return None
    return {"engine": ENGINE_NAME, "version": ENGINE_VERSION, **job.to_dict()}


def director_history(limit: int = 50) -> dict[str, Any]:
    jobs = store.history(limit=limit)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "jobs": [j.summary() for j in jobs],
        "count": len(jobs),
        "queue": director_queue.status(),
    }


def director_report(limit: int = 50) -> dict[str, Any]:
    jobs = [j for j in store.history(limit=limit) if j.state == "completed" and j.production_plan]
    if not jobs:
        return {
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "jobs_analyzed": 0,
            "avg_accuracy": 0.0,
            "avg_runtime_sec": 0.0,
            "avg_scene_count": 0.0,
            "avg_shot_count": 0.0,
            "threshold": PLANNING_ACCURACY_THRESHOLD,
            "pass_rate": 0.0,
        }
    accuracies = [j.accuracy_score for j in jobs]
    runtimes = [j.production_plan.total_runtime_sec for j in jobs if j.production_plan]
    scenes = [len(j.production_plan.scenes) for j in jobs if j.production_plan]
    shots = [j.production_plan.shot_count for j in jobs if j.production_plan]
    passed = sum(1 for a in accuracies if a >= PLANNING_ACCURACY_THRESHOLD)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "jobs_analyzed": len(jobs),
        "avg_accuracy": round(sum(accuracies) / len(accuracies), 2),
        "avg_runtime_sec": round(sum(runtimes) / len(runtimes), 2) if runtimes else 0.0,
        "avg_scene_count": round(sum(scenes) / len(scenes), 2) if scenes else 0.0,
        "avg_shot_count": round(sum(shots) / len(shots), 2) if shots else 0.0,
        "threshold": PLANNING_ACCURACY_THRESHOLD,
        "pass_rate": round(100.0 * passed / len(jobs), 2),
        "queue": director_queue.status(),
    }


def plan_dict(**kwargs: Any) -> dict[str, Any]:
    return plan_director(**kwargs)


def generate_dict(**kwargs: Any) -> dict[str, Any]:
    return generate_director(**kwargs)


__all__ = [
    "plan_director",
    "generate_director",
    "process_director_job",
    "get_director",
    "director_history",
    "director_report",
    "plan_dict",
    "generate_dict",
    "clear_memory",
]
