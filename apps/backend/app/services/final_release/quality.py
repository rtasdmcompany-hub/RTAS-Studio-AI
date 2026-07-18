"""Production quality scoring across director → export chain."""

from __future__ import annotations

from typing import Any

from app.services.final_release.version import QUALITY_THRESHOLD


def _clamp100(v: float) -> float:
    return max(0.0, min(100.0, float(v)))


def score_production(
    *,
    director: dict[str, Any],
    video_engine: dict[str, Any] | None = None,
    export_job: dict[str, Any] | None = None,
) -> dict[str, Any]:
    plan = director.get("production_plan") or {}
    scenes = plan.get("scenes") or []
    shots = plan.get("shot_list") or []
    analysis = director.get("analysis") or {}

    scene_q = 90.0 if len(scenes) >= 4 else 60.0
    if all(s.get("environment") and s.get("emotion_flow") for s in scenes):
        scene_q = min(100.0, scene_q + 8.0)

    angles = set()
    for sh in shots:
        if sh.get("camera_angle"):
            angles.add(sh["camera_angle"])
    camera_q = 70.0 + min(25.0, len(angles) * 4.0)

    continuity = 95.0 if director.get("accuracy_score", 0) >= 80 else 55.0
    if plan.get("story_structure"):
        continuity = min(100.0, continuity + 3.0)

    lighting_q = 88.0
    if any(s.get("beat") in ("climax", "conflict") for s in scenes):
        lighting_q = 92.0

    emotions = {s.get("emotion_flow") for s in scenes if s.get("emotion_flow")}
    emotion_q = 70.0 + min(25.0, len(emotions) * 5.0)

    motion_q = 85.0
    if any(sh.get("camera_angle") in ("tracking", "drone", "pov") for sh in shots):
        motion_q = 92.0

    identity = 90.0
    if (director.get("integrations") or {}).get("character_dna", {}).get("linked"):
        identity = 96.0

    audio_q = 80.0
    cues = (plan.get("audio_plan") or {}).get("music_cues") or []
    if cues:
        audio_q = 90.0

    export_q = 70.0
    if export_job and (export_job.get("status") in ("completed", "ready", "packaged") or export_job.get("ok")):
        export_q = 95.0
    elif (plan.get("export_plan") or {}).get("formats"):
        export_q = 88.0

    ve_q = 80.0
    if video_engine:
        qs = video_engine.get("quality") or video_engine.get("quality_score") or {}
        if isinstance(qs, dict):
            overall = qs.get("overall") or qs.get("score") or qs.get("overall_score")
            if overall is not None:
                try:
                    val = float(overall)
                    ve_q = val * 100.0 if val <= 1.0 else val
                except (TypeError, ValueError):
                    ve_q = 80.0
        if video_engine.get("production_ready"):
            ve_q = max(ve_q, 90.0)

    overall = (
        scene_q * 0.14
        + camera_q * 0.12
        + continuity * 0.14
        + lighting_q * 0.10
        + emotion_q * 0.10
        + motion_q * 0.10
        + identity * 0.10
        + audio_q * 0.08
        + export_q * 0.06
        + ve_q * 0.06
    )
    overall = _clamp100(round(overall, 2))
    scores = {
        "scene_quality": round(scene_q, 2),
        "camera_quality": round(camera_q, 2),
        "continuity": round(continuity, 2),
        "lighting": round(lighting_q, 2),
        "emotion": round(emotion_q, 2),
        "motion": round(motion_q, 2),
        "identity_lock": round(identity, 2),
        "audio_sync": round(audio_q, 2),
        "export_package": round(export_q, 2),
        "video_engine": round(ve_q, 2),
        "overall_production_score": overall,
        "passed": overall >= QUALITY_THRESHOLD,
        "threshold": QUALITY_THRESHOLD,
        "genre": analysis.get("genre"),
        "format_type": analysis.get("format_type") or plan.get("format_type"),
    }
    return scores
