"""Phase 10 Sprint 7 — Observability & Operational Excellence APIs."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from app.core.config import settings
from app.services import phase10_observability as obs_svc

router = APIRouter(prefix="/observability", tags=["phase10-observability"])


def _auth(secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if expected and (secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _svc():
    return obs_svc.get_phase10_observability_service()


@router.get("/status")
async def obs_status():
    return _svc().status()


@router.get("/audit")
async def obs_audit(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().observability_audit()


@router.get("/logging")
async def obs_logging(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().verify_logging()


@router.get("/monitoring")
async def obs_monitoring(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().monitoring_coverage()


@router.get("/alerting")
async def obs_alerting(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().verify_alerting()


@router.get("/health-checks")
async def obs_health_checks(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().health_verification()


@router.get("/operations")
async def obs_operations(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().operational_readiness()


@router.post("/validate")
async def obs_validate(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().monitoring_validation()


@router.get("/report")
async def obs_report(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().full_report()
