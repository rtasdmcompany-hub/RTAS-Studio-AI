"""API for Multi GPU Engine (backend only — no UI)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.multi_gpu import (
    build_multi_gpu_dict,
    complete_job,
    distribute_pending,
    get_job,
    get_plan,
    heartbeat,
    list_workers,
    queue_status,
)

router = APIRouter(prefix="/multi-gpu", tags=["multi-gpu"])


class MultiGpuPlanRequest(BaseModel):
    scene_render: dict[str, Any] | None = Field(None, alias="sceneRender")
    jobs: list[dict[str, Any]] | None = None
    strategy: str | None = None
    quality: str = "production"
    seed_fleet: bool = Field(True, alias="seedFleet")
    distribute: bool = True
    parent_generation_id: str | None = Field(None, alias="parentGenerationId")
    prompt: str | None = None

    model_config = {"populate_by_name": True}


class HeartbeatRequest(BaseModel):
    state: str | None = None
    active_jobs: int | None = Field(None, alias="activeJobs")
    queued_jobs: int | None = Field(None, alias="queuedJobs")
    vram_free_mb: int | None = Field(None, alias="vramFreeMb")
    load: float | None = None

    model_config = {"populate_by_name": True}


class CompleteRequest(BaseModel):
    success: bool = True
    error: str | None = None


@router.post("/plan")
async def plan_multi_gpu(body: MultiGpuPlanRequest):
    try:
        result = build_multi_gpu_dict(
            scene_render=body.scene_render,
            jobs=body.jobs,
            strategy=body.strategy,
            quality=body.quality,
            seed_fleet=body.seed_fleet,
            distribute=body.distribute,
            parent_generation_id=body.parent_generation_id,
            prompt=body.prompt,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True, **result}


@router.get("/plans/{job_id}")
async def get_multi_gpu_plan(job_id: str):
    plan = get_plan(job_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Multi GPU plan not found")
    return {"ok": True, "plan": plan.to_dict(), "summary": plan.summary()}


@router.get("/workers")
async def get_workers():
    return {"ok": True, "workers": [w.to_dict() for w in list_workers()]}


@router.post("/workers/{worker_id}/heartbeat")
async def worker_heartbeat(worker_id: str, body: HeartbeatRequest):
    w = heartbeat(
        worker_id,
        state=body.state,  # type: ignore[arg-type]
        active_jobs=body.active_jobs,
        queued_jobs=body.queued_jobs,
        vram_free_mb=body.vram_free_mb,
        load=body.load,
    )
    if not w:
        raise HTTPException(status_code=404, detail="Worker not found")
    return {"ok": True, "worker": w.to_dict()}


@router.get("/queue")
async def get_queue():
    return {"ok": True, **queue_status()}


@router.post("/distribute")
async def do_distribute(strategy: str = "capability_match", max_jobs: int = 16):
    assignments = distribute_pending(strategy=strategy, max_jobs=max_jobs)  # type: ignore[arg-type]
    return {"ok": True, "assignments": assignments}


@router.get("/jobs/{job_id}")
async def get_mgpu_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"ok": True, "job": job.to_dict()}


@router.post("/jobs/{job_id}/complete")
async def complete_mgpu_job(job_id: str, body: CompleteRequest):
    job = complete_job(job_id, success=body.success, error=body.error)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"ok": True, "job": job.to_dict()}
