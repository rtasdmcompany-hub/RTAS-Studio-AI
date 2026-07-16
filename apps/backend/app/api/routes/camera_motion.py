"""API for Camera Motion Engine (backend only — no UI)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.camera_motion import build_camera_motion_dict, get_plan

router = APIRouter(prefix="/camera-motion", tags=["camera-motion"])


class CameraMotionPlanRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    scenes: list[dict[str, Any]] | None = None
    cameras: list[dict[str, Any]] | None = None
    shots: list[dict[str, Any]] | None = None
    director_plan: dict[str, Any] | None = Field(None, alias="directorPlan")
    scene_breakdown: dict[str, Any] | None = Field(None, alias="sceneBreakdown")
    production_package: dict[str, Any] | None = Field(None, alias="productionPackage")
    prompt_understanding: dict[str, Any] | None = Field(
        None, alias="promptUnderstanding"
    )
    motion_intelligence: dict[str, Any] | None = Field(
        None, alias="motionIntelligence"
    )
    duration_seconds: float | None = Field(None, alias="durationSeconds")
    parent_generation_id: str | None = Field(None, alias="parentGenerationId")

    model_config = {"populate_by_name": True}


@router.post("/plan")
async def plan_camera_motion(body: CameraMotionPlanRequest):
    try:
        result = build_camera_motion_dict(
            body.prompt,
            scenes=body.scenes,
            cameras=body.cameras,
            shots=body.shots,
            director_plan=body.director_plan,
            scene_breakdown=body.scene_breakdown,
            production_package=body.production_package,
            prompt_understanding=body.prompt_understanding,
            motion_intelligence=body.motion_intelligence,
            duration_seconds=body.duration_seconds,
            parent_generation_id=body.parent_generation_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True, **result}


@router.get("/jobs/{job_id}")
async def get_camera_motion_job(job_id: str):
    plan = get_plan(job_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Camera motion plan not found")
    return {"ok": True, "plan": plan.to_dict(), "summary": plan.summary()}
