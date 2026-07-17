"""API for AI Cinematic Environment & World Generation under /api/world."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import world_intelligence as wi
from app.services.character_generation.paddle_status import paddle_status

router = APIRouter(prefix="/world", tags=["world-intelligence"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class WorldCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    world_id: str | None = Field(None, alias="worldId")
    scene_id: str | None = Field(None, alias="sceneId")
    environment: str | None = None
    weather: str | None = None
    time_of_day: str | None = Field(None, alias="timeOfDay")
    mood: str | None = None
    lighting: str | None = None
    story_plan: dict | None = Field(None, alias="storyPlan")
    director_plan: dict | None = Field(None, alias="directorPlan")
    scene_plan: dict | None = Field(None, alias="scenePlan")
    camera_plan: dict | None = Field(None, alias="cameraPlan")
    character_dna: dict | None = Field(None, alias="characterDna")
    motion_plan: dict | None = Field(None, alias="motionPlan")
    emotion_plan: dict | None = Field(None, alias="emotionPlan")
    timeline_plan: dict | None = Field(None, alias="timelinePlan")
    audio_summary: dict | None = Field(None, alias="audioSummary")
    metadata: dict | None = None

    model_config = {"populate_by_name": True}


class WorldGenerateRequest(WorldCreateRequest):
    job_id: str | None = Field(None, alias="jobId")
    prompt: str | None = None  # type: ignore[assignment]


@router.post("/create")
async def create_world(
    body: WorldCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = wi.create_dict(
            prompt=body.prompt,
            world_id=body.world_id,
            scene_id=body.scene_id,
            environment=body.environment,
            weather=body.weather,
            time_of_day=body.time_of_day,
            mood=body.mood,
            lighting=body.lighting,
            story_plan=body.story_plan,
            director_plan=body.director_plan,
            scene_plan=body.scene_plan,
            camera_plan=body.camera_plan,
            character_dna=body.character_dna,
            motion_plan=body.motion_plan,
            emotion_plan=body.emotion_plan,
            timeline_plan=body.timeline_plan,
            audio_summary=body.audio_summary,
            metadata=body.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="World create failed") from exc
    return {"ok": True, **result}


@router.post("/generate")
async def generate_world(
    body: WorldGenerateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        if body.job_id:
            result = wi.generate_dict(job_id=body.job_id)
        else:
            if not body.prompt:
                raise ValueError("prompt is required when jobId is not provided")
            result = wi.generate_dict(
                prompt=body.prompt,
                world_id=body.world_id,
                scene_id=body.scene_id,
                environment=body.environment,
                weather=body.weather,
                time_of_day=body.time_of_day,
                mood=body.mood,
                lighting=body.lighting,
                story_plan=body.story_plan,
                director_plan=body.director_plan,
                scene_plan=body.scene_plan,
                camera_plan=body.camera_plan,
                character_dna=body.character_dna,
                motion_plan=body.motion_plan,
                emotion_plan=body.emotion_plan,
                timeline_plan=body.timeline_plan,
                audio_summary=body.audio_summary,
                metadata=body.metadata,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="World generate failed") from exc
    return {"ok": True, **result}


@router.get("/library")
async def get_world_library(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **wi.world_library_payload()}


@router.get("/history")
async def get_world_history(
    limit: int = Query(50, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **wi.world_history(limit=limit)}


@router.get("/paddle-status")
async def world_paddle_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, "paddle": paddle_status(), "secrets_exposed": False}


@router.get("/{job_id}")
async def get_world_job(
    job_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    payload = wi.get_world(job_id)
    if not payload:
        raise HTTPException(status_code=404, detail="World job not found")
    return {"ok": True, **payload}
