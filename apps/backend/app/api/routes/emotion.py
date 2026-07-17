"""API for AI Emotion, Expression & Performance under /api/emotion."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import emotion_intelligence as ei
from app.services.character_generation.paddle_status import paddle_status

router = APIRouter(prefix="/emotion", tags=["emotion-intelligence"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class EmotionAnalyzeRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    character_id: str | None = Field(None, alias="characterId")
    dialogue: str | None = None
    story_context: str | None = Field(None, alias="storyContext")
    emotion_hint: str | None = Field(None, alias="emotionHint")
    duration_sec: float | None = Field(None, alias="durationSec")
    director_plan: dict | None = Field(None, alias="directorPlan")
    story_plan: dict | None = Field(None, alias="storyPlan")
    motion_plan: dict | None = Field(None, alias="motionPlan")
    camera_plan: dict | None = Field(None, alias="cameraPlan")
    voice_plan: dict | None = Field(None, alias="voicePlan")
    audio_summary: dict | None = Field(None, alias="audioSummary")
    timeline_plan: dict | None = Field(None, alias="timelinePlan")
    metadata: dict | None = None

    model_config = {"populate_by_name": True}


class EmotionGenerateRequest(EmotionAnalyzeRequest):
    job_id: str | None = Field(None, alias="jobId")
    prompt: str | None = None  # type: ignore[assignment]


@router.post("/analyze")
async def analyze_emotion(
    body: EmotionAnalyzeRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = ei.analyze_dict(
            prompt=body.prompt,
            character_id=body.character_id,
            dialogue=body.dialogue,
            story_context=body.story_context,
            emotion_hint=body.emotion_hint,
            duration_sec=body.duration_sec,
            director_plan=body.director_plan,
            story_plan=body.story_plan,
            motion_plan=body.motion_plan,
            camera_plan=body.camera_plan,
            voice_plan=body.voice_plan,
            audio_summary=body.audio_summary,
            timeline_plan=body.timeline_plan,
            metadata=body.metadata,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Emotion analyze failed") from exc
    return {"ok": True, **result}


@router.post("/generate")
async def generate_emotion(
    body: EmotionGenerateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        if body.job_id:
            result = ei.generate_dict(
                job_id=body.job_id,
                emotion_hint=body.emotion_hint,
            )
        else:
            if not body.prompt:
                raise ValueError("prompt is required when jobId is not provided")
            result = ei.generate_dict(
                prompt=body.prompt,
                character_id=body.character_id,
                dialogue=body.dialogue,
                story_context=body.story_context,
                emotion_hint=body.emotion_hint,
                duration_sec=body.duration_sec,
                director_plan=body.director_plan,
                story_plan=body.story_plan,
                motion_plan=body.motion_plan,
                camera_plan=body.camera_plan,
                voice_plan=body.voice_plan,
                audio_summary=body.audio_summary,
                timeline_plan=body.timeline_plan,
                metadata=body.metadata,
            )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Emotion generate failed") from exc
    return {"ok": True, **result}


@router.get("/library")
async def get_emotion_library(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **ei.emotion_library_payload()}


@router.get("/history")
async def get_emotion_history(
    limit: int = Query(50, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **ei.emotion_history(limit=limit)}


@router.get("/paddle-status")
async def emotion_paddle_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, "paddle": paddle_status(), "secrets_exposed": False}


@router.get("/{job_id}")
async def get_emotion_job(
    job_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    payload = ei.get_emotion(job_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Emotion job not found")
    return {"ok": True, **payload}
