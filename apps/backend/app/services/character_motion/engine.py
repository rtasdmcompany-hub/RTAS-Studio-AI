"""Character Motion Engine — create, generate, process queue."""

from __future__ import annotations

import hashlib
import time
from typing import Any

from app.services.character_motion import store
from app.services.character_motion.bridge import build_integrations
from app.services.character_motion.emotion import emotion_movement_bias, resolve_emotion
from app.services.character_motion.engines import (
    build_pose_sequence,
    eye_movement_engine,
    facial_expression_engine,
    hand_gesture_engine,
    head_movement_engine,
    running_engine,
    sitting_engine,
    standing_engine,
    walking_engine,
)
from app.services.character_motion.library import get_action_spec, list_motion_library, resolve_action
from app.services.character_motion.models import (
    CharacterMotionJob,
    MotionClip,
    MotionObservability,
    MotionTimelineEvent,
)
from app.services.character_motion.profile import build_motion_profile, validate_body_consistency
from app.services.character_motion.queue import motion_queue
from app.services.character_motion.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION


def _job_id(*parts: str) -> str:
    digest = hashlib.sha1("|".join(parts).encode()).hexdigest()
    return f"cmotion_{digest[:12]}"


def _clip_id(job_id: str, action: str, idx: int) -> str:
    digest = hashlib.sha1(f"{job_id}|{action}|{idx}".encode()).hexdigest()
    return f"clip_{digest[:10]}"


def _normalize_actions(actions: list[str] | None, action: str | None) -> list[str]:
    raw = list(actions or [])
    if action:
        raw.append(action)
    if not raw:
        raw = ["standing"]
    out: list[str] = []
    seen: set[str] = set()
    for a in raw:
        key = resolve_action(a)
        if key not in seen:
            seen.add(key)
            out.append(key)
    return out


def create_motion_job(
    *,
    character_id: str | None = None,
    actions: list[str] | None = None,
    action: str | None = None,
    emotion: str | None = None,
    duration_sec: float | None = None,
    profile_overrides: dict[str, Any] | None = None,
    director_plan: dict[str, Any] | None = None,
    scene_plan: dict[str, Any] | None = None,
    camera_plan: dict[str, Any] | None = None,
    timeline_plan: dict[str, Any] | None = None,
    audio_summary: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    resolved_actions = _normalize_actions(actions, action)
    emo = resolve_emotion(emotion)
    specs = [get_action_spec(a) for a in resolved_actions]
    default_dur = sum(float(s.get("default_duration") or 2.0) for s in specs)
    dur = float(duration_sec) if duration_sec and duration_sec > 0 else default_dur
    profile = build_motion_profile(character_id, overrides=profile_overrides)
    jid = _job_id(profile.character_id, ",".join(resolved_actions), emo, str(time.time_ns()))
    obs = MotionObservability(motion_job_id=jid, character_id=character_id)
    job = CharacterMotionJob(
        job_id=jid,
        state="queued",
        character_id=character_id or profile.character_id,
        profile=profile,
        actions=resolved_actions,
        emotion=emo,
        duration_sec=round(dur, 3),
        observability=obs,
        metadata={
            **(metadata or {}),
            "engine_version": ENGINE_VERSION,
            "integration_hints": {
                "director": bool(director_plan),
                "scene": bool(scene_plan),
                "camera": bool(camera_plan),
                "timeline": bool(timeline_plan),
                "audio": bool(audio_summary),
            },
        },
    )
    job.integrations = build_integrations(
        job,
        director_plan=director_plan,
        scene_plan=scene_plan,
        camera_plan=camera_plan,
        timeline_plan=timeline_plan,
        audio_summary=audio_summary,
    )
    # stash plans for generate
    job.metadata["_plans"] = {
        "director_plan": director_plan,
        "scene_plan": scene_plan,
        "camera_plan": camera_plan,
        "timeline_plan": timeline_plan,
        "audio_summary": audio_summary,
    }
    motion_queue.enqueue(job)
    store.save(job)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        "operation": "create",
        **job.to_dict(),
        "queue": motion_queue.status(),
    }


def _generate_clip(
    job: CharacterMotionJob,
    action: str,
    idx: int,
    slice_dur: float,
) -> MotionClip:
    assert job.profile is not None
    bias = emotion_movement_bias(job.emotion)
    poses = build_pose_sequence(action, slice_dur, bias)
    locomotion: dict[str, Any] = {}
    if action == "walking":
        locomotion = walking_engine(job.profile.walking_style, bias)
    elif action == "running":
        locomotion = running_engine(job.profile.running_style, bias)
    elif action == "sitting":
        locomotion = sitting_engine(bias)
    elif action in ("standing", "talking", "listening", "smiling", "custom"):
        locomotion = standing_engine(bias)
    elif action == "driving":
        locomotion = {**sitting_engine(bias), "activity": "driving"}
    else:
        locomotion = standing_engine(bias)

    return MotionClip(
        clip_id=_clip_id(job.job_id, action, idx),
        action=action,
        emotion=job.emotion,
        duration_sec=round(slice_dur, 3),
        poses=poses,
        hand_gestures=hand_gesture_engine(action, job.profile.gesture_style, bias),
        head_motion=head_movement_engine(job.profile.head_movement, action, bias),
        eye_motion=eye_movement_engine(job.profile.eye_contact, action, bias),
        facial_expression=facial_expression_engine(job.emotion, action),
        locomotion=locomotion,
        metadata={"body_fingerprint": job.profile.fingerprint(), "no_distortion": True},
    )


def process_motion_job(job_id: str) -> CharacterMotionJob | None:
    job = motion_queue.get(job_id) or store.get(job_id)
    if not job:
        return None
    t0 = time.perf_counter()
    queue_ms = motion_queue.queue_wait_ms(job_id)
    try:
        motion_queue.update_state(job_id, "preparing")
        motion_queue.update_state(job_id, "motion_planning")
        job = store.get(job_id) or motion_queue.get(job_id) or job
        if not job.profile:
            job.profile = build_motion_profile(job.character_id)

        motion_queue.update_state(job_id, "pose_generation")
        n = max(1, len(job.actions))
        slice_dur = job.duration_sec / n
        clips: list[MotionClip] = []
        timeline: list[MotionTimelineEvent] = []
        cursor = 0.0
        for i, action in enumerate(job.actions):
            clip = _generate_clip(job, action, i, slice_dur)
            clips.append(clip)
            timeline.append(
                MotionTimelineEvent(
                    event_id=f"evt_{clip.clip_id}",
                    start_sec=round(cursor, 3),
                    end_sec=round(cursor + slice_dur, 3),
                    action=action,
                    clip_id=clip.clip_id,
                    layer="body",
                )
            )
            cursor += slice_dur

        motion_queue.update_state(job_id, "animation")
        job.clips = clips
        job.timeline = timeline
        job.consistency = validate_body_consistency(job.profile)
        plans = (job.metadata or {}).get("_plans") or {}
        job.integrations = build_integrations(
            job,
            director_plan=plans.get("director_plan"),
            scene_plan=plans.get("scene_plan"),
            camera_plan=plans.get("camera_plan"),
            timeline_plan=plans.get("timeline_plan"),
            audio_summary=plans.get("audio_summary"),
        )
        elapsed = round((time.perf_counter() - t0) * 1000.0, 3)
        if job.observability:
            job.observability.animation_duration_sec = job.duration_sec
            job.observability.processing_time_ms = elapsed
            job.observability.queue_time_ms = queue_ms
            job.observability.retry_count = job.retry_count
        job.production_ready = bool(job.consistency and job.consistency.consistent)
        job.version += 1
        job.state = "completed"
        motion_queue.update_state(job_id, "completed")
        store.save(job)
        return job
    except Exception as exc:
        motion_queue.update_state(job_id, "failed", error=str(exc))
        job = store.get(job_id) or motion_queue.get(job_id) or job
        job.state = "failed"
        job.error = str(exc)
        store.save(job)
        return job


def generate_motion(
    *,
    job_id: str | None = None,
    character_id: str | None = None,
    actions: list[str] | None = None,
    action: str | None = None,
    emotion: str | None = None,
    duration_sec: float | None = None,
    **kwargs: Any,
) -> dict[str, Any]:
    if job_id:
        job = store.get(job_id) or motion_queue.get(job_id)
        if not job:
            raise ValueError(f"Motion job not found: {job_id}")
    else:
        created = create_motion_job(
            character_id=character_id,
            actions=actions,
            action=action,
            emotion=emotion,
            duration_sec=duration_sec,
            **kwargs,
        )
        job_id = created["job_id"]
    processed = process_motion_job(job_id)
    if not processed:
        raise ValueError(f"Failed to process motion job: {job_id}")
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
        "operation": "generate",
        **processed.to_dict(),
        "queue": motion_queue.status(),
    }


def get_motion(job_id: str) -> dict[str, Any] | None:
    job = store.get(job_id) or motion_queue.get(job_id)
    if not job:
        return None
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        **job.to_dict(),
    }


def motion_history(limit: int = 50) -> dict[str, Any]:
    jobs = store.history(limit=limit)
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "jobs": [j.summary() for j in jobs],
        "count": len(jobs),
        "queue": motion_queue.status(),
    }


def motion_library_payload() -> dict[str, Any]:
    return {
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        **list_motion_library(),
    }


def create_dict(**kwargs: Any) -> dict[str, Any]:
    return create_motion_job(**kwargs)


def generate_dict(**kwargs: Any) -> dict[str, Any]:
    return generate_motion(**kwargs)
