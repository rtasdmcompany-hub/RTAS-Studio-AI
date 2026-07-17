"""API for Music Generation under /api/music (backend only — no UI)."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import music_generation as mg

router = APIRouter(prefix="/music", tags=["music-generation"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class MusicGenerateRequest(BaseModel):
    genre: str | None = None
    role: str | None = "background"
    title: str | None = None
    bpm: int | None = None
    key: str | None = None
    mood: str | None = None
    energy: float | None = None
    intensity: float | None = None
    duration_sec: float | None = Field(None, alias="durationSec")
    instruments: list[str] | None = None
    loop: bool | None = None
    fade_in_sec: float | None = Field(None, alias="fadeInSec")
    fade_out_sec: float | None = Field(None, alias="fadeOutSec")
    provider: str = "simulation"
    enqueue: bool = True
    auto_process: bool = Field(True, alias="autoProcess")
    prompt: str | None = None
    parent_audio_job_id: str | None = Field(None, alias="parentAudioJobId")
    parent_video_job_id: str | None = Field(None, alias="parentVideoJobId")
    parent_generation_id: str | None = Field(None, alias="parentGenerationId")
    scene_emotion: str | None = Field(None, alias="sceneEmotion")
    scene_duration_sec: float | None = Field(None, alias="sceneDurationSec")
    camera_motion: str | None = Field(None, alias="cameraMotion")
    story_beat: str | None = Field(None, alias="storyBeat")
    audio_director: dict | None = Field(None, alias="audioDirector")
    video_engine: dict | None = Field(None, alias="videoEngine")
    director: dict | None = None
    scenes: list[dict] | None = None
    character_memory: list[dict] | None = Field(None, alias="characterMemory")

    model_config = {"populate_by_name": True}


@router.get("/library")
async def music_library(
    genre: str | None = Query(None),
    role: str | None = Query(None),
    limit: int = Query(100, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    payload = mg.library_payload(genre=genre, role=role, limit=limit)
    return {"ok": True, **payload, "engine": mg.ENGINE_LABEL}


@router.post("/generate")
async def generate_music_endpoint(
    body: MusicGenerateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = mg.generate_music_dict(
            genre=body.genre,
            role=body.role,
            title=body.title,
            bpm=body.bpm,
            key=body.key,
            mood=body.mood,
            energy=body.energy,
            intensity=body.intensity,
            duration_sec=body.duration_sec,
            instruments=body.instruments,
            loop=body.loop,
            fade_in_sec=body.fade_in_sec,
            fade_out_sec=body.fade_out_sec,
            provider=body.provider,
            enqueue=body.enqueue,
            auto_process=body.auto_process,
            prompt=body.prompt,
            parent_audio_job_id=body.parent_audio_job_id,
            parent_video_job_id=body.parent_video_job_id,
            parent_generation_id=body.parent_generation_id,
            scene_emotion=body.scene_emotion,
            scene_duration_sec=body.scene_duration_sec,
            camera_motion=body.camera_motion,
            story_beat=body.story_beat,
            audio_director=body.audio_director,
            video_engine=body.video_engine,
            director=body.director,
            scenes=body.scenes,
            character_memory=body.character_memory,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Music generation failed") from exc
    return {"ok": True, **result}


@router.get("/job/{job_id}")
async def get_music_job(
    job_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    job = mg.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Music job not found")
    return {
        "ok": True,
        "job": job.to_dict(),
        "summary": job.summary(),
        "history": mg.store.get_job_history(job_id),
    }


@router.get("/history")
async def music_history(
    limit: int = Query(50, ge=1, le=200),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {
        "ok": True,
        "history": mg.store.list_history(limit=limit),
        "queue": mg.music_queue.status(),
        "engine": mg.ENGINE_LABEL,
    }


@router.get("/version")
async def music_version(
    job_id: str | None = Query(None, alias="jobId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **mg.version_payload(job_id)}


@router.post("/job/{job_id}/retry")
async def retry_music_job(
    job_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    job = mg.music_queue.retry(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Music job not found")
    mg.store.put_job(job)
    processed = mg.process_music_job(job_id) or job
    return {"ok": True, "summary": processed.summary()}


@router.post("/job/{job_id}/cancel")
async def cancel_music_job(
    job_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    job = mg.music_queue.cancel(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Music job not found")
    mg.store.put_job(job)
    return {"ok": True, "summary": job.summary()}
