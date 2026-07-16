"""Bridge Motion Intelligence ↔ Director / Character / Camera / Scene Planner."""

from __future__ import annotations

from typing import Any

from app.services.motion_intelligence.models import LocomotionKind, SceneMotionPlan


def _camera_for_scene(cameras: list[dict[str, Any]], scene_index: int) -> dict[str, Any]:
    for cam in cameras:
        if int(cam.get("scene_index", -1)) == scene_index:
            return cam
    if cameras and scene_index < len(cameras):
        return cameras[scene_index]
    return {}


def camera_sync_notes(
    primary: LocomotionKind,
    camera: dict[str, Any],
) -> list[str]:
    movement = str(camera.get("movement") or camera.get("cinematic_motion") or "")
    framing = str(camera.get("framing") or "")
    notes: list[str] = []
    if primary in ("walking", "running"):
        if any(x in movement.lower() for x in ("track", "steadicam", "follow", "dolly")):
            notes.append(f"Match camera {movement} to character locomotion speed.")
        else:
            notes.append("Prefer tracking / steadicam when subject walks or runs.")
    if primary == "sitting" and "wide" in framing.lower():
        notes.append("Hold wider frame through sit-down for body readability.")
    if primary in ("looking", "turning"):
        notes.append("Allow slight camera settle so gaze/turn reads clearly.")
    if movement:
        notes.append(f"Camera movement: {movement}; framing: {framing or 'default'}.")
    return notes


def director_notes_for_scene(
    primary: LocomotionKind,
    director_plan: dict[str, Any] | None,
    scene_index: int,
) -> list[str]:
    notes: list[str] = []
    dp = director_plan or {}
    rhythm = dp.get("cinematic_rhythm")
    if rhythm:
        notes.append(f"Follow cinematic rhythm: {rhythm}")
    pacing_list = dp.get("emotional_pacing") or []
    if isinstance(pacing_list, list) and scene_index < len(pacing_list):
        notes.append(f"Emotional pacing: {pacing_list[scene_index]}")
    decisions = dp.get("decisions") or []
    if isinstance(decisions, list) and scene_index < len(decisions):
        d = decisions[scene_index]
        if isinstance(d, dict):
            if d.get("pacing"):
                notes.append(f"Director pacing: {d['pacing']}")
            if d.get("emotional_beat"):
                notes.append(f"Beat: {d['emotional_beat']}")
    if primary == "running":
        notes.append("Energy beat — keep motion decisive; cut on stride peak if needed.")
    elif primary == "walking":
        notes.append("Motivational walk — camera and performance share tempo.")
    elif primary == "standing":
        notes.append("Performance hold — rely on gaze, hands, micro body for life.")
    return notes


def build_director_integration(
    director_plan: dict[str, Any] | None,
    scenes: list[SceneMotionPlan],
) -> dict[str, Any]:
    dp = director_plan or {}
    return {
        "cinematic_rhythm": dp.get("cinematic_rhythm"),
        "transition_style": dp.get("transition_style"),
        "scene_emphasis": (dp.get("scene_emphasis") or [])[:8],
        "motion_aligned_scenes": [
            {
                "scene_index": s.scene_index,
                "primary_locomotion": s.primary_locomotion,
                "director_notes": s.director_notes[:4],
            }
            for s in scenes
        ],
    }


def build_camera_integration(
    cameras: list[dict[str, Any]],
    scenes: list[SceneMotionPlan],
) -> dict[str, Any]:
    synced = []
    for s in scenes:
        cam = _camera_for_scene(cameras, s.scene_index)
        synced.append(
            {
                "scene_index": s.scene_index,
                "movement": cam.get("movement") or cam.get("cinematic_motion"),
                "framing": cam.get("framing"),
                "lens": cam.get("lens"),
                "sync": s.camera_sync[:4],
            }
        )
    return {"cameras": synced, "count": len(cameras)}


def build_character_integration(
    character_memory: list[dict[str, Any]] | None,
) -> tuple[list[str], dict[str, str], dict[str, Any]]:
    ids: list[str] = []
    walks: dict[str, str] = {}
    details: list[dict[str, Any]] = []
    for c in character_memory or []:
        if not isinstance(c, dict):
            continue
        cid = str(c.get("character_id") or c.get("subject_id") or "").strip()
        if not cid:
            continue
        ids.append(cid)
        walk = str(c.get("walking_style") or "").strip()
        if walk:
            walks[cid] = walk
        details.append(
            {
                "character_id": cid,
                "walking_style": walk or None,
                "pose": c.get("pose"),
                "expression": c.get("expression"),
                "body": c.get("body"),
            }
        )
    return ids, walks, {"characters": details, "count": len(ids)}


def build_scene_planner_integration(
    scenes_raw: list[dict[str, Any]],
    scene_breakdown: dict[str, Any] | None,
) -> dict[str, Any]:
    titles = []
    for s in scenes_raw:
        titles.append(
            {
                "index": s.get("index", s.get("scene_index")),
                "title": s.get("title"),
                "actions": s.get("actions") or [],
                "duration_seconds": s.get("duration_seconds"),
            }
        )
    prod = (scene_breakdown or {}).get("Production") or {}
    return {
        "scene_count": len(scenes_raw),
        "estimated_runtime": prod.get("EstimatedRuntime"),
        "scenes": titles[:16],
    }


def resolve_scene_list(
    scenes: list[dict[str, Any]] | None,
    scene_breakdown: dict[str, Any] | None,
    production_package: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    if scenes:
        return list(scenes)
    # Scene breakdown nested shapes
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
