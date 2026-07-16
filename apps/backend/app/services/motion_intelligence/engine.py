"""
Motion Intelligence Engine.

AI decides walking, running, sitting, standing, turning, looking,
hand motion, body motion, and natural human animation — integrated with
Director, Character Memory, Camera, and Scene Planner.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any
from uuid import uuid4

from app.services.motion_intelligence.body_motion import plan_body_motion
from app.services.motion_intelligence.director_bridge import (
    build_camera_integration,
    build_character_integration,
    build_director_integration,
    build_scene_planner_integration,
    camera_sync_notes,
    director_notes_for_scene,
    resolve_cameras,
    resolve_scene_list,
)
from app.services.motion_intelligence.gaze import plan_gaze_cues
from app.services.motion_intelligence.hand_motion import plan_hand_motion
from app.services.motion_intelligence.locomotion import (
    actions_from_scene,
    detect_primary_locomotion,
    plan_locomotion_cues,
)
from app.services.motion_intelligence.models import MotionIntelligencePlan, SceneMotionPlan
from app.services.motion_intelligence.naturalness import (
    build_animation_directives,
    build_natural_hint,
    flatten_timeline,
)
from app.services.motion_intelligence.store import get_plan as store_get
from app.services.motion_intelligence.store import put_plan

logger = logging.getLogger(__name__)


def _job_id(prompt: str) -> str:
    seed = f"{prompt}|{uuid4().hex[:8]}"
    return f"motion_{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:10]}"


def _scene_text(scene: dict[str, Any], prompt: str) -> str:
    parts = [
        str(scene.get("title") or ""),
        str(scene.get("description") or ""),
        " ".join(actions_from_scene(scene)),
        " ".join(str(c) for c in (scene.get("characters") or []) if c),
        prompt or "",
    ]
    return " ".join(p for p in parts if p).strip()


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


def _pacing_for(director_plan: dict[str, Any] | None, scene_index: int) -> str | None:
    dp = director_plan or {}
    decisions = dp.get("decisions") or []
    if isinstance(decisions, list) and scene_index < len(decisions):
        d = decisions[scene_index]
        if isinstance(d, dict) and d.get("pacing"):
            return str(d["pacing"])
    pacing = dp.get("emotional_pacing") or []
    if isinstance(pacing, list) and scene_index < len(pacing):
        return str(pacing[scene_index])
    return None


def _emotion_hint(
    director_plan: dict[str, Any] | None,
    prompt_understanding: dict[str, Any] | None,
    scene_index: int,
) -> str | None:
    pu = prompt_understanding or {}
    if pu.get("emotion"):
        return str(pu["emotion"])
    dp = director_plan or {}
    pacing = dp.get("emotional_pacing") or []
    if isinstance(pacing, list) and scene_index < len(pacing):
        return str(pacing[scene_index])
    return None


def build_motion_intelligence_plan(
    prompt: str,
    *,
    scenes: list[dict[str, Any]] | None = None,
    cameras: list[dict[str, Any]] | None = None,
    character_memory: list[dict[str, Any]] | None = None,
    director_plan: dict[str, Any] | None = None,
    scene_breakdown: dict[str, Any] | None = None,
    production_package: dict[str, Any] | None = None,
    prompt_understanding: dict[str, Any] | None = None,
    duration_seconds: float | None = None,
    parent_generation_id: str | None = None,
) -> MotionIntelligencePlan:
    text = (prompt or "").strip() or "A person standing naturally."
    scene_list = resolve_scene_list(scenes, scene_breakdown, production_package)
    cam_list = resolve_cameras(cameras, production_package)
    char_ids, walking_styles, char_integration = build_character_integration(character_memory)
    primary_char = char_ids[0] if char_ids else None
    primary_walk = walking_styles.get(primary_char or "", "") if primary_char else ""

    if not scene_list:
        # Single synthetic scene from prompt
        scene_list = [
            {
                "index": 0,
                "title": "Motion Beat",
                "description": text,
                "duration_seconds": float(duration_seconds or 8.0),
                "actions": [],
                "characters": char_ids[:1],
            }
        ]

    default_dur = float(duration_seconds or 6.0)
    if len(scene_list) > 1 and duration_seconds:
        default_dur = max(2.0, float(duration_seconds) / len(scene_list))

    scene_plans: list[SceneMotionPlan] = []
    for i, scene in enumerate(scene_list):
        idx = _scene_index(scene, i)
        dur = _scene_duration(scene, default_dur)
        blob = _scene_text(scene, text)
        actions = actions_from_scene(scene)
        primary = detect_primary_locomotion(blob, actions=actions)

        cam = {}
        for c in cam_list:
            if int(c.get("scene_index", -1)) == idx:
                cam = c
                break
        if not cam and i < len(cam_list):
            cam = cam_list[i]

        framing = str(cam.get("framing") or "")
        pacing = _pacing_for(director_plan, idx)
        emotion = _emotion_hint(director_plan, prompt_understanding, idx)

        loco = plan_locomotion_cues(
            duration_seconds=dur,
            primary=primary,
            text=blob,
            character_id=primary_char,
            walking_style=primary_walk or None,
            pacing=pacing,
        )
        gaze = plan_gaze_cues(
            duration_seconds=dur,
            text=blob,
            primary=primary,
            character_id=primary_char,
            camera_framing=framing,
        )
        hands = plan_hand_motion(
            duration_seconds=dur,
            text=blob,
            primary=primary,
            character_id=primary_char,
            emotion=emotion,
        )
        body = plan_body_motion(
            duration_seconds=dur,
            text=blob,
            primary=primary,
            character_id=primary_char,
            emotion=emotion,
        )

        scene_plans.append(
            SceneMotionPlan(
                scene_index=idx,
                title=str(scene.get("title") or f"Scene {idx}"),
                duration_seconds=dur,
                primary_locomotion=primary,
                locomotion=loco,
                gaze=gaze,
                hand_motion=hands,
                body_motion=body,
                camera_sync=camera_sync_notes(primary, cam),
                director_notes=director_notes_for_scene(primary, director_plan, idx),
            )
        )

    kinds = [s.primary_locomotion for s in scene_plans]
    emotion0 = _emotion_hint(director_plan, prompt_understanding, 0)
    natural = build_natural_hint(primary_kinds=kinds, emotion=emotion0)
    directives = build_animation_directives(
        scene_plans, natural, walking_styles=walking_styles
    )
    timeline = flatten_timeline(scene_plans)
    total = sum(s.duration_seconds for s in scene_plans)

    plan = MotionIntelligencePlan(
        job_id=_job_id(text),
        prompt=text[:2000],
        total_duration_seconds=round(total, 3),
        character_ids=char_ids,
        walking_styles=walking_styles,
        scenes=scene_plans,
        natural=natural,
        director_integration=build_director_integration(director_plan, scene_plans),
        camera_integration=build_camera_integration(cam_list, scene_plans),
        character_integration=char_integration,
        scene_planner_integration=build_scene_planner_integration(
            scene_list, scene_breakdown
        ),
        timeline=timeline,
        animation_directives=directives,
    )
    if parent_generation_id:
        plan.director_integration["parent_generation_id"] = parent_generation_id

    put_plan(plan)
    logger.info(
        "motion_intelligence_ready job=%s scenes=%s loco=%s",
        plan.job_id,
        len(plan.scenes),
        kinds,
    )
    return plan


def build_motion_intelligence_dict(prompt: str, **kwargs: Any) -> dict[str, Any]:
    plan = build_motion_intelligence_plan(prompt, **kwargs)
    return {"plan": plan.to_dict(), "summary": plan.summary()}


def get_plan(job_id: str) -> MotionIntelligencePlan | None:
    return store_get(job_id)
