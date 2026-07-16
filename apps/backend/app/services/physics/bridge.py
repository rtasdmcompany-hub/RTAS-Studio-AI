"""Bridge Physics ↔ Director / Scene Planner / Motion Intelligence."""

from __future__ import annotations

from typing import Any

from app.services.physics.catalog import display
from app.services.physics.models import ScenePhysicsPlan


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


def locomotion_for_scene(
    motion_intelligence: dict[str, Any] | None,
    scene_index: int,
) -> str | None:
    if not motion_intelligence:
        return None
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


def weather_from_context(
    prompt_understanding: dict[str, Any] | None,
    scene: dict[str, Any],
) -> str | None:
    pu = prompt_understanding or {}
    if pu.get("weather"):
        return str(pu["weather"])
    env = str(scene.get("environment") or "")
    if env:
        return env
    return None


def build_director_integration(
    director_plan: dict[str, Any] | None,
    scenes: list[ScenePhysicsPlan],
) -> dict[str, Any]:
    dp = director_plan or {}
    return {
        "cinematic_rhythm": dp.get("cinematic_rhythm"),
        "transition_style": dp.get("transition_style"),
        "physics_aligned": [
            {
                "scene_index": s.scene_index,
                "effects": s.active_effects,
                "displays": [display(e) for e in s.active_effects],
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
        "environments": [s.get("environment") for s in scenes_raw[:16]],
    }


def build_motion_integration(
    motion_intelligence: dict[str, Any] | None,
    scenes: list[ScenePhysicsPlan],
) -> dict[str, Any]:
    mi = motion_intelligence or {}
    return {
        "motion_job_id": mi.get("job_id"),
        "soft_body_sync": [
            {
                "scene_index": s.scene_index,
                "hair": "hair_motion" in s.active_effects,
                "cloth": "cloth_motion" in s.active_effects,
            }
            for s in scenes
        ],
    }


def scene_directives(scene: ScenePhysicsPlan) -> list[str]:
    lines = [
        f"PHYSICS effects: {', '.join(display(e) for e in scene.active_effects)}",
    ]
    if scene.gravity:
        lines.append(f"Gravity strength={scene.gravity.strength}")
    if scene.wind:
        lines.append(f"Wind strength={scene.wind.strength}; turb={scene.wind.turbulence}")
    for cue in scene.cues[:6]:
        if cue.particles:
            lines.append(f"  {display(cue.kind)}: {len(cue.particles)} particle system(s)")
        if cue.soft_body:
            lines.append(
                f"  {display(cue.kind)}: stiffness={cue.soft_body.stiffness} "
                f"wind_resp={cue.soft_body.wind_response}"
            )
    return lines
