"""Bridge Multi GPU ↔ Scene Render / production workloads."""

from __future__ import annotations

from typing import Any

from app.services.multi_gpu.catalog import preferred_skus
from app.services.multi_gpu.models import BalanceStrategy, GpuSku, MultiGpuJob
from app.services.multi_gpu.queue import make_job


def resolve_strategy(value: str | None) -> BalanceStrategy:
    v = (value or "capability_match").strip().lower()
    aliases: dict[str, BalanceStrategy] = {
        "least_load": "least_load",
        "least-load": "least_load",
        "load": "least_load",
        "least_queue": "least_queue",
        "least-queue": "least_queue",
        "queue": "least_queue",
        "round_robin": "round_robin",
        "round-robin": "round_robin",
        "rr": "round_robin",
        "capability_match": "capability_match",
        "capability": "capability_match",
        "sku": "capability_match",
    }
    return aliases.get(v, "capability_match")


def jobs_from_scene_render(
    scene_render: dict[str, Any] | None,
    *,
    quality: str = "production",
) -> list[MultiGpuJob]:
    sr = scene_render or {}
    jobs: list[MultiGpuJob] = []
    parent = sr.get("job_id")
    require_rt = bool(sr.get("ray_tracing_ready"))
    gpu_jobs = sr.get("gpu_queue") or []
    scenes = sr.get("scenes") or []

    # Prefer explicit gpu_queue from scene render plan
    sources: list[dict[str, Any]] = []
    if isinstance(gpu_jobs, list) and gpu_jobs and isinstance(gpu_jobs[0], dict):
        sources = list(gpu_jobs)
    elif isinstance(scenes, list):
        for s in scenes:
            if isinstance(s, dict):
                gj = s.get("gpu_job") or {}
                sources.append(
                    {
                        "job_id": gj.get("job_id"),
                        "scene_index": s.get("scene_index"),
                        "priority": gj.get("priority", 100),
                        "estimated_vram_mb": gj.get("estimated_vram_mb", 4096),
                        "estimated_ms": gj.get("estimated_ms", 5000),
                        "quality": gj.get("quality") or quality,
                    }
                )

    if not sources:
        # Single synthetic job from summary
        n = int(sr.get("scenes") or sr.get("gpu_jobs") or 1)
        for i in range(max(1, min(n, 8))):
            sources.append(
                {
                    "scene_index": i,
                    "priority": 10 + i * 10,
                    "estimated_vram_mb": 4096,
                    "estimated_ms": 8000,
                    "quality": quality,
                }
            )

    for src in sources:
        q = str(src.get("quality") or quality)
        vram = int(src.get("estimated_vram_mb") or 4096)
        skus: list[GpuSku] = preferred_skus(
            quality=q, require_rt=require_rt, min_vram_mb=int(vram * 0.8)
        )
        jobs.append(
            make_job(
                kind="scene_render",
                priority=int(src.get("priority") or 100),
                required_vram_mb=vram,
                preferred_skus=skus,
                require_rt=require_rt,
                estimated_ms=int(src.get("estimated_ms") or 5000),
                parent_plan_id=parent,
                scene_index=src.get("scene_index"),
            )
        )
    return jobs


def scene_render_integration(
    scene_render: dict[str, Any] | None,
    assignments: list[dict[str, Any]],
) -> dict[str, Any]:
    sr = scene_render or {}
    return {
        "scene_render_job_id": sr.get("job_id"),
        "ray_tracing_ready": sr.get("ray_tracing_ready"),
        "quality": sr.get("quality"),
        "linked_assignments": [
            {
                "job_id": a.get("job_id"),
                "worker_id": a.get("worker_id"),
                "sku": a.get("sku"),
            }
            for a in assignments
            if a.get("assigned")
        ][:32],
    }
