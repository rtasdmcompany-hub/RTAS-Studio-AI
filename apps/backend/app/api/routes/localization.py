"""API for Multi-Language Dubbing & Localization under /api/localization."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import localization as loc

router = APIRouter(prefix="/localization", tags=["localization"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class LocalizationRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=20000)
    source_language: str = Field("en", alias="sourceLanguage")
    target_language: str = Field(..., alias="targetLanguage")
    duration_sec: float | None = Field(None, alias="durationSec")
    accent_profile: str | None = Field(None, alias="accentProfile")
    context: str | None = None
    provider: str = "simulation"
    enqueue: bool = True
    auto_process: bool = Field(True, alias="autoProcess")
    character_memory: list[dict] | None = Field(None, alias="characterMemory")
    voice_summary: dict | None = Field(None, alias="voiceSummary")
    clone_id: str | None = Field(None, alias="cloneId")
    parent_voice_job_id: str | None = Field(None, alias="parentVoiceJobId")
    parent_video_job_id: str | None = Field(None, alias="parentVideoJobId")
    parent_generation_id: str | None = Field(None, alias="parentGenerationId")

    model_config = {"populate_by_name": True}


def _kwargs(body: LocalizationRequest) -> dict:
    return {
        "text": body.text,
        "source_language": body.source_language,
        "target_language": body.target_language,
        "duration_sec": body.duration_sec,
        "accent_profile": body.accent_profile,
        "context": body.context,
        "provider": body.provider,
        "enqueue": body.enqueue,
        "auto_process": body.auto_process,
        "character_memory": body.character_memory,
        "voice_summary": body.voice_summary,
        "clone_id": body.clone_id,
        "parent_voice_job_id": body.parent_voice_job_id,
        "parent_video_job_id": body.parent_video_job_id,
        "parent_generation_id": body.parent_generation_id,
    }


@router.get("/languages")
async def list_localization_languages(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **loc.languages_payload(), "engine": loc.ENGINE_LABEL}


@router.post("/translate")
async def translate_endpoint(
    body: LocalizationRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = loc.translate_dict(**_kwargs(body))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Translation failed") from exc
    return {"ok": True, **result}


@router.post("/dub")
async def dub_endpoint(
    body: LocalizationRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = loc.dub_dict(**_kwargs(body))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Dubbing failed") from exc
    return {"ok": True, **result}


@router.get("/job/{job_id}")
async def get_localization_job(
    job_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    job = loc.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Localization job not found")
    return {
        "ok": True,
        "job": job.to_dict(),
        "summary": job.summary(),
        "history": loc.store.get_job_history(job_id),
        "engine": loc.ENGINE_LABEL,
    }


@router.get("/history")
async def localization_history(
    limit: int = Query(50, ge=1, le=200),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {
        "ok": True,
        "history": loc.store.list_history(limit=limit),
        "queue": loc.localization_queue.status(),
        "engine": loc.ENGINE_LABEL,
    }
