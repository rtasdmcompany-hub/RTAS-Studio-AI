"""Emotion Intelligence Engine — analyze, generate, process queue."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from app.services.emotion_intelligence import memory, store
from app.services.emotion_intelligence.analysis import analyze_scene
from app.services.emotion_intelligence.bridge import build_integrations
from app.services.emotion_intelligence.expressions import generate_facial_expression
from app.services.emotion_intelligence.library import list_emotion_library, resolve_emotion
from app.services.emotion_intelligence.models import (
    EmotionIntelligenceJob,
    EmotionObservability,
    EmotionProfile,
)
from app.services.emotion_intelligence.performance import generate_body_performance
from app.services.emotion_intelligence.queue import emotion_queue
from app.services.emotion_intelligence.timeline import build_emotion_timeline
from app.services.emotion_intelligence.validator import verify_consistency
from app.services.emotion_intelligence.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION


def _job_id(*parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).encode()).hexdigest()
    return f"emotion_{digest[:12]}"


def analyze_emotion(
    *,
    prompt: str,
    character_id: str | None = None,
    dialogue: str | None = None,
    story_context: str | None = None,
    emotion_hint: str | None = None,
    duration_sec: float | None = None,
    director_plan: dict[str, Any] | None = None,
    story_plan: dict[str, Any] | None = None,
    motion_plan: dict[str, Any] | None = None,
    camera_plan: dict[str, Any] | None = None,
    voice_plan: dict[str, Any] | None = None,
    audio_summary: dict[str, Any] | None = None,
    timeline_plan: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    text = (prompt or "").strip()
    if not text:
        raise ValueError("prompt is required")
    jid = _job_id(text[:80], character_id or "", str(time.time_ns()))
    analysis = analyze_scene(
        text,
        dialogue=dialogue,
        story_context=story_context,
        character_hint=character_id,
        emotion_hint=emotion_hint,
    )
    primary = analysis.character_emotion
    secondary = (
        analysis.scene_emotion if analysis.scene_emotion != primary else None
    )
    obs = EmotionObservability(
        emotion_job_id=jid,
        character_id=character_id,
        emotion_type=primary,
    )
    profile = EmotionProfile(
        character_id=character_id,
        primary_emotion=primary,
        secondary_emotion=secondary,
        intensity=analysis.performance_intensity,
        memory_key=memory.memory_key(character_id),
    )
    job = EmotionIntelligenceJob(
        job_id=jid,
        state="queued",
        prompt=text,
        character_id=character_id,
        analysis=analysis,
        profile=profile,
        observability=obs,
        duration_sec=float(duration_sec) if duration_sec and duration_sec > 0 else 4.0,
        metadata={
            **(metadata or {}),
            "engine_version": ENGINE_VERSION,
            "_plans": {
                "director_plan": director_plan,
                "story_plan": story_plan,
                "motion_plan": motion_plan,
                "camera_plan": camera_plan,
                "voice_plan": voice_plan,
                "audio_summary": audio_summary,
                "timeline_plan": timeline_plan,
                "dialogue": dialogue,
                "story_context": story_context,
            },
        },
    )
    job.integrations = build_integrations(
        job,
        director_plan=director_plan,
        story_plan=story_plan,
        motion_plan=motion_plan,
        camera_plan=camera_plan,
        voice_plan=voice_plan,
        audio_summary=audio_summary,
        timeline_plan=timeline_plan,
    )
    emotion_queue.enqueue(job)
    store.save(job)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        "operation": "analyze",
        **job.to_dict(),
        "queue": emotion_queue.status(),
    }


def process_emotion_job(job_id: str) -> EmotionIntelligenceJob | None:
    job = emotion_queue.get(job_id) or store.get(job_id)
    if not job:
        return None
    t0 = time.perf_counter()
    queue_ms = emotion_queue.queue_wait_ms(job_id)
    try:
        emotion_queue.update_state(job_id, "preparing")
        emotion_queue.update_state(job_id, "emotion_analysis")
        job = store.get(job_id) or emotion_queue.get(job_id) or job
        if not job.analysis:
            job.analysis = analyze_scene(job.prompt, emotion_hint=None)

        emotion_queue.update_state(job_id, "expression_generation")
        primary = job.profile.primary_emotion if job.profile else job.analysis.character_emotion
        intensity = job.profile.intensity if job.profile else job.analysis.performance_intensity
        expression = generate_facial_expression(primary, intensity=intensity)
        job.expression = expression

        emotion_queue.update_state(job_id, "performance_optimization")
        job.performance = generate_body_performance(primary, intensity=intensity)
        secondary = job.profile.secondary_emotion if job.profile else None
        job.timeline = build_emotion_timeline(
            job_id=job.job_id,
            primary=primary,
            secondary=secondary,
            duration_sec=job.duration_sec,
            intensity=intensity,
        )

        prior = memory.last_emotion(job.character_id)
        face_ref = None
        try:
            from app.services.face_lock import get_identity

            if job.character_id:
                ident = get_identity(job.character_id)
                face_ref = ident.get("face_embedding_ref") if ident else None
        except Exception:
            face_ref = None
        if job.profile:
            job.profile.face_embedding_ref = face_ref

        job.consistency = verify_consistency(
            character_id=job.character_id,
            expression=expression,
            face_embedding_ref=face_ref,
            prior_emotion=prior,
        )
        plans = (job.metadata or {}).get("_plans") or {}
        job.integrations = build_integrations(
            job,
            director_plan=plans.get("director_plan"),
            story_plan=plans.get("story_plan"),
            motion_plan=plans.get("motion_plan"),
            camera_plan=plans.get("camera_plan"),
            voice_plan=plans.get("voice_plan"),
            audio_summary=plans.get("audio_summary"),
            timeline_plan=plans.get("timeline_plan"),
        )
        memory.remember(
            job.character_id,
            emotion=primary,
            intensity=intensity,
            expression_score=expression.expression_score,
            job_id=job.job_id,
        )
        elapsed = round((time.perf_counter() - t0) * 1000.0, 3)
        if job.observability:
            job.observability.emotion_type = primary
            job.observability.expression_score = expression.expression_score
            job.observability.processing_time_ms = elapsed
            job.observability.queue_time_ms = queue_ms
            job.observability.retry_count = job.retry_count
        job.production_ready = bool(job.consistency and job.consistency.consistent)
        job.version += 1
        job.state = "completed"
        emotion_queue.update_state(job_id, "completed")
        store.save(job)
        return job
    except Exception as exc:
        emotion_queue.update_state(job_id, "failed", error=str(exc))
        job = store.get(job_id) or emotion_queue.get(job_id) or job
        job.state = "failed"
        job.error = str(exc)
        store.save(job)
        return job


def generate_emotion(
    *,
    job_id: str | None = None,
    prompt: str | None = None,
    character_id: str | None = None,
    emotion_hint: str | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    if job_id:
        job = store.get(job_id) or emotion_queue.get(job_id)
        if not job:
            raise ValueError(f"Emotion job not found: {job_id}")
        if emotion_hint and job.profile:
            job.profile.primary_emotion = resolve_emotion(emotion_hint)
            store.save(job)
    else:
        if not prompt:
            raise ValueError("prompt is required when job_id is not provided")
        created = analyze_emotion(
            prompt=prompt,
            character_id=character_id,
            emotion_hint=emotion_hint,
            **kwargs,
        )
        job_id = created["job_id"]
    processed = process_emotion_job(job_id)
    if not processed:
        raise ValueError(f"Failed to process emotion job: {job_id}")
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        "operation": "generate",
        **processed.to_dict(),
        "queue": emotion_queue.status(),
    }


def get_emotion(job_id: str) -> dict[str, Any] | None:
    job = store.get(job_id) or emotion_queue.get(job_id)
    if not job:
        return None
    return {"engine": ENGINE_NAME, "version": ENGINE_VERSION, **job.to_dict()}


def emotion_history(limit: int = 50) -> dict[str, Any]:
    jobs = store.history(limit=limit)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "jobs": [j.summary() for j in jobs],
        "count": len(jobs),
        "queue": emotion_queue.status(),
    }


def emotion_library_payload() -> dict[str, Any]:
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        **list_emotion_library(),
    }


def analyze_dict(**kwargs: Any) -> dict[str, Any]:
    return analyze_emotion(**kwargs)


def generate_dict(**kwargs: Any) -> dict[str, Any]:
    return generate_emotion(**kwargs)
