"""Usage analytics APIs — Phase 8 Sprint 4."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query

from app.core.config import settings
from app.services import credit_metering as cm
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

router = APIRouter(prefix="/usage", tags=["usage-analytics"])


def _auth(secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if expected and (secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _svc():
    return cm.get_credit_metering_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Usage analytics failed")


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


@router.get("/analytics")
async def usage_analytics(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    limit: int = Query(100, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().analytics.analytics(
            actor_id=actor,
            organization_id=organization_id,
            workspace_id=workspace_id,
            limit=limit,
        )
    except Exception as exc:
        raise _map(exc) from exc
