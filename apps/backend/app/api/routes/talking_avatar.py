"""API for Talking Avatar Engine (backend only — no UI)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.talking_avatar import (
    build_talking_avatar_dict,
    get_job,
    get_job_history,
)

router = APIRouter(prefix="/talking-avatar", tags=["talking-avatar"])


class TalkingAvatarPlanRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    dialogue: str | None = None
    emotion: str | None = None
    duration_seconds: float | None = Field(None, alias="durationSeconds")
    reference_face_url: str | None = Field(None, alias="referenceFaceUrl")
    character_memory: list[dict[str, Any]] | None = Field(None, alias="characterMemory")
    director_plan: dict[str, Any] | None = Field(None, alias="directorPlan")
    audio_director: dict[str, Any] | None = Field(None, alias="audioDirector")
    timeline: dict[str, Any] | None = None
    identity_strength: float = Field(0.9, alias="identityStrength")
    natural_motion: bool = Field(True, alias="naturalMotion")
    parent_generation_id: str | None = Field(None, alias="parentGenerationId")
    run_intelligence: bool = Field(False, alias="runIntelligence")

    model_config = {"populate_by_name": True}


@router.post("/plan")
async def plan_talking_avatar(body: TalkingAvatarPlanRequest):
    try:
        character_memory = body.character_memory
        director_plan = body.director_plan
        audio_director = body.audio_director
        timeline = body.timeline
        if body.run_intelligence:
            from app.services.intelligence.pipeline import run_intelligence_pipeline_dict

            plan = run_intelligence_pipeline_dict(
                body.prompt,
                duration_hint=int(body.duration_seconds) if body.duration_seconds else None,
            )
            character_memory = character_memory or plan.get("character_memory")
            director_plan = director_plan or plan.get("director_plan")
            audio_director = audio_director or plan.get("audio_director")
            timeline = timeline or plan.get("timeline")

        result = build_talking_avatar_dict(
            prompt=body.prompt,
            dialogue=body.dialogue,
            emotion_hint=body.emotion,
            duration_hint=body.duration_seconds,
            reference_face_url=body.reference_face_url,
            character_memory=character_memory,
            director_plan=director_plan,
            audio_director=audio_director,
            timeline=timeline,
            identity_strength=body.identity_strength,
            natural_motion=body.natural_motion,
            parent_generation_id=body.parent_generation_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True, **result}


@router.get("/jobs/{job_id}")
async def get_talking_avatar_job(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Talking avatar job not found")
    return {"ok": True, "job": job, "history": get_job_history(job_id)}


@router.get("/jobs/{job_id}/history")
async def get_talking_avatar_history(job_id: str):
    return {"ok": True, "jobId": job_id, "history": get_job_history(job_id)}
