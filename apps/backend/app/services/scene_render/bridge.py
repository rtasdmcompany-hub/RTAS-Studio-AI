"""Bridge Scene Render ↔ Director / Production / Physics / Camera."""

from __future__ import annotations

from typing import Any

from app.services.scene_render.models import RenderQuality, SceneRenderPass


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


def resolve_quality(
    quality: str | None,
    director_plan: dict[str, Any] | None,
    production_render: dict[str, Any] | None,
) -> RenderQuality:
    q = (quality or "").strip().lower()
    aliases = {
        "draft": "draft",
        "preview": "preview",
        "production": "production",
        "cinema": "cinema",
        "cinematic": "cinema",
        "final": "production",
        "high": "production",
    }
    if q in aliases:
        return aliases[q]  # type: ignore[return-value]

    rhythm = str((director_plan or {}).get("cinematic_rhythm") or "").lower()
    if any(x in rhythm for x in ("epic", "cinema", "grand")):
        return "cinema"

    if production_render and (production_render.get("export_specs") or production_render.get("validation")):
        return "production"
    return "production"


def physics_effects_for_scene(
    physics: dict[str, Any] | None,
    scene_index: int,
) -> list[str]:
    if not physics:
        return []
    # Summary shape
    if isinstance(physics.get("effects"), list) and not physics.get("scenes"):
        return [str(e) for e in physics["effects"]]
    for s in physics.get("scenes") or []:
        if not isinstance(s, dict):
            continue
        if int(s.get("scene_index", -1)) == scene_index:
            return [str(e) for e in (s.get("active_effects") or [])]
    if scene_index == 0 and isinstance(physics.get("effects"), list):
        return [str(e) for e in physics["effects"]]
    return []


def camera_motion_for_scene(
    camera_motion: dict[str, Any] | None,
    scene_index: int,
) -> str | None:
    if not camera_motion:
        return None
    primaries = camera_motion.get("primary_motions") or []
    if isinstance(primaries, list) and scene_index < len(primaries):
        return str(primaries[scene_index])
    for s in camera_motion.get("scenes") or []:
        if isinstance(s, dict) and int(s.get("scene_index", -1)) == scene_index:
            return str(s.get("primary_motion") or "")
    return None


def build_director_integration(
    director_plan: dict[str, Any] | None,
    scenes: list[SceneRenderPass],
) -> dict[str, Any]:
    dp = director_plan or {}
    return {
        "cinematic_rhythm": dp.get("cinematic_rhythm"),
        "transition_style": dp.get("transition_style"),
        "render_aligned": [
            {
                "scene_index": s.scene_index,
                "quality": s.ray_tracing.quality,
                "hdr": s.hdr.enabled,
                "rt_ready": s.ray_tracing.ready,
            }
            for s in scenes
        ],
    }


def build_production_integration(
    production_render: dict[str, Any] | None,
    production_package: dict[str, Any] | None,
) -> dict[str, Any]:
    pr = production_render or {}
    return {
        "export_validated": ((pr.get("validation") or {}).get("passed")),
        "has_manifest": bool(pr.get("video_manifest")),
        "package_keys": list((production_package or {}).keys())[:12],
    }


def build_physics_integration(
    physics: dict[str, Any] | None,
    scenes: list[SceneRenderPass],
) -> dict[str, Any]:
    return {
        "physics_job_id": (physics or {}).get("job_id"),
        "effects": (physics or {}).get("effects") or [],
        "particle_aware_scenes": [
            s.scene_index for s in scenes if "particle" in " ".join(s.directives).lower()
        ],
    }


def build_camera_integration(
    camera_motion: dict[str, Any] | None,
    scenes: list[SceneRenderPass],
) -> dict[str, Any]:
    return {
        "camera_motion_job_id": (camera_motion or {}).get("job_id"),
        "motions": (camera_motion or {}).get("primary_motions")
        or [camera_motion_for_scene(camera_motion, s.scene_index) for s in scenes],
    }


def scene_directives(pass_: SceneRenderPass) -> list[str]:
    return [
        f"RENDER scene {pass_.scene_index}: quality={pass_.ray_tracing.quality}",
        f"Lighting: {pass_.lighting.key}; {pass_.lighting.color_temperature_k}K; vol={pass_.lighting.volumetric}",
        f"Shadows: soft={pass_.shadows.soft} res={pass_.shadows.resolution} cascades={pass_.shadows.cascade_count}",
        f"Reflections: {pass_.reflections.mode} intensity={pass_.reflections.intensity}",
        f"HDR: {pass_.hdr.tonemapper} exposure={pass_.hdr.exposure} bloom={pass_.hdr.bloom}",
        f"RT ready={pass_.ray_tracing.ready} spp={pass_.ray_tracing.samples_per_pixel}",
        f"Cache={pass_.cache.cache_key} (~{pass_.cache.size_estimate_mb}MB)",
        f"GPU job={pass_.gpu_job.job_id} prio={pass_.gpu_job.priority} ~{pass_.gpu_job.estimated_ms}ms",
    ]
