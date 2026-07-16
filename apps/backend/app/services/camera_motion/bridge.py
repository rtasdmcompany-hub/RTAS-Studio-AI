"""Bridge Camera Motion ↔ Director / Motion Intelligence / Scene Planner."""

from __future__ import annotations

from typing import Any

from app.services.camera_motion.catalog import display
from app.services.camera_motion.models import SceneCameraMotion


def resolve_scenes(
    scenes: list[dict[str, Any]] | None,
    scene_breakdown: dict[str, Any] | None,
    production_package: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if scenes:
        return list(scenes)
    if scene_breakdown:
        for key in ("scenes", "Scenes", "scene_plans"):
            block = scene_breakdown.get(key)
            if isinstance(block, list) and block:
                return list(block)
        narrative = scene_breakdown.get("Narrative") or {}
        if isinstance(narrative, dict):
            block = narrative.get("scenes") or narrative.get("Scenes")
            if isinstance(block, list) and block:
                return list(block)
    if production_package:
        block = production_package.get("scenes") or production_package.get("Scenes")
        if isinstance(block, list) and block:
            return list(block)
    return []


def resolve_cameras(
    cameras: list[dict[str, Any]] | None,
    production_package: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if cameras:
        return list(cameras)
    if production_package:
        block = production_package.get("cameras") or production_package.get("camera_plans")
        if isinstance(block, list):
            return list(block)
    return []


def camera_for_scene(cameras: list[dict[str, Any]], scene_index: int, i: int) -> dict[str, Any]:
    for cam in cameras:
        if int(cam.get("scene_index", -1)) == scene_index:
            return cam
    if i < len(cameras):
        return cameras[i]
    return {}


def locomotion_for_scene(
    motion_intelligence: dict[str, Any] | None,
    scene_index: int,
) -> str | None:
    if not motion_intelligence:
        return None
    # Accept summary or full plan shape
    scenes = motion_intelligence.get("scenes") or []
    if scenes and isinstance(scenes[0], dict) and "primary_locomotion" in scenes[0]:
        for s in scenes:
            if int(s.get("scene_index", -1)) == scene_index:
                return s.get("primary_locomotion")
        if scene_index < len(scenes):
            return scenes[scene_index].get("primary_locomotion")
    primaries = motion_intelligence.get("primary_locomotion") or []
    if isinstance(primaries, list) and scene_index < len(primaries):
        return str(primaries[scene_index])
    return None


def pacing_for_scene(director_plan: dict[str, Any] | None, scene_index: int) -> str | None:
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


def emotion_hint(
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


def build_director_integration(
    director_plan: dict[str, Any] | None,
    scenes: list[SceneCameraMotion],
) -> dict[str, Any]:
    dp = director_plan or {}
    return {
        "cinematic_rhythm": dp.get("cinematic_rhythm"),
        "transition_style": dp.get("transition_style"),
        "scene_emphasis": (dp.get("scene_emphasis") or [])[:8],
        "camera_aligned": [
            {
                "scene_index": s.scene_index,
                "primary_motion": s.primary_motion,
                "display": display(s.primary_motion),
                "reason": s.adaptive.reason,
            }
            for s in scenes
        ],
    }


def build_motion_integration(
    motion_intelligence: dict[str, Any] | None,
    scenes: list[SceneCameraMotion],
) -> dict[str, Any]:
    mi = motion_intelligence or {}
    return {
        "motion_job_id": mi.get("job_id"),
        "subject_locomotion": mi.get("primary_locomotion")
        or [s.get("primary_locomotion") for s in (mi.get("scenes") or []) if isinstance(s, dict)],
        "synced": [
            {
                "scene_index": s.scene_index,
                "camera": s.primary_motion,
                "notes": s.directives[:3],
            }
            for s in scenes
        ],
    }


def build_scene_planner_integration(
    scenes_raw: list[dict[str, Any]],
    scene_breakdown: dict[str, Any] | None,
) -> dict[str, Any]:
    prod = (scene_breakdown or {}).get("Production") or {}
    return {
        "scene_count": len(scenes_raw),
        "estimated_runtime": prod.get("EstimatedRuntime"),
        "titles": [s.get("title") for s in scenes_raw[:16]],
    }


def scene_directives(scene: SceneCameraMotion) -> list[str]:
    return [
        f"CAMERA: {display(scene.primary_motion)} ({scene.primary_motion})",
        f"Adaptive: {scene.adaptive.reason}",
        f"Framing={scene.framing or 'auto'}; angle={scene.angle or 'auto'}",
        *[f"Alt: {display(a)}" for a in scene.adaptive.alternatives[:2]],
    ]
