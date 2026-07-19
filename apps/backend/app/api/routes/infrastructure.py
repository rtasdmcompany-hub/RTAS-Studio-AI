"""Phase 10 Sprint 4 — Infrastructure scalability validation APIs."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query

from app.core.backend_auth import require_backend_secret
from app.core.config import settings
from app.services import phase10_infrastructure as infra

router = APIRouter(prefix="/infrastructure", tags=["phase10-infrastructure"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    require_backend_secret(x_rtas_backend_secret=x_rtas_backend_secret)


@router.get("/status")
async def infrastructure_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    inv = infra.infrastructure_inventory()
    return {
        "ok": True,
        "phase": 10,
        "sprint": 4,
        "engine": infra.ENGINE_NAME,
        "version": infra.ENGINE_VERSION,
        **inv,
    }


@router.get("/scalability")
async def infrastructure_scalability(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return infra.scalability_matrix()


@router.get("/cache")
async def infrastructure_cache(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return infra.cache_inventory()


@router.get("/queue")
async def infrastructure_queue(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return infra.queue_architecture_report()


@router.get("/latency")
async def infrastructure_latency(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return {"ok": True, **infra.latency_profile()}


@router.post("/recovery")
async def infrastructure_recovery(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return infra.recovery_suite()


@router.post("/stress")
async def infrastructure_stress(
    max_jobs: int = Query(1000, ge=100, le=1000),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    batches = (100, 250, 500, 1000)
    batches = tuple(b for b in batches if b <= max_jobs)
    return infra.run_stress_batches(batches)


@router.get("/report")
async def infrastructure_report(
    run_stress: bool = Query(False, alias="runStress"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return infra.full_report(run_stress=run_stress)
