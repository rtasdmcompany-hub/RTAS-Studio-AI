"""Enterprise SaaS Platform final validation APIs — Phase 7 Sprint 10."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query

from app.core.backend_auth import require_backend_secret
from app.core.config import settings
from app.services import enterprise_saas as es
from app.services.multi_tenant.validation import ValidationError

router = APIRouter(prefix="/enterprise", tags=["enterprise-saas"])


def _auth(secret: str | None) -> None:
    require_backend_secret(x_rtas_backend_secret=secret)


def _svc():
    return es.get_enterprise_saas_service()


@router.get("/status")
async def enterprise_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().status()


@router.get("/observability")
async def enterprise_observability(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().observability()


@router.post("/validate")
async def enterprise_validate(
    run_stress: bool = Query(True, alias="runStress"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    try:
        # API default uses lighter stress batches for latency
        batches = (50, 100, 250) if run_stress else None
        return _svc().validate(
            run_stress=run_stress,
            stress_batches=batches,
            regression_pass_rate=1.0,
        )
    except ValidationError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/modules")
async def enterprise_modules(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().modules.verify_all()


@router.get("/scores")
async def enterprise_scores(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    scores = _svc().observability().get("scores") or {}
    if not scores:
        # compute without full stress for ranking endpoint
        result = _svc().validate(run_stress=False, regression_pass_rate=1.0)
        scores = result["scores"]
    return {"ok": True, "scores": scores}
