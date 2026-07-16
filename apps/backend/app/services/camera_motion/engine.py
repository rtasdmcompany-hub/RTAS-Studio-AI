"""
Camera Motion Engine.

Professional dolly, crane, drone, orbit, slider, tracking, push in, pull out,
POV, steadicam, handheld — with adaptive camera logic integrated with
Director, Motion Intelligence, and Scene Planner.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any
from uuid import uuid4

from app.services.camera_motion.adaptive import choose_camera_motion
from app.services.camera_motion.bridge import (
    build_director_integration,
    build_motion_integration,
    build_scene_planner_integration,
    camera_for_scene,
    emotion_hint,
    locomotion_for_scene,
    pacing_for_scene,
    resolve_cameras,
    resolve_scenes,
    scene_directives,
)
from app.services.camera_motion.catalog import DISPLAY_NAME, MOTION_KINDS, display
from app.services.camera_motion.models import CameraMotionPlan, SceneCameraMotion
from app.services.camera_motion.path import flatten_timeline, plan_motion_cues
from app.services.camera_motion.store import get_plan as store_get
from app.services.camera_motion.store import put_plan

logger = logging.getLogger(__name__)


def _job_id(prompt: str) -> str:
    seed = f"{prompt}|{uuid4().hex[:8]}"
    return f"cammotion_{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:10]}"


def _scene_text(scene: dict[str, Any], prompt: str) -> str:
    """Scene-local text only — avoid polluting every beat with the full prompt."""
    actions = scene.get("actions") or []
    if isinstance(actions, list):
        act = " ".join(str(a) for a in actions if a)
    else:
        act = str(actions)
    parts = [
        str(scene.get("title") or ""),
        str(scene.get("description") or ""),
        act,
    ]
    local = " ".join(p for p in parts if p).strip()
    # Fallback to prompt only when the scene has almost no content
    if len(local) < 12:
        return (local + " " + (prompt or "")).strip()
    return local


def _scene_duration(scene: dict[str, Any], fallback: float) -> float:
    for key in ("duration_seconds", "duration", "Duration"):
        val = scene.get(key)
        if val is not None:
            try:
                return max(1.0, float(val))
            except (TypeError, ValueError):
                pass
    return fallback


def _scene_index(scene: dict[str, Any], i: int) -> int:
    for key in ("index", "scene_index", "SceneIndex"):
        if scene.get(key) is not None:
            try:
                return int(scene[key])
            except (TypeError, ValueError):
                pass
    return i


def build_camera_motion_plan(
    prompt: str,
    *,
    scenes: list[dict[str, Any]] | None = None,
    cameras: list[dict[str, Any]] | None = None,
    shots: list[dict[str, Any]] | None = None,
    director_plan: dict[str, Any] | None = None,
    scene_breakdown: dict[str, Any] | None = None,
    production_package: dict[str, Any] | None = None,
    prompt_understanding: dict[str, Any] | None = None,
    motion_intelligence: dict[str, Any] | None = None,
    duration_seconds: float | None = None,
    parent_generation_id: str | None = None,
) -> CameraMotionPlan:
    text = (prompt or "").strip() or "Cinematic scene with professional camera move."
    scene_list = resolve_scenes(scenes, scene_breakdown, production_package)
    cam_list = resolve_cameras(cameras, production_package)
    dp = director_plan or {}

    if not scene_list:
        scene_list = [
            {
                "index": 0,
                "title": "Camera Beat",
                "description": text,
                "duration_seconds": float(duration_seconds or 8.0),
                "actions": [],
            }
        ]

    default_dur = float(duration_seconds or 6.0)
    if len(scene_list) > 1 and duration_seconds:
        default_dur = max(2.0, float(duration_seconds) / len(scene_list))

    scene_plans: list[SceneCameraMotion] = []
    for i, scene in enumerate(scene_list):
        idx = _scene_index(scene, i)
        dur = _scene_duration(scene, default_dur)
        blob = _scene_text(scene, text)
        actions = scene.get("actions") if isinstance(scene.get("actions"), list) else []
        cam = camera_for_scene(cam_list, idx, i)
        loco = locomotion_for_scene(motion_intelligence, idx)
        pacing = pacing_for_scene(dp, idx)
        emotion = emotion_hint(dp, prompt_understanding, idx)

        adaptive = choose_camera_motion(
            blob,
            camera=cam,
            actions=[str(a) for a in (actions or [])],
            locomotion=loco,
            emotion=emotion,
            director_pacing=pacing,
            cinematic_rhythm=str(dp.get("cinematic_rhythm") or "") or None,
        )

        framing = str(cam.get("framing") or "")
        angle = str(cam.get("angle") or "")
        cues = plan_motion_cues(
            adaptive.chosen,
            duration_seconds=dur,
            text=blob,
            scene_index=idx,
            pacing=pacing,
            framing=framing or None,
        )

        # If shots exist for this scene, annotate first matching shot
        if shots:
            for sh in shots:
                if int(sh.get("scene_index", -1)) == idx:
                    for c in cues:
                        if c.shot_index is None:
                            c.shot_index = int(sh.get("shot_index", 0) or 0)
                    break

        scm = SceneCameraMotion(
            scene_index=idx,
            title=str(scene.get("title") or f"Scene {idx}"),
            duration_seconds=dur,
            primary_motion=adaptive.chosen,
            adaptive=adaptive,
            cues=cues,
            framing=framing,
            angle=angle,
        )
        scm.directives = scene_directives(scm)
        scene_plans.append(scm)

    timeline = flatten_timeline(scene_plans)
    total = sum(s.duration_seconds for s in scene_plans)

    provider_directives = [
        "PROFESSIONAL CAMERA MOTION ENGINE — cinematic, motivated moves only.",
        "Supported: Dolly, Crane, Drone, Orbit, Slider, Tracking, Push In, Pull Out, POV, Steadicam, Handheld.",
        "Ease major moves; avoid robotic teleport; match subject locomotion tempo when tracking.",
    ]
    for s in scene_plans[:10]:
        provider_directives.append(
            f"Scene {s.scene_index}: {display(s.primary_motion)} — {s.adaptive.reason}"
        )
        for d in s.directives[:2]:
            provider_directives.append(f"  {d}")

    adaptive_logic = {
        "mode": "context_weighted",
        "supported_motions": list(MOTION_KINDS),
        "display_names": dict(DISPLAY_NAME),
        "factors": [
            "prompt_keywords",
            "camera_plan",
            "subject_locomotion",
            "emotion",
            "director_pacing",
            "cinematic_rhythm",
        ],
        "decisions": [s.adaptive.to_dict() for s in scene_plans],
    }

    plan = CameraMotionPlan(
        job_id=_job_id(text),
        prompt=text[:2000],
        total_duration_seconds=round(total, 3),
        scenes=scene_plans,
        timeline=timeline,
        adaptive_logic=adaptive_logic,
        director_integration=build_director_integration(dp, scene_plans),
        motion_integration=build_motion_integration(motion_intelligence, scene_plans),
        scene_planner_integration=build_scene_planner_integration(
            scene_list, scene_breakdown
        ),
        provider_directives=provider_directives,
    )
    if parent_generation_id:
        plan.director_integration["parent_generation_id"] = parent_generation_id

    put_plan(plan)
    logger.info(
        "camera_motion_ready job=%s scenes=%s motions=%s",
        plan.job_id,
        len(plan.scenes),
        [s.primary_motion for s in plan.scenes],
    )
    return plan


def build_camera_motion_dict(prompt: str, **kwargs: Any) -> dict[str, Any]:
    plan = build_camera_motion_plan(prompt, **kwargs)
    return {"plan": plan.to_dict(), "summary": plan.summary()}


def get_plan(job_id: str) -> CameraMotionPlan | None:
    return store_get(job_id)
