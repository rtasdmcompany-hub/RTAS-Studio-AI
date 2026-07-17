"""API for AI Character Motion & Cinematic Animation under /api/motion."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import character_motion as cm
from app.services.character_generation.paddle_status import paddle_status

router = APIRouter(prefix="/motion", tags=["character-motion"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class MotionCreateRequest(BaseModel):
    character_id: str | None = Field(None, alias="characterId")
    actions: list[str] | None = None
    action: str | None = None
    emotion: str | None = None
    duration_sec: float | None = Field(None, alias="durationSec")
    profile_overrides: dict | None = Field(None, alias="profileOverrides")
    director_plan: dict | None = Field(None, alias="directorPlan")
    scene_plan: dict | None = Field(None, alias="scenePlan")
    camera_plan: dict | None = Field(None, alias="cameraPlan")
    timeline_plan: dict | None = Field(None, alias="timelinePlan")
    audio_summary: dict | None = Field(None, alias="audioSummary")
    metadata: dict | None = None

    model_config = {"populate_by_name": True}


class MotionGenerateRequest(BaseModel):
    job_id: str | None = Field(None, alias="jobId")
    character_id: str | None = Field(None, alias="characterId")
    actions: list[str] | None = None
    action: str | None = None
    emotion: str | None = None
    duration_sec: float | None = Field(None, alias="durationSec")
    profile_overrides: dict | None = Field(None, alias="profileOverrides")
    director_plan: dict | None = Field(None, alias="directorPlan")
    scene_plan: dict | None = Field(None, alias="scenePlan")
    camera_plan: dict | None = Field(None, alias="cameraPlan")
    timeline_plan: dict | None = Field(None, alias="timelinePlan")
    audio_summary: dict | None = Field(None, alias="audioSummary")
    metadata: dict | None = None

    model_config = {"populate_by_name": True}


@router.post("/create")
async def create_motion(
    body: MotionCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = cm.create_dict(
            character_id=body.character_id,
            actions=body.actions,
            action=body.action,
            emotion=body.emotion,
            duration_sec=body.duration_sec,
            profile_overrides=body.profile_overrides,
            director_plan=body.director_plan,
            scene_plan=body.scene_plan,
            camera_plan=body.camera_plan,
            timeline_plan=body.timeline_plan,
            audio_summary=body.audio_summary,
            metadata=body.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Motion create failed") from exc
    return {"ok": True, **result}


@router.post("/generate")
async def generate_motion(
    body: MotionGenerateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = cm.generate_dict(
            job_id=body.job_id,
            character_id=body.character_id,
            actions=body.actions,
            action=body.action,
            emotion=body.emotion,
            duration_sec=body.duration_sec,
            profile_overrides=body.profile_overrides,
            director_plan=body.director_plan,
            scene_plan=body.scene_plan,
            camera_plan=body.camera_plan,
            timeline_plan=body.timeline_plan,
            audio_summary=body.audio_summary,
            metadata=body.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Motion generate failed") from exc
    return {"ok": True, **result}


@router.get("/library")
async def get_motion_library(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **cm.motion_library_payload()}


@router.get("/history")
async def get_motion_history(
    limit: int = Query(50, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **cm.motion_history(limit=limit)}


@router.get("/paddle-status")
async def motion_paddle_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, "paddle": paddle_status(), "secrets_exposed": False}


@router.get("/{job_id}")
async def get_motion_job(
    job_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    payload = cm.get_motion(job_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Motion job not found")
    return {"ok": True, **payload}
