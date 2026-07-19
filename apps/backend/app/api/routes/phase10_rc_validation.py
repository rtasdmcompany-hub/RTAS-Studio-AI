"""Phase 10 Sprint 5 — AI QA & Release Candidate (RC-1) APIs."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query

from app.core.config import settings
from app.services import phase10_rc_validation as rc_svc

router = APIRouter(prefix="/phase10/rc", tags=["phase10-rc-validation"])


def _auth(secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if expected and (secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _svc():
    return rc_svc.get_phase10_rc_validation_service()


@router.get("/status")
async def rc_status():
    return _svc().status()


@router.get("/ai")
async def rc_ai(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().validate_ai_generation()


@router.get("/workflow")
async def rc_workflow(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().validate_e2e_workflow()


@router.get("/providers")
async def rc_providers(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().validate_provider_routing()


@router.get("/quality")
async def rc_quality(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().validate_output_quality()


@router.get("/modules")
async def rc_modules(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().validate_rc1_modules()


@router.get("/regression")
async def rc_regression(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().validate_regression()


@router.post("/validate")
async def rc_validate(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().full_validation()


@router.get("/report")
async def rc_report(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().full_validation()
