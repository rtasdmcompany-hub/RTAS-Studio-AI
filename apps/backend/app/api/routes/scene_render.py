"""API for Scene Render Engine (backend only — no UI)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.scene_render import (
    build_scene_render_dict,
    complete_gpu_job,
    dequeue_gpu_job,
    get_gpu_job,
    get_plan,
    queue_status,
)

router = APIRouter(prefix="/scene-render", tags=["scene-render"])


class SceneRenderPlanRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    scenes: list[dict[str, Any]] | None = None
    cameras: list[dict[str, Any]] | None = None
    director_plan: dict[str, Any] | None = Field(None, alias="directorPlan")
    scene_breakdown: dict[str, Any] | None = Field(None, alias="sceneBreakdown")
    production_package: dict[str, Any] | None = Field(None, alias="productionPackage")
    production_render: dict[str, Any] | None = Field(None, alias="productionRender")
    prompt_understanding: dict[str, Any] | None = Field(
        None, alias="promptUnderstanding"
    )
    visual_style: dict[str, Any] | None = Field(None, alias="visualStyle")
    physics: dict[str, Any] | None = None
    camera_motion: dict[str, Any] | None = Field(None, alias="cameraMotion")
    quality: str | None = None
    duration_seconds: float | None = Field(None, alias="durationSeconds")
    enqueue_gpu: bool = Field(True, alias="enqueueGpu")
    parent_generation_id: str | None = Field(None, alias="parentGenerationId")

    model_config = {"populate_by_name": True}


@router.post("/plan")
async def plan_scene_render(body: SceneRenderPlanRequest):
    try:
        result = build_scene_render_dict(
            body.prompt,
            scenes=body.scenes,
            cameras=body.cameras,
            director_plan=body.director_plan,
            scene_breakdown=body.scene_breakdown,
            production_package=body.production_package,
            production_render=body.production_render,
            prompt_understanding=body.prompt_understanding,
            visual_style=body.visual_style,
            physics=body.physics,
            camera_motion=body.camera_motion,
            quality=body.quality,
            duration_seconds=body.duration_seconds,
            enqueue_gpu=body.enqueue_gpu,
            parent_generation_id=body.parent_generation_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True, **result}


@router.get("/jobs/{job_id}")
async def get_scene_render_job(job_id: str):
    plan = get_plan(job_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Scene render plan not found")
    return {"ok": True, "plan": plan.to_dict(), "summary": plan.summary()}


@router.get("/gpu/queue")
async def get_gpu_queue():
    return {"ok": True, **queue_status()}


@router.post("/gpu/dequeue")
async def gpu_dequeue():
    job = dequeue_gpu_job()
    if not job:
        return {"ok": True, "job": None}
    return {"ok": True, "job": job.to_dict()}


@router.post("/gpu/jobs/{job_id}/complete")
async def gpu_complete(job_id: str, failed: bool = False):
    job = complete_gpu_job(job_id, failed=failed)
    if not job:
        raise HTTPException(status_code=404, detail="GPU job not found")
    return {"ok": True, "job": job.to_dict()}


@router.get("/gpu/jobs/{job_id}")
async def gpu_get(job_id: str):
    job = get_gpu_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="GPU job not found")
    return {"ok": True, "job": job.to_dict()}
