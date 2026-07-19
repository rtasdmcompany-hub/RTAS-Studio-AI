"""Phase 9 Final Integration & Production Validation APIs — Sprint 10."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query

from app.core.config import settings
from app.services import phase9_final_validation as p9_svc
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

phase9_router = APIRouter(prefix="/phase9", tags=["phase9-final-validation"])


def _auth(secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if expected and (secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _svc():
    return p9_svc.get_phase9_final_validation_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Phase 9 validation failed")


@phase9_router.get("/status")
async def phase9_status():
    return _svc().status()


@phase9_router.get("/modules")
async def phase9_modules(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    try:
        return _svc().modules.verify()
    except Exception as exc:
        raise _map(exc) from exc


@phase9_router.get("/endpoints")
async def phase9_endpoints():
    return _svc().endpoints.catalog()


@phase9_router.post("/validate")
async def phase9_validate(
    run_load: bool = Query(True, alias="runLoad"),
    light_load: bool = Query(False, alias="lightLoad"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    try:
        batches = (50, 100) if light_load else None
        return _svc().full_validation(run_load=run_load, load_batches=batches)
    except Exception as exc:
        raise _map(exc) from exc


@phase9_router.get("/report")
async def phase9_report(
    light_load: bool = Query(True, alias="lightLoad"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    try:
        batches = (50, 100) if light_load else None
        return _svc().full_validation(run_load=True, load_batches=batches)
    except Exception as exc:
        raise _map(exc) from exc
