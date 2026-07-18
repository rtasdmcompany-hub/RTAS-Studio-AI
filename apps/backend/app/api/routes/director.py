"""API for AI Cinematic Director & Auto Filmmaker under /api/director."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import director_intelligence as di
from app.services.character_generation.paddle_status import paddle_status

router = APIRouter(prefix="/director", tags=["director-intelligence"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class DirectorPlanRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    project_id: str | None = Field(None, alias="projectId")
    format_type: str | None = Field(None, alias="formatType")
    genre: str | None = None
    runtime_sec: float | None = Field(None, alias="runtimeSec")
    audience: str | None = None
    characters: list[str] | None = None
    ai_brain: dict | None = Field(None, alias="aiBrain")
    story_plan: dict | None = Field(None, alias="storyPlan")
    character_dna: dict | None = Field(None, alias="characterDna")
    motion_plan: dict | None = Field(None, alias="motionPlan")
    camera_plan: dict | None = Field(None, alias="cameraPlan")
    emotion_plan: dict | None = Field(None, alias="emotionPlan")
    world_plan: dict | None = Field(None, alias="worldPlan")
    audio_summary: dict | None = Field(None, alias="audioSummary")
    timeline_plan: dict | None = Field(None, alias="timelinePlan")
    export_plan: dict | None = Field(None, alias="exportPlan")
    metadata: dict | None = None

    model_config = {"populate_by_name": True}


class DirectorGenerateRequest(DirectorPlanRequest):
    job_id: str | None = Field(None, alias="jobId")
    prompt: str | None = None  # type: ignore[assignment]


@router.post("/plan")
async def plan_director(
    body: DirectorPlanRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = di.plan_dict(
            prompt=body.prompt,
            project_id=body.project_id,
            format_type=body.format_type,
            genre=body.genre,
            runtime_sec=body.runtime_sec,
            audience=body.audience,
            characters=body.characters,
            ai_brain=body.ai_brain,
            story_plan=body.story_plan,
            character_dna=body.character_dna,
            motion_plan=body.motion_plan,
            camera_plan=body.camera_plan,
            emotion_plan=body.emotion_plan,
            world_plan=body.world_plan,
            audio_summary=body.audio_summary,
            timeline_plan=body.timeline_plan,
            export_plan=body.export_plan,
            metadata=body.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Director plan failed") from exc
    return {"ok": True, **result}


@router.post("/generate")
async def generate_director(
    body: DirectorGenerateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        if body.job_id:
            result = di.generate_dict(job_id=body.job_id)
        else:
            if not body.prompt:
                raise ValueError("prompt is required when jobId is not provided")
            result = di.generate_dict(
                prompt=body.prompt,
                project_id=body.project_id,
                format_type=body.format_type,
                genre=body.genre,
                runtime_sec=body.runtime_sec,
                audience=body.audience,
                characters=body.characters,
                ai_brain=body.ai_brain,
                story_plan=body.story_plan,
                character_dna=body.character_dna,
                motion_plan=body.motion_plan,
                camera_plan=body.camera_plan,
                emotion_plan=body.emotion_plan,
                world_plan=body.world_plan,
                audio_summary=body.audio_summary,
                timeline_plan=body.timeline_plan,
                export_plan=body.export_plan,
                metadata=body.metadata,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Director generate failed") from exc
    return {"ok": True, **result}


@router.get("/history")
async def get_director_history(
    limit: int = Query(50, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **di.director_history(limit=limit)}


@router.get("/report")
async def get_director_report(
    limit: int = Query(50, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **di.director_report(limit=limit)}


@router.get("/paddle-status")
async def director_paddle_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, "paddle": paddle_status(), "secrets_exposed": False}


@router.get("/{job_id}")
async def get_director_job(
    job_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    payload = di.get_director(job_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Director job not found")
    return {"ok": True, **payload}
