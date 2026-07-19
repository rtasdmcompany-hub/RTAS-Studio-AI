"""Usage analytics, budget & cost optimization APIs — Phase 8 Sprint 8."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.backend_auth import require_backend_secret
from app.core.config import settings
from app.services import provider_analytics as pa_svc
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

analytics_router = APIRouter(prefix="/analytics", tags=["provider-analytics"])
budget_router = APIRouter(prefix="/budget", tags=["budget"])
optimization_router = APIRouter(prefix="/optimization", tags=["optimization"])


def _auth(secret: str | None) -> None:
    require_backend_secret(x_rtas_backend_secret=secret)


def _svc():
    return pa_svc.get_provider_analytics_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Analytics operation failed")


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class BudgetUpdateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    scope: str = "organization"
    scope_id: str | None = Field(None, alias="scopeId")
    daily_limit_usd: float = Field(0.0, alias="dailyLimitUsd")
    monthly_limit_usd: float = Field(0.0, alias="monthlyLimitUsd")
    alerts_enabled: bool | None = Field(None, alias="alertsEnabled")
    hard_stop: bool | None = Field(None, alias="hardStop")
    model_config = {"populate_by_name": True}


class UsageRecordRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    provider: str
    model: str = ""
    user_id: str | None = Field(None, alias="userId")
    workspace_id: str | None = Field(None, alias="workspaceId")
    status: str = "success"
    latency_ms: float = Field(0.0, alias="latencyMs")
    credits_charged: float = Field(0.0, alias="creditsCharged")
    units: float = 1.0
    model_config = {"populate_by_name": True, "protected_namespaces": ()}


# --- Analytics ---


@analytics_router.get("/providers")
async def provider_analytics(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().analytics.provider_analytics(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@analytics_router.get("/costs")
async def cost_analytics(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().billing.costs(actor_id=actor, organization_id=organization_id)
    except Exception as exc:
        raise _map(exc) from exc


@analytics_router.get("/revenue")
async def revenue_analytics(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().billing.revenue(actor_id=actor, organization_id=organization_id)
    except Exception as exc:
        raise _map(exc) from exc


@analytics_router.get("/profit")
async def profit_analytics(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().profit.profit(actor_id=actor, organization_id=organization_id)
    except Exception as exc:
        raise _map(exc) from exc


@analytics_router.get("/usage")
async def usage_analytics(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().analytics.usage(actor_id=actor, organization_id=organization_id)
    except Exception as exc:
        raise _map(exc) from exc


@analytics_router.post("/usage/record")
async def record_usage(
    body: UsageRecordRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    try:
        event = _svc().analytics.record(
            body.organization_id,
            body.provider,
            model=body.model,
            user_id=body.user_id,
            workspace_id=body.workspace_id,
            status=body.status,
            latency_ms=body.latency_ms,
            credits_charged=body.credits_charged,
            units=body.units,
        )
        return {"ok": True, "event": event.to_dict()}
    except Exception as exc:
        raise _map(exc) from exc


@analytics_router.get("/engine-status")
async def engine_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().status()


# --- Budget ---


@budget_router.get("")
async def get_budget(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().budgets.get(actor_id=actor, organization_id=organization_id)
    except Exception as exc:
        raise _map(exc) from exc


@budget_router.post("/update")
async def update_budget(
    body: BudgetUpdateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().budgets.update(
            body.model_dump(by_alias=True, exclude_none=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


# --- Optimization ---


@optimization_router.get("/recommendations")
async def optimization_recommendations(
    organization_id: str = Query(..., alias="organizationId"),
    mode: str = Query("balanced"),
    capability: str | None = Query(None),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().optimizer.recommendations(
            actor_id=actor,
            organization_id=organization_id,
            mode=mode,
            capability=capability,
        )
    except Exception as exc:
        raise _map(exc) from exc


@optimization_router.get("/history")
async def optimization_history(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().optimizer.history(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc
