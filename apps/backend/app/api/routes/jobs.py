"""Job APIs — provider job status + AI Job Orchestration Engine."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import job_orchestration as jo
from app.services.ai_service import LiveGenerationError
from app.services.orchestrator import provider_cancel, provider_status

router = APIRouter(prefix="/jobs", tags=["jobs"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class JobCreateRequest(BaseModel):
    prompt: str = Field(..., min_length=1)
    priority: str = "normal"
    provider: str | None = None
    model: str | None = None
    request_type: str | None = Field(None, alias="requestType")
    depends_on: list[str] | None = Field(None, alias="dependsOn")
    timeout_sec: float | None = Field(None, alias="timeoutSec")
    max_retries: int | None = Field(None, alias="maxRetries")
    metadata: dict | None = None
    auto_process: bool = Field(True, alias="autoProcess")

    model_config = {"populate_by_name": True}


class JobIdRequest(BaseModel):
    job_id: str = Field(..., alias="jobId")

    model_config = {"populate_by_name": True}


# --- Orchestration endpoints (static paths first) ---


@router.post("/create")
async def create_orchestrated_job(
    body: JobCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = jo.create_dict(
            prompt=body.prompt,
            priority=body.priority,  # type: ignore[arg-type]
            provider=body.provider,
            model=body.model,
            request_type=body.request_type,
            depends_on=body.depends_on,
            timeout_sec=body.timeout_sec,
            max_retries=body.max_retries,
            metadata=body.metadata,
            auto_process=body.auto_process,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Job create failed") from exc
    return {"ok": True, **result}


@router.get("/status")
async def orchestrated_jobs_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    jo.pump_scheduler()
    return {"ok": True, **jo.jobs_status()}


@router.get("/history")
async def orchestrated_jobs_history(
    limit: int = Query(50, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **jo.jobs_history(limit=limit)}


@router.post("/cancel")
async def cancel_orchestrated_job(
    body: JobIdRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = jo.cancel_job(body.job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Job cancel failed") from exc
    return {"ok": True, **result}


@router.post("/retry")
async def retry_orchestrated_job(
    body: JobIdRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = jo.retry_job(body.job_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Job retry failed") from exc
    return {"ok": True, **result}


@router.get("/{job_id}")
async def get_orchestrated_job(
    job_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    """Get orchestrated job by id (must not match provider/external pattern with slashes)."""
    _require_backend_auth(x_rtas_backend_secret)
    # Avoid colliding with legacy /{provider}/{external_job_id}/status
    if "/" in job_id:
        raise HTTPException(status_code=404, detail="Job not found")
    payload = jo.get_job(job_id)
    if not payload:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"ok": True, **payload}


# --- Legacy provider job endpoints ---


@router.get("/{provider}/{external_job_id}/status")
async def get_provider_job_status(provider: str, external_job_id: str):
    try:
        status = await provider_status(provider, external_job_id)
    except LiveGenerationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {
        "provider": status.provider,
        "externalJobId": status.external_job_id,
        "status": status.status,
        "progressPercent": status.progress_percent,
        "error": status.error,
        "remoteUrl": status.remote_url,
        "metadata": status.metadata,
    }


@router.post("/{provider}/{external_job_id}/cancel")
async def cancel_provider_job(provider: str, external_job_id: str):
    ok = await provider_cancel(provider, external_job_id)
    if not ok:
        raise HTTPException(
            status_code=409,
            detail="Provider did not accept cancel (unsupported or already terminal)",
        )
    return {"ok": True, "provider": provider, "externalJobId": external_job_id}
