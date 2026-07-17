"""API for RTAS Studio AI Video Engine v1.0 (backend only — no UI)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.video_engine import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    build_video_engine_dict,
    get_plan,
)

router = APIRouter(prefix="/video-engine", tags=["video-engine"])


class VideoEnginePlanRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    intelligence: dict[str, Any] | None = None
    director_plan: dict[str, Any] | None = Field(None, alias="directorPlan")
    scenes: list[dict[str, Any]] | None = None
    shots: list[dict[str, Any]] | None = None
    cameras: list[dict[str, Any]] | None = None
    character_memory: list[dict[str, Any]] | None = Field(None, alias="characterMemory")
    cinematic_quality: dict[str, Any] | None = Field(None, alias="cinematicQuality")
    character_consistency: dict[str, Any] | None = Field(
        None, alias="characterConsistency"
    )
    production_render: dict[str, Any] | None = Field(None, alias="productionRender")
    scene_render: dict[str, Any] | None = Field(None, alias="sceneRender")
    camera_motion: dict[str, Any] | None = Field(None, alias="cameraMotion")
    physics: dict[str, Any] | None = None
    multi_gpu: dict[str, Any] | None = Field(None, alias="multiGpu")
    text_to_video: dict[str, Any] | None = Field(None, alias="textToVideo")
    auto_retry: bool = Field(True, alias="autoRetry")
    run_stress: bool = Field(False, alias="runStress")
    stress_iterations: int = Field(3, alias="stressIterations")
    parent_generation_id: str | None = Field(None, alias="parentGenerationId")

    model_config = {"populate_by_name": True}


@router.get("/version")
async def version():
    return {
        "ok": True,
        "engine": ENGINE_NAME,
        "version": ENGINE_VERSION,
        "label": ENGINE_LABEL,
    }


@router.post("/plan")
async def plan_video_engine(body: VideoEnginePlanRequest):
    try:
        result = build_video_engine_dict(
            body.prompt,
            intelligence=body.intelligence,
            director_plan=body.director_plan,
            scenes=body.scenes,
            shots=body.shots,
            cameras=body.cameras,
            character_memory=body.character_memory,
            cinematic_quality=body.cinematic_quality,
            character_consistency=body.character_consistency,
            production_render=body.production_render,
            scene_render=body.scene_render,
            camera_motion=body.camera_motion,
            physics=body.physics,
            multi_gpu=body.multi_gpu,
            text_to_video=body.text_to_video,
            auto_retry=body.auto_retry,
            run_stress=body.run_stress,
            stress_iterations=body.stress_iterations,
            parent_generation_id=body.parent_generation_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True, **result}


@router.get("/jobs/{job_id}")
async def get_video_engine_job(job_id: str):
    plan = get_plan(job_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Video engine plan not found")
    return {"ok": True, "plan": plan.to_dict(), "summary": plan.summary()}


@router.get("/download/{job_id}")
async def download_hint(job_id: str):
    plan = get_plan(job_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Video engine plan not found")
    return {
        "ok": True,
        "ready": plan.download.ready,
        "download": plan.download.to_dict(),
        "production_ready": plan.production_ready,
        "engine": ENGINE_LABEL,
    }
