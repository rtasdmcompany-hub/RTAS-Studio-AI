"""API for Audio Timeline & Cinematic Synchronization under /api/timeline."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import audio_timeline as tl

router = APIRouter(prefix="/timeline", tags=["timeline"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class TimelineCreateRequest(BaseModel):
    fps: float = 24.0
    duration_sec: float | None = Field(None, alias="durationSec")
    scenes: list[dict] | None = None
    shots: list[dict] | None = None
    lip_sync: dict | None = Field(None, alias="lipSync")
    camera_plan: dict | None = Field(None, alias="cameraPlan")
    audio_director: dict | None = Field(None, alias="audioDirector")
    voice_summary: dict | None = Field(None, alias="voiceSummary")
    music_summary: dict | None = Field(None, alias="musicSummary")
    sfx_summary: dict | None = Field(None, alias="sfxSummary")
    ambient_summary: dict | None = Field(None, alias="ambientSummary")
    mix_summary: dict | None = Field(None, alias="mixSummary")
    localization_summary: dict | None = Field(None, alias="localizationSummary")
    bpm: float = 96.0
    snap_enabled: bool = Field(True, alias="snapEnabled")
    auto_align: bool = Field(True, alias="autoAlign")
    locked: bool = False
    provider: str = "simulation"
    enqueue: bool = True
    auto_process: bool = Field(True, alias="autoProcess")
    parent_voice_job_id: str | None = Field(None, alias="parentVoiceJobId")
    parent_music_job_id: str | None = Field(None, alias="parentMusicJobId")
    parent_sfx_job_id: str | None = Field(None, alias="parentSfxJobId")
    parent_mix_job_id: str | None = Field(None, alias="parentMixJobId")
    parent_localization_job_id: str | None = Field(None, alias="parentLocalizationJobId")
    parent_video_job_id: str | None = Field(None, alias="parentVideoJobId")
    parent_generation_id: str | None = Field(None, alias="parentGenerationId")

    model_config = {"populate_by_name": True}


class TimelineSyncRequest(TimelineCreateRequest):
    job_id: str | None = Field(None, alias="jobId")


class TimelineExportRequest(BaseModel):
    job_id: str = Field(..., alias="jobId")

    model_config = {"populate_by_name": True}


def _create_kwargs(body: TimelineCreateRequest) -> dict:
    return {
        "fps": body.fps,
        "duration_sec": body.duration_sec,
        "scenes": body.scenes,
        "shots": body.shots,
        "lip_sync": body.lip_sync,
        "camera_plan": body.camera_plan,
        "audio_director": body.audio_director,
        "voice_summary": body.voice_summary,
        "music_summary": body.music_summary,
        "sfx_summary": body.sfx_summary,
        "ambient_summary": body.ambient_summary,
        "mix_summary": body.mix_summary,
        "localization_summary": body.localization_summary,
        "bpm": body.bpm,
        "snap_enabled": body.snap_enabled,
        "auto_align": body.auto_align,
        "locked": body.locked,
        "provider": body.provider,
        "enqueue": body.enqueue,
        "auto_process": body.auto_process,
        "parent_voice_job_id": body.parent_voice_job_id,
        "parent_music_job_id": body.parent_music_job_id,
        "parent_sfx_job_id": body.parent_sfx_job_id,
        "parent_mix_job_id": body.parent_mix_job_id,
        "parent_localization_job_id": body.parent_localization_job_id,
        "parent_video_job_id": body.parent_video_job_id,
        "parent_generation_id": body.parent_generation_id,
    }


@router.post("/create")
async def create_timeline_endpoint(
    body: TimelineCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = tl.create_timeline_dict(**_create_kwargs(body))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Timeline create failed") from exc
    return {"ok": True, **result}


@router.post("/sync")
async def sync_timeline_endpoint(
    body: TimelineSyncRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = tl.sync_timeline_dict(job_id=body.job_id, **_create_kwargs(body))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Timeline sync failed") from exc
    return {"ok": True, **result}


@router.get("/history")
async def timeline_history(
    limit: int = Query(50, ge=1, le=500),
    parent_generation_id: str | None = Query(None, alias="parentGenerationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {
        "ok": True,
        **tl.history_payload(
            limit=limit, parent_generation_id=parent_generation_id
        ),
    }


@router.get("/{job_id}")
async def get_timeline(
    job_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    job = tl.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Timeline not found")
    return {"ok": True, **job.to_dict()}


@router.post("/export")
async def export_timeline_endpoint(
    body: TimelineExportRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = tl.export_timeline(body.job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Timeline export failed") from exc
    return {"ok": True, **result}
