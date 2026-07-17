"""API for Audio Export, Delivery & Distribution under /api/export."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import audio_export as ex

router = APIRouter(prefix="/export", tags=["export"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class ExportCreateRequest(BaseModel):
    platform: str = "youtube"
    quality: str = "high"
    formats: list[str] | None = None
    watermark: bool = False
    duration_sec: float | None = Field(None, alias="durationSec")
    expire_hours: float = Field(24.0, alias="expireHours")
    batch_id: str | None = Field(None, alias="batchId")
    platforms: list[str] | None = None  # batch
    include_subtitles: bool = Field(True, alias="includeSubtitles")
    include_captions: bool = Field(True, alias="includeCaptions")
    include_thumbnail: bool = Field(True, alias="includeThumbnail")
    provider: str = "simulation"
    enqueue: bool = True
    auto_process: bool = Field(True, alias="autoProcess")
    timeline_summary: dict | None = Field(None, alias="timelineSummary")
    localization_summary: dict | None = Field(None, alias="localizationSummary")
    video_summary: dict | None = Field(None, alias="videoSummary")
    mix_summary: dict | None = Field(None, alias="mixSummary")
    character_memory: list[dict] | None = Field(None, alias="characterMemory")
    parent_timeline_job_id: str | None = Field(None, alias="parentTimelineJobId")
    parent_video_job_id: str | None = Field(None, alias="parentVideoJobId")
    parent_localization_job_id: str | None = Field(None, alias="parentLocalizationJobId")
    parent_mix_job_id: str | None = Field(None, alias="parentMixJobId")
    parent_generation_id: str | None = Field(None, alias="parentGenerationId")

    model_config = {"populate_by_name": True}


class ExportDownloadRequest(BaseModel):
    job_id: str = Field(..., alias="jobId")
    token: str | None = None

    model_config = {"populate_by_name": True}


class ExportPackageRequest(ExportCreateRequest):
    pass


def _create_kwargs(body: ExportCreateRequest) -> dict:
    return {
        "platform": body.platform,
        "quality": body.quality,
        "formats": body.formats,
        "watermark": body.watermark,
        "duration_sec": body.duration_sec,
        "expire_hours": body.expire_hours,
        "batch_id": body.batch_id,
        "include_subtitles": body.include_subtitles,
        "include_captions": body.include_captions,
        "include_thumbnail": body.include_thumbnail,
        "provider": body.provider,
        "enqueue": body.enqueue,
        "auto_process": body.auto_process,
        "timeline_summary": body.timeline_summary,
        "localization_summary": body.localization_summary,
        "video_summary": body.video_summary,
        "mix_summary": body.mix_summary,
        "character_memory": body.character_memory,
        "parent_timeline_job_id": body.parent_timeline_job_id,
        "parent_video_job_id": body.parent_video_job_id,
        "parent_localization_job_id": body.parent_localization_job_id,
        "parent_mix_job_id": body.parent_mix_job_id,
        "parent_generation_id": body.parent_generation_id,
    }


@router.get("/profiles")
async def list_export_profiles(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **ex.profiles_payload(), "engine": ex.ENGINE_LABEL}


@router.post("/create")
async def create_export_endpoint(
    body: ExportCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        if body.platforms:
            jobs = ex.create_batch_exports(body.platforms, **_create_kwargs(body))
            return {
                "ok": True,
                "batch": True,
                "batch_id": jobs[0].batch_id if jobs else body.batch_id,
                "jobs": [j.to_dict() for j in jobs],
                "count": len(jobs),
            }
        result = ex.create_export_dict(**_create_kwargs(body))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Export create failed") from exc
    return {"ok": True, **result}


@router.post("/package")
async def package_export_endpoint(
    body: ExportPackageRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = ex.package_export_dict(**_create_kwargs(body))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Export package failed") from exc
    return {"ok": True, **result}


@router.post("/download")
async def download_export_endpoint(
    body: ExportDownloadRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = ex.download_export(body.job_id, token=body.token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Export download failed") from exc
    return {"ok": True, **result}


@router.get("/history")
async def export_history(
    limit: int = Query(50, ge=1, le=500),
    parent_generation_id: str | None = Query(None, alias="parentGenerationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {
        "ok": True,
        **ex.history_payload(
            limit=limit, parent_generation_id=parent_generation_id
        ),
    }


@router.get("/job/{job_id}")
async def get_export_job(
    job_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    job = ex.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Export job not found")
    return {"ok": True, **job.to_dict()}
