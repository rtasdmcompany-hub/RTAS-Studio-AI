"""API for Complete Audio Production Pipeline under /api/audio-pipeline."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.backend_auth import require_backend_secret
from app.core.config import settings
from app.services import audio_pipeline as pipe

router = APIRouter(prefix="/audio-pipeline", tags=["audio-pipeline"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    require_backend_secret(x_rtas_backend_secret=x_rtas_backend_secret)


class PipelineRunRequest(BaseModel):
    prompt: str = Field(..., min_length=1, max_length=8000)
    platform: str = "youtube"
    language: str = "en"
    target_language: str = Field("ur", alias="targetLanguage")
    duration_sec: float = Field(8.0, alias="durationSec")
    mode: str = "live"  # live | simulation
    enqueue: bool = True
    parent_generation_id: str | None = Field(None, alias="parentGenerationId")
    scenes: list[dict] | None = None
    character_memory: list[dict] | None = Field(None, alias="characterMemory")
    provider: str = "simulation"

    model_config = {"populate_by_name": True}


class StressRequest(BaseModel):
    concurrent: int = Field(8, ge=1, le=32)
    prompt: str = "Stress test cinematic dialogue scene"
    mode: str = "simulation"


@router.get("/release")
async def audio_engine_release(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **pipe.release_manifest(), "engine": pipe.ENGINE_LABEL}


@router.get("/health")
async def audio_pipeline_health(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **pipe.health_payload()}


@router.get("/metrics")
async def audio_pipeline_metrics(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **pipe.metrics_payload()}


@router.post("/run")
async def run_audio_pipeline(
    body: PipelineRunRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = pipe.run_pipeline_dict(
            prompt=body.prompt,
            platform=body.platform,
            language=body.language,
            target_language=body.target_language,
            duration_sec=body.duration_sec,
            mode=body.mode,
            enqueue=body.enqueue,
            parent_generation_id=body.parent_generation_id,
            scenes=body.scenes,
            character_memory=body.character_memory,
            provider=body.provider,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Pipeline run failed") from exc
    return {"ok": True, **result}


@router.get("/job/{job_id}")
async def get_pipeline_job(
    job_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    job = pipe.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Pipeline job not found")
    return {"ok": True, **job.to_dict()}


@router.post("/stress")
async def stress_pipeline(
    body: StressRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    result = pipe.stress_test(
        concurrent=body.concurrent, prompt=body.prompt, mode=body.mode
    )
    return {"ok": True, **result}


@router.get("/regression")
async def regression_pipeline(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **pipe.regression_checklist()}
