"""API for Physics Engine (backend only — no UI)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.physics import build_physics_dict, get_plan

router = APIRouter(prefix="/physics", tags=["physics"])


class PhysicsPlanRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    scenes: list[dict[str, Any]] | None = None
    director_plan: dict[str, Any] | None = Field(None, alias="directorPlan")
    scene_breakdown: dict[str, Any] | None = Field(None, alias="sceneBreakdown")
    production_package: dict[str, Any] | None = Field(None, alias="productionPackage")
    prompt_understanding: dict[str, Any] | None = Field(
        None, alias="promptUnderstanding"
    )
    motion_intelligence: dict[str, Any] | None = Field(
        None, alias="motionIntelligence"
    )
    character_memory: list[dict[str, Any]] | None = Field(
        None, alias="characterMemory"
    )
    duration_seconds: float | None = Field(None, alias="durationSeconds")
    parent_generation_id: str | None = Field(None, alias="parentGenerationId")

    model_config = {"populate_by_name": True}


@router.post("/plan")
async def plan_physics(body: PhysicsPlanRequest):
    try:
        result = build_physics_dict(
            body.prompt,
            scenes=body.scenes,
            director_plan=body.director_plan,
            scene_breakdown=body.scene_breakdown,
            production_package=body.production_package,
            prompt_understanding=body.prompt_understanding,
            motion_intelligence=body.motion_intelligence,
            character_memory=body.character_memory,
            duration_seconds=body.duration_seconds,
            parent_generation_id=body.parent_generation_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True, **result}


@router.get("/jobs/{job_id}")
async def get_physics_job(job_id: str):
    plan = get_plan(job_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Physics plan not found")
    return {"ok": True, "plan": plan.to_dict(), "summary": plan.summary()}
