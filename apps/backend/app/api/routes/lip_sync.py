"""API for Professional Lip Sync Engine (backend only — no UI)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.lip_sync import build_lip_sync_dict, get_plan

router = APIRouter(prefix="/lip-sync", tags=["lip-sync"])


class LipSyncPlanRequest(BaseModel):
    dialogue: str = Field(..., min_length=1)
    language: str | None = None
    emotion: str | None = None
    duration_seconds: float | None = Field(None, alias="durationSeconds")
    start_sec: float = Field(0.0, alias="startSec")
    character_id: str | None = Field(None, alias="characterId")
    audio_director: dict[str, Any] | None = Field(None, alias="audioDirector")
    voice_timeline: list[dict[str, Any]] | None = Field(None, alias="voiceTimeline")

    model_config = {"populate_by_name": True}


@router.post("/plan")
async def plan_lip_sync(body: LipSyncPlanRequest):
    try:
        result = build_lip_sync_dict(
            body.dialogue,
            language_hint=body.language,
            emotion_hint=body.emotion,
            duration_seconds=body.duration_seconds,
            start_sec=body.start_sec,
            character_id=body.character_id,
            audio_director=body.audio_director,
            voice_timeline=body.voice_timeline,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    return {"ok": True, **result}


@router.get("/jobs/{job_id}")
async def get_lip_sync_job(job_id: str):
    plan = get_plan(job_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Lip sync plan not found")
    return {"ok": True, "plan": plan.to_dict(), "summary": plan.summary()}
