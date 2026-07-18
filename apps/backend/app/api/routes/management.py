"""Org Management Engine status & observability — Phase 7 Sprint 3."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException

from app.core.config import settings
from app.services import org_management as om

router = APIRouter(prefix="/management", tags=["org-management"])


def _auth(secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if expected and (secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("/status")
async def management_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return om.get_org_management_service().status()


@router.get("/observability")
async def management_observability(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return om.get_org_management_service().observability()
