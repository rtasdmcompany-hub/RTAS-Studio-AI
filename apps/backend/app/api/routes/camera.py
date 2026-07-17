"""API for AI Cinematic Camera & Shot Intelligence under /api/camera."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import camera_intelligence as ci
from app.services.character_generation.paddle_status import paddle_status

router = APIRouter(prefix="/camera", tags=["camera-intelligence"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class CameraPlanRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    scene_id: str | None = Field(None, alias="sceneId")
    character_ids: list[str] | None = Field(None, alias="characterIds")
    emotion: str | None = None
    environment: str | None = None
    shot_types: list[str] | None = Field(None, alias="shotTypes")
    preset: str | None = None
    max_shots: int = Field(4, alias="maxShots")
    duration_sec: float | None = Field(None, alias="durationSec")
    director_plan: dict | None = Field(None, alias="directorPlan")
    story_plan: dict | None = Field(None, alias="storyPlan")
    scene_plan: dict | None = Field(None, alias="scenePlan")
    character_dna: dict | None = Field(None, alias="characterDna")
    motion_plan: dict | None = Field(None, alias="motionPlan")
    timeline_plan: dict | None = Field(None, alias="timelinePlan")
    audio_summary: dict | None = Field(None, alias="audioSummary")
    export_plan: dict | None = Field(None, alias="exportPlan")
    metadata: dict | None = None

    model_config = {"populate_by_name": True}


class CameraGenerateRequest(CameraPlanRequest):
    job_id: str | None = Field(None, alias="jobId")
    prompt: str | None = None  # type: ignore[assignment]


@router.post("/plan")
async def plan_camera(
    body: CameraPlanRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = ci.plan_dict(
            prompt=body.prompt,
            scene_id=body.scene_id,
            character_ids=body.character_ids,
            emotion=body.emotion,
            environment=body.environment,
            shot_types=body.shot_types,
            preset=body.preset,
            max_shots=body.max_shots,
            duration_sec=body.duration_sec,
            director_plan=body.director_plan,
            story_plan=body.story_plan,
            scene_plan=body.scene_plan,
            character_dna=body.character_dna,
            motion_plan=body.motion_plan,
            timeline_plan=body.timeline_plan,
            audio_summary=body.audio_summary,
            export_plan=body.export_plan,
            metadata=body.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Camera plan failed") from exc
    return {"ok": True, **result}


@router.post("/generate")
async def generate_camera(
    body: CameraGenerateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        if body.job_id:
            result = ci.generate_dict(job_id=body.job_id)
        else:
            if not body.prompt:
                raise ValueError("prompt is required when jobId is not provided")
            result = ci.generate_dict(
                prompt=body.prompt,
                scene_id=body.scene_id,
                character_ids=body.character_ids,
                emotion=body.emotion,
                environment=body.environment,
                shot_types=body.shot_types,
                preset=body.preset,
                max_shots=body.max_shots,
                duration_sec=body.duration_sec,
                director_plan=body.director_plan,
                story_plan=body.story_plan,
                scene_plan=body.scene_plan,
                character_dna=body.character_dna,
                motion_plan=body.motion_plan,
                timeline_plan=body.timeline_plan,
                audio_summary=body.audio_summary,
                export_plan=body.export_plan,
                metadata=body.metadata,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Camera generate failed") from exc
    return {"ok": True, **result}


@router.get("/library")
async def get_camera_library(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **ci.camera_library_payload()}


@router.get("/history")
async def get_camera_history(
    limit: int = Query(50, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **ci.camera_history(limit=limit)}


@router.get("/paddle-status")
async def camera_paddle_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, "paddle": paddle_status(), "secrets_exposed": False}


@router.get("/{job_id}")
async def get_camera_job(
    job_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    payload = ci.get_camera(job_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Camera job not found")
    return {"ok": True, **payload}
