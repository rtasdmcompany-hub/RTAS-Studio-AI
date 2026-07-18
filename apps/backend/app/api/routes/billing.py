"""Billing & Subscription Foundation APIs — Phase 8 Sprint 1."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import billing as billing_svc
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

router = APIRouter(prefix="/billing", tags=["billing"])


def _auth(secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if expected and (secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _svc():
    return billing_svc.get_billing_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Billing operation failed")


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class SubscriptionCreateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    plan_key: str = Field("free_trial", alias="planKey")
    billing_cycle: str = Field("monthly", alias="billingCycle")
    seats: int = 1
    company_name: str | None = Field(None, alias="companyName")
    billing_email: str | None = Field(None, alias="billingEmail")
    metadata: dict[str, Any] | None = None
    model_config = {"populate_by_name": True}


class SubscriptionPatchRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    plan_key: str | None = Field(None, alias="planKey")
    billing_cycle: str | None = Field(None, alias="billingCycle")
    status: str | None = None
    seats: int | None = None
    cancel_at_period_end: bool | None = Field(None, alias="cancelAtPeriodEnd")
    metadata: dict[str, Any] | None = None
    model_config = {"populate_by_name": True}


@router.get("/status")
async def billing_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().status()


@router.get("/observability")
async def billing_observability(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().observability()


@router.get("/plans")
async def list_plans(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().plans.list_plans()


@router.get("/subscription")
async def get_subscription(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().subscriptions.get(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/subscription")
async def create_subscription(
    body: SubscriptionCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().subscriptions.create(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.patch("/subscription")
async def patch_subscription(
    body: SubscriptionPatchRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().subscriptions.update(
            body.model_dump(by_alias=True, exclude_none=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/credits")
async def get_credits(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().credits.get(
            organization_id,
            actor_id=actor,
            workspace_id=workspace_id,
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/usage")
async def get_usage(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    limit: int = Query(100, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().usage.list(
            actor_id=actor,
            organization_id=organization_id,
            workspace_id=workspace_id,
            limit=limit,
        )
    except Exception as exc:
        raise _map(exc) from exc
