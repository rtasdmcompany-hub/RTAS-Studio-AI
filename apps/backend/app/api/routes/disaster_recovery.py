"""Phase 10 Sprint 6 — Disaster Recovery & High Availability APIs."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from app.core.backend_auth import require_backend_secret
from app.core.config import settings
from app.services import phase10_disaster_recovery as dr_svc

router = APIRouter(prefix="/disaster-recovery", tags=["phase10-disaster-recovery"])


def _auth(secret: str | None) -> None:
    require_backend_secret(x_rtas_backend_secret=secret)


def _svc():
    return dr_svc.get_phase10_disaster_recovery_service()


@router.get("/status")
async def dr_status():
    return _svc().status()


@router.get("/audit")
async def dr_audit(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().disaster_recovery_audit()


@router.post("/backup")
async def dr_backup(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().run_backup_cycle()


@router.post("/simulate")
async def dr_simulate(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().simulate_recovery()


@router.get("/high-availability")
async def dr_ha(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().verify_high_availability()


@router.post("/continuity")
async def dr_continuity(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().business_continuity()


@router.get("/monitoring")
async def dr_monitoring(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().verify_monitoring()


@router.get("/reliability")
async def dr_reliability(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().reliability_tests()


@router.get("/report")
async def dr_report(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().full_report()
