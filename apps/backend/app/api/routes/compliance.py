"""Phase 10 Sprint 8 — Legal Compliance & Enterprise Release APIs."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import phase10_compliance as comp_svc
import app.services.phase10_compliance.dsr_store as dsr_store

router = APIRouter(prefix="/compliance", tags=["phase10-compliance"])


def _auth(secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if expected and (secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _svc():
    return comp_svc.get_phase10_compliance_service()


class DsrUserBody(BaseModel):
    user_id: str = Field(..., min_length=1, max_length=200)


@router.get("/status")
async def compliance_status():
    return _svc().status()


@router.get("/legal")
async def compliance_legal(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().legal_compliance_audit()


@router.get("/privacy")
async def compliance_privacy(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().privacy_audit()


@router.get("/matrix")
async def compliance_matrix(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().compliance_matrix()


@router.get("/third-party")
async def compliance_third_party(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().third_party_readiness()


@router.get("/licensing")
async def compliance_licensing(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().licensing_audit()


@router.get("/documentation")
async def compliance_documentation(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().documentation_audit()


@router.get("/release")
async def compliance_release(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().enterprise_release_readiness()


@router.post("/dsr/access")
async def dsr_access(
    body: DsrUserBody,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return dsr_store.request_access(body.user_id)


@router.post("/dsr/export")
async def dsr_export(
    body: DsrUserBody,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return dsr_store.export_user_data(body.user_id)


@router.post("/dsr/erase")
async def dsr_erase(
    body: DsrUserBody,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return dsr_store.delete_user_account(body.user_id)


@router.get("/dsr/{request_id}")
async def dsr_status(
    request_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    item = dsr_store.get_request(request_id)
    if not item:
        raise HTTPException(status_code=404, detail="DSR request not found")
    return item


@router.get("/report")
async def compliance_report(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().full_report()
