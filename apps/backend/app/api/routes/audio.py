"""API for Voice Generation + Cloning under /api/audio (backend only — no UI)."""

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
from app.services import voice_cloning as vc

router = APIRouter(prefix="/audio", tags=["audio-voice"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> bool:
    """Protect endpoints with existing AI_BACKEND_SECRET when configured."""
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        # Local/dev without secret: allow (matches other engine routes)
        return True
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")
    return True


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


# ---------------------------------------------------------------------------
# Phase 4 Sprint 3 — Voice Cloning & Character Voice
# ---------------------------------------------------------------------------


class VoiceCloneRequest(BaseModel):
    reference_url: str = Field(..., alias="referenceUrl", min_length=1, max_length=2000)
    owner_id: str | None = Field(None, alias="ownerId")
    character_id: str | None = Field(None, alias="characterId")
    language: str = "en"
    accent: str = "neutral"
    speaking_style: str = Field("natural", alias="speakingStyle")
    emotion_profile: str = Field("calm", alias="emotionProfile")
    gender: str = "unspecified"
    age_group: str | None = Field(None, alias="ageGroup")
    duration_sec: float | None = Field(None, alias="durationSec")
    sample_rate: int | None = Field(None, alias="sampleRate")
    file_type: str | None = Field(None, alias="fileType")
    mime_type: str | None = Field(None, alias="mimeType")
    quality_hint: float | None = Field(None, alias="qualityHint")
    lock_voice: bool = Field(False, alias="lockVoice")
    provider: str = "simulation"
    enqueue: bool = True
    auto_process: bool = Field(True, alias="autoProcess")
    parent_generation_id: str | None = Field(None, alias="parentGenerationId")
    parent_video_job_id: str | None = Field(None, alias="parentVideoJobId")
    signature: str | None = None

    model_config = {"populate_by_name": True}


class VoiceTrainRequest(BaseModel):
    clone_id: str = Field(..., alias="cloneId")
    reference_url: str | None = Field(None, alias="referenceUrl")
    owner_id: str | None = Field(None, alias="ownerId")
    auto_process: bool = Field(True, alias="autoProcess")
    signature: str | None = None

    model_config = {"populate_by_name": True}


class CharacterAssignRequest(BaseModel):
    character_id: str = Field(..., alias="characterId")
    clone_id: str = Field(..., alias="cloneId")
    lock: bool = True
    language: str | None = None
    accent: str | None = None
    speaking_style: str | None = Field(None, alias="speakingStyle")
    emotion_profile: str | None = Field(None, alias="emotionProfile")
    gender: str | None = None
    age_group: str | None = Field(None, alias="ageGroup")
    owner_id: str | None = Field(None, alias="ownerId")

    model_config = {"populate_by_name": True}


def _check_optional_signature(payload: str, signature: str | None) -> None:
    secret = (settings.ai_backend_secret or "").strip()
    if not secret:
        return
    if signature and not vc.verify_signature(payload, signature, secret):
        raise HTTPException(status_code=401, detail="Invalid request signature")


@router.post("/clone")
async def clone_voice_endpoint(
    body: VoiceCloneRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    _check_optional_signature(body.reference_url, body.signature)
    try:
        result = vc.clone_voice_dict(
            body.reference_url,
            owner_id=body.owner_id,
            character_id=body.character_id,
            language=body.language,
            accent=body.accent,
            speaking_style=body.speaking_style,
            emotion_profile=body.emotion_profile,
            gender=body.gender,
            age_group=body.age_group,
            duration_sec=body.duration_sec,
            sample_rate=body.sample_rate,
            file_type=body.file_type,
            mime_type=body.mime_type,
            quality_hint=body.quality_hint,
            lock_voice=body.lock_voice,
            provider=body.provider,
            enqueue=body.enqueue,
            auto_process=body.auto_process,
            parent_generation_id=body.parent_generation_id,
            parent_video_job_id=body.parent_video_job_id,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Voice clone failed") from exc
    return {"ok": True, **result}


@router.post("/train")
async def train_voice_endpoint(
    body: VoiceTrainRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    _check_optional_signature(body.clone_id, body.signature)
    try:
        job = vc.retrain_clone(
            body.clone_id,
            reference_url=body.reference_url,
            owner_id=body.owner_id,
            auto_process=body.auto_process,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Voice train failed") from exc
    return {
        "ok": True,
        "clone": job.to_dict(),
        "summary": job.summary(),
        "engine": vc.ENGINE_LABEL,
    }


@router.get("/clone/{clone_id}")
async def get_clone_endpoint(
    clone_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    job = vc.get_clone(clone_id)
    if not job:
        raise HTTPException(status_code=404, detail="Voice clone not found")
    return {
        "ok": True,
        "clone": job.to_dict(),
        "summary": job.summary(),
        "history": vc.store.get_clone_history(clone_id),
        "preview": {
            "preview_url": job.preview_url,
            "asset_url": job.asset_url,
        },
    }


@router.get("/character/{character_id}")
async def get_character_voice(
    character_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    profile = vc.store.get_character(character_id)
    if not profile:
        # Lazy restore from bare character id
        profile = vc.profile_from_character_memory({"character_id": character_id})
    return {
        "ok": True,
        "character": profile.to_dict(),
        "restore": profile.restore_voice_kwargs(),
        "engine": vc.ENGINE_LABEL,
    }


@router.post("/character/assign")
async def assign_character_voice(
    body: CharacterAssignRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    clone = vc.get_clone(body.clone_id)
    if not clone:
        raise HTTPException(status_code=404, detail="Voice clone not found")
    try:
        profile = vc.assign_clone_to_character(
            body.character_id,
            body.clone_id,
            lock=body.lock,
            language=body.language,
            accent=body.accent,
            speaking_style=body.speaking_style,
            emotion_profile=body.emotion_profile,
            gender=body.gender,
            age_group=body.age_group,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Character assign failed") from exc
    return {"ok": True, "character": profile.to_dict(), "restore": profile.restore_voice_kwargs()}


@router.get("/voices/history")
async def voices_clone_history(
    limit: int = Query(50, ge=1, le=200),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {
        "ok": True,
        "history": vc.store.list_clone_history(limit=limit),
        "queue": vc.clone_queue.status(),
        "audit": vc.list_audit(limit=min(limit, 50)),
        "engine": vc.ENGINE_LABEL,
    }
