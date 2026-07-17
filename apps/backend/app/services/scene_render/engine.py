"""
Scene Render Engine.

Scene rendering with lighting, shadows, reflections, HDR, ray-tracing ready
flags, scene cache, memory optimization, and GPU queue.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any
from uuid import uuid4

from app.services.scene_render.bridge import (
    build_camera_integration,
    build_director_integration,
    build_physics_integration,
    build_production_integration,
    camera_motion_for_scene,
    physics_effects_for_scene,
    resolve_quality,
    resolve_scenes,
    scene_directives,
)
from app.services.scene_render.cache import build_cache_entry, cache_stats
from app.services.scene_render.gpu_queue import (
    enqueue_many,
    estimate_job,
    prioritize_scene_order,
    queue_status,
)
from app.services.scene_render.hdr import build_hdr
from app.services.scene_render.lighting import build_lighting
from app.services.scene_render.memory import build_memory_budget, optimize_memory_plan
from app.services.scene_render.models import RenderQuality, SceneRenderPass, SceneRenderPlan
from app.services.scene_render.ray_tracing import build_ray_tracing
from app.services.scene_render.reflections import build_reflections
from app.services.scene_render.shadows import build_shadows
from app.services.scene_render.store import get_plan as store_get
from app.services.scene_render.store import put_plan

logger = logging.getLogger(__name__)


def _job_id(prompt: str) -> str:
    seed = f"{prompt}|{uuid4().hex[:8]}"
    return f"scenerender_{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:10]}"


def _scene_text(scene: dict[str, Any], prompt: str) -> str:
    actions = scene.get("actions") or []
    if isinstance(actions, list):
        act = " ".join(str(a) for a in actions if a)
    else:
        act = str(actions)
    parts = [
        str(scene.get("title") or ""),
        str(scene.get("description") or ""),
        str(scene.get("environment") or ""),
        act,
    ]
    local = " ".join(p for p in parts if p).strip()
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


def build_scene_render_plan(
    prompt: str,
    *,
    scenes: list[dict[str, Any]] | None = None,
    cameras: list[dict[str, Any]] | None = None,
    director_plan: dict[str, Any] | None = None,
    scene_breakdown: dict[str, Any] | None = None,
    production_package: dict[str, Any] | None = None,
    production_render: dict[str, Any] | None = None,
    prompt_understanding: dict[str, Any] | None = None,
    visual_style: dict[str, Any] | None = None,
    physics: dict[str, Any] | None = None,
    camera_motion: dict[str, Any] | None = None,
    quality: str | None = None,
    duration_seconds: float | None = None,
    enqueue_gpu: bool = True,
    parent_generation_id: str | None = None,
) -> SceneRenderPlan:
    text = (prompt or "").strip() or "Cinematic scene render with natural lighting."
    scene_list = resolve_scenes(scenes, scene_breakdown, production_package)
    q: RenderQuality = resolve_quality(quality, director_plan, production_render)
    pu = prompt_understanding or {}
    vs = visual_style or {}

    if not scene_list:
        scene_list = [
            {
                "index": 0,
                "title": "Render Beat",
                "description": text,
                "duration_seconds": float(duration_seconds or 8.0),
                "environment": str(pu.get("weather") or ""),
                "actions": [],
            }
        ]

    default_dur = float(duration_seconds or 6.0)
    if len(scene_list) > 1 and duration_seconds:
        default_dur = max(2.0, float(duration_seconds) / len(scene_list))

    indices = [_scene_index(s, i) for i, s in enumerate(scene_list)]
    priorities = {idx: prio for idx, prio in prioritize_scene_order(indices)}

    passes: list[SceneRenderPass] = []
    budgets = []
    gpu_jobs = []

    for i, scene in enumerate(scene_list):
        idx = _scene_index(scene, i)
        dur = _scene_duration(scene, default_dur)
        blob = _scene_text(scene, text)
        fx = physics_effects_for_scene(physics, idx)
        particle_heavy = any(
            e in fx for e in ("rain", "smoke", "dust", "fire", "explosion", "particles", "water")
        )
        cam_move = camera_motion_for_scene(camera_motion, idx)

        lighting = build_lighting(
            blob,
            visual_style=vs,
            prompt_understanding=pu,
            environment=str(scene.get("environment") or ""),
        )
        hard = "hard" in lighting.key.lower() or "harsh" in blob
        rt = build_ray_tracing(blob, quality=q)
        shadows = build_shadows(blob, quality=q, hard_light=hard)
        reflections = build_reflections(blob, quality=q, ray_tracing_ready=rt.ready)
        hdr = build_hdr(
            blob,
            quality=q,
            lighting_temp_k=lighting.color_temperature_k,
            visual_style=vs,
        )
        memory = build_memory_budget(
            quality=q,
            scene_count=len(scene_list),
            particle_heavy=particle_heavy,
            physics_effects=fx,
        )
        budgets.append(memory)

        assets = []
        if cameras and i < len(cameras):
            assets.append(f"camera:{cameras[i].get('lens') or cameras[i].get('movement')}")
        if cam_move:
            assets.append(f"cam_motion:{cam_move}")
        for e in fx[:6]:
            assets.append(f"fx:{e}")

        cache_entry = build_cache_entry(
            scene,
            scene_index=idx,
            lighting_key=lighting.key,
            quality=q,
            physics_effects=fx,
            assets=assets,
            duration_seconds=dur,
        )

        gpu_job = estimate_job(
            idx,
            quality=q,
            priority=priorities.get(idx, 100 + i),
            particle_heavy=particle_heavy,
        )
        gpu_jobs.append(gpu_job)

        sp = SceneRenderPass(
            scene_index=idx,
            title=str(scene.get("title") or f"Scene {idx}"),
            duration_seconds=dur,
            lighting=lighting,
            shadows=shadows,
            reflections=reflections,
            hdr=hdr,
            ray_tracing=rt,
            cache=cache_entry,
            memory=memory,
            gpu_job=gpu_job,
        )
        if particle_heavy:
            sp.directives.append("particle-aware memory + GPU estimate")
        sp.directives = scene_directives(sp) + sp.directives
        passes.append(sp)

    if _dbg:
        print("enqueue", enqueue_gpu, flush=True)
    if enqueue_gpu:
        enqueue_many(gpu_jobs)

    mem_opt = optimize_memory_plan(budgets, quality=q)
    mem_opt["cache_stats"] = cache_stats()
    mem_opt["gpu_queue"] = queue_status()
    if _dbg:
        print("mem_opt ok", flush=True)

    timeline = []
    offset = 0.0
    for sp in passes:
        timeline.append(
            {
                "t": round(offset, 3),
                "end": round(offset + sp.duration_seconds, 3),
                "scene": sp.scene_index,
                "quality": q,
                "hdr": sp.hdr.enabled,
                "rt_ready": sp.ray_tracing.ready,
                "gpu_job_id": sp.gpu_job.job_id,
                "cache_key": sp.cache.cache_key,
            }
        )
        offset += sp.duration_seconds

    provider_directives = [
        "SCENE RENDER ENGINE — cinematic lighting, shadows, reflections, HDR.",
        "Ray-tracing ready materials/lights; raster fallback when RT unavailable.",
        "Use scene cache fingerprints; respect VRAM budgets and GPU queue priority.",
        f"Global quality={q}; HDR={all(s.hdr.enabled for s in passes)}; "
        f"RT={any(s.ray_tracing.ready for s in passes)}",
    ]
    for sp in passes[:8]:
        provider_directives.append(
            f"Scene {sp.scene_index}: {sp.lighting.key}; shadows={sp.shadows.resolution}; "
            f"refl={sp.reflections.mode}; gpu={sp.gpu_job.job_id}"
        )

    plan = SceneRenderPlan(
        job_id=_job_id(text),
        prompt=text[:2000],
        quality=q,
        total_duration_seconds=round(sum(s.duration_seconds for s in passes), 3),
        scenes=passes,
        gpu_queue=list(gpu_jobs),
        scene_cache=[s.cache for s in passes],
        memory_optimization=mem_opt,
        ray_tracing_ready=any(s.ray_tracing.ready for s in passes),
        hdr_enabled=all(s.hdr.enabled for s in passes),
        timeline=timeline,
        director_integration=build_director_integration(director_plan, passes),
        production_integration=build_production_integration(
            production_render, production_package
        ),
        physics_integration=build_physics_integration(physics, passes),
        camera_integration=build_camera_integration(camera_motion, passes),
        provider_directives=provider_directives,
    )
    if parent_generation_id:
        plan.director_integration["parent_generation_id"] = parent_generation_id

    put_plan(plan)
    logger.info(
        "scene_render_ready job=%s scenes=%s quality=%s rt=%s gpu=%s",
        plan.job_id,
        len(plan.scenes),
        q,
        plan.ray_tracing_ready,
        len(plan.gpu_queue),
    )
    return plan


def build_scene_render_dict(prompt: str, **kwargs: Any) -> dict[str, Any]:
    plan = build_scene_render_plan(prompt, **kwargs)
    return {"plan": plan.to_dict(), "summary": plan.summary()}


def get_plan(job_id: str) -> SceneRenderPlan | None:
    return store_get(job_id)
