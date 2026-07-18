"""Production download alias under /api/download → export download package."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import audio_export as ex

router = APIRouter(prefix="/download", tags=["download"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class DownloadRequest(BaseModel):
    job_id: str = Field(..., alias="jobId")
    token: str | None = None

    model_config = {"populate_by_name": True}


@router.post("")
@router.post("/")
async def download_package(
    body: DownloadRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = ex.download_export(body.job_id, token=body.token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Download failed") from exc
    return {"ok": True, **result}


@router.get("/{job_id}")
async def download_by_id(
    job_id: str,
    token: str | None = None,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        result = ex.download_export(job_id, token=token)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Download failed") from exc
    return {"ok": True, **result}
