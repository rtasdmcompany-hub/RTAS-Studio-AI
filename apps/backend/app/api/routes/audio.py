"""API for Voice Generation under /api/audio (backend only — no UI)."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services.voice_generation import (
    ENGINE_LABEL,
    generate_voice_dict,
    get_job,
    process_voice_job,
    store,
    voice_queue,
    voices_payload,
)

router = APIRouter(prefix="/audio", tags=["audio-voice"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    """Protect endpoints with existing AI_BACKEND_SECRET when configured."""
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        # Local/dev without secret: allow (matches other engine routes)
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class VoiceGenerateRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=5000)
    language: str | None = "en"
    voice_id: str | None = Field(None, alias="voiceId")
    gender: str | None = "female"
    speed: float = 1.0
    pitch: float = 0.0
    volume: float = 1.0
    pause_ms: int = Field(0, alias="pauseMs")
    pronunciation_hints: dict[str, str] | None = Field(
        None, alias="pronunciationHints"
    )
    provider: str = "simulation"
    enqueue: bool = True
    auto_process: bool = Field(True, alias="autoProcess")
    parent_audio_job_id: str | None = Field(None, alias="parentAudioJobId")
    parent_generation_id: str | None = Field(None, alias="parentGenerationId")

    model_config = {"populate_by_name": True}


@router.get("/voices")
async def list_available_voices(
    language: str | None = Query(None),
    gender: str | None = Query(None),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    payload = voices_payload()
    voices = payload["voices"]
    if language:
        voices = [v for v in voices if v["language"] == language.lower().split("-")[0]]
    if gender:
        voices = [v for v in voices if v["gender"] == gender.lower()]
    return {
        "ok": True,
        "languages": payload["languages"],
        "voices": voices,
        "count": len(voices),
        "engine": ENGINE_LABEL,
    }


@router.post("/generate")
async def generate_voice_audio(
    body: VoiceGenerateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = generate_voice_dict(
            body.text,
            language=body.language,
            voice_id=body.voice_id,
            gender=body.gender,
            speed=body.speed,
            pitch=body.pitch,
            volume=body.volume,
            pause_ms=body.pause_ms,
            pronunciation_hints=body.pronunciation_hints,
            provider=body.provider,
            enqueue=body.enqueue,
            auto_process=body.auto_process,
            parent_audio_job_id=body.parent_audio_job_id,
            parent_generation_id=body.parent_generation_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Voice generation failed") from exc
    return {"ok": True, **result}


@router.get("/job/{job_id}")
async def get_voice_job(
    job_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Voice job not found")
    return {
        "ok": True,
        "job": job.to_dict(),
        "summary": job.summary(),
        "history": store.get_job_history(job_id),
    }


@router.get("/history")
async def voice_history(
    limit: int = Query(50, ge=1, le=200),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {
        "ok": True,
        "history": store.list_history(limit=limit),
        "queue": voice_queue.status(),
    }


@router.post("/job/{job_id}/retry")
async def retry_voice_job(
    job_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    job = voice_queue.retry(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Voice job not found")
    store.put_job(job)
    processed = process_voice_job(job_id) or job
    return {"ok": True, "summary": processed.summary()}


@router.post("/job/{job_id}/cancel")
async def cancel_voice_job(
    job_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    job = voice_queue.cancel(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Voice job not found")
    store.put_job(job)
    return {"ok": True, "summary": job.summary()}
