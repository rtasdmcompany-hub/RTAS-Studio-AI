"""System monitoring / observability / self-healing APIs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import monitoring_observability as mo

router = APIRouter(prefix="/system", tags=["monitoring-observability"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


class RecoveryRequest(BaseModel):
    actions: list[str] | None = None
    component: str | None = None
    job_ids: list[str] | None = Field(None, alias="jobIds")

    model_config = {"populate_by_name": True}


@router.get("/health")
async def system_health(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return mo.get_monitoring_engine().health()


@router.get("/metrics")
async def system_metrics(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return mo.get_monitoring_engine().metrics()


@router.get("/incidents")
async def system_incidents(
    limit: int = Query(50, ge=1, le=500),
    status: str | None = Query(None),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return mo.get_monitoring_engine().incidents(limit=limit, status=status)


@router.get("/alerts")
async def system_alerts(
    limit: int = Query(50, ge=1, le=500),
    level: str | None = Query(None),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return mo.get_monitoring_engine().alerts(limit=limit, level=level)


@router.post("/recovery")
async def system_recovery(
    body: RecoveryRequest | None = None,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    engine = mo.get_monitoring_engine()
    try:
        payload: dict[str, Any] = {}
        if body:
            payload = body.model_dump(by_alias=False, exclude_none=True)
        return engine.recovery(payload)
    except Exception as exc:
        raise HTTPException(status_code=500, detail="System recovery failed") from exc


@router.get("/status")
async def system_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return mo.get_monitoring_engine().status()
