"""Enterprise AI Orchestration Platform APIs — Phase 6 final release."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.backend_auth import require_backend_secret
from app.core.config import settings
from app.services import enterprise_platform as ep

router = APIRouter(prefix="/platform", tags=["enterprise-platform"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    require_backend_secret(x_rtas_backend_secret=x_rtas_backend_secret)


class PlatformValidateRequest(BaseModel):
    prompt: str | None = None

    model_config = {"populate_by_name": True}


class PlatformStressRequest(BaseModel):
    counts: list[int] | None = Field(
        default=None,
        description="Job batch sizes, default [50,100,250,500,1000]",
    )


@router.get("/status")
async def platform_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return ep.get_platform_engine().status()


@router.post("/validate")
async def platform_validate(
    body: PlatformValidateRequest | None = None,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return ep.get_platform_engine().validate(prompt=(body.prompt if body else None))
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Platform validate failed") from exc


@router.get("/quality")
async def platform_quality(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return ep.get_platform_engine().quality_report()


@router.post("/stress")
async def platform_stress(
    body: PlatformStressRequest | None = None,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        counts = body.counts if body else None
        return ep.get_platform_engine().stress_test(counts=counts)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Platform stress failed") from exc


@router.get("/release")
async def platform_release(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return ep.get_platform_engine().release()
