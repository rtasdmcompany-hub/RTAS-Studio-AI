"""Credit consumption, history, and quota APIs — Phase 8 Sprint 4."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import credit_metering as cm
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

router = APIRouter(prefix="/credits", tags=["credit-metering"])


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
    return HTTPException(status_code=500, detail="Credit operation failed")


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class ConsumeRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    service_type: str = Field(..., alias="serviceType")
    workspace_id: str | None = Field(None, alias="workspaceId")
    team_id: str | None = Field(None, alias="teamId")
    user_id: str | None = Field(None, alias="userId")
    provider: str = "default"
    quantity: float = 1.0
    credits: int | None = None
    resource_type: str | None = Field(None, alias="resourceType")
    resource_id: str | None = Field(None, alias="resourceId")
    model_config = {"populate_by_name": True}


@router.get("/status")
async def credits_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().status()


@router.get("/usage")
async def credits_usage(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().consumption.usage_summary(
            actor_id=actor,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/history")
async def credits_history(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    limit: int = Query(100, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().consumption.history(
            actor_id=actor,
            organization_id=organization_id,
            workspace_id=workspace_id,
            limit=limit,
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/quota")
async def credits_quota(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    team_id: str | None = Query(None, alias="teamId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().quotas.get(
            actor_id=actor,
            organization_id=organization_id,
            workspace_id=workspace_id,
            team_id=team_id,
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/consume")
async def credits_consume(
    body: ConsumeRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().consumption.consume(
            body.model_dump(by_alias=True, exclude_none=True),
            actor_id=actor,
        )
    except Exception as exc:
        raise _map(exc) from exc
