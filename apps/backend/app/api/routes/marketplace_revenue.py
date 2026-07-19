"""Marketplace Analytics, Revenue Intelligence & Monetization APIs — Phase 9 Sprint 9."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.backend_auth import require_backend_secret
from app.core.config import settings
from app.services import marketplace_revenue as mr_svc
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

# Registered before provider_analytics so Sprint 9 paths win on /analytics/*.
analytics_router = APIRouter(prefix="/analytics", tags=["marketplace-revenue"])
monetization_router = APIRouter(prefix="/monetization", tags=["marketplace-revenue"])


def _auth(secret: str | None) -> None:
    require_backend_secret(x_rtas_backend_secret=secret)


def _svc():
    return mr_svc.get_marketplace_revenue_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(
        status_code=500, detail="Marketplace revenue operation failed"
    )


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class LedgerRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    stream: str
    amount: float
    workspace_id: str | None = Field(None, alias="workspaceId")
    currency: str = "USD"
    creator_id: str | None = Field(None, alias="creatorId")
    product_id: str | None = Field(None, alias="productId")
    customer_id: str | None = Field(None, alias="customerId")
    period: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


class SaleRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    event_type: str = Field(..., alias="eventType")
    amount: float = 0.0
    workspace_id: str | None = Field(None, alias="workspaceId")
    product_id: str | None = Field(None, alias="productId")
    creator_id: str | None = Field(None, alias="creatorId")
    customer_id: str | None = Field(None, alias="customerId")
    quantity: int = 1
    model_config = {"populate_by_name": True}


class ProductMetricRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    product_id: str = Field(..., alias="productId")
    metric: str
    category: str = "other"
    featured: bool = False
    value: float = 1.0
    creator_id: str | None = Field(None, alias="creatorId")
    amount: float = 0.0
    model_config = {"populate_by_name": True}


@monetization_router.get("/engine-status")
async def monetization_engine_status():
    return _svc().status()


@analytics_router.get("")
async def analytics_root():
    """Unauthenticated analytics surface health probe."""
    return _svc().status()


@analytics_router.get("/status")
async def analytics_engine_status():
    return _svc().status()


@analytics_router.get("/revenue")
async def analytics_revenue(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    period: str | None = Query(None),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().revenue.report(
            actor_id=actor,
            organization_id=organization_id,
            workspace_id=workspace_id,
            period=period,
        )
    except Exception as exc:
        raise _map(exc) from exc


@analytics_router.get("/sales")
async def analytics_sales(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().sales.report(
            actor_id=actor,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
    except Exception as exc:
        raise _map(exc) from exc


@analytics_router.get("/marketplace")
async def analytics_marketplace(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().marketplace.report(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@analytics_router.get("/creators")
async def analytics_creators(
    organization_id: str = Query(..., alias="organizationId"),
    creator_id: str | None = Query(None, alias="creatorId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().creators.report(
            actor_id=actor,
            organization_id=organization_id,
            creator_id=creator_id,
        )
    except Exception as exc:
        raise _map(exc) from exc


@analytics_router.get("/forecast")
async def analytics_forecast(
    organization_id: str = Query(..., alias="organizationId"),
    horizon: str = Query("90d"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().forecast.forecast(
            actor_id=actor,
            organization_id=organization_id,
            horizon=horizon,
        )
    except Exception as exc:
        raise _map(exc) from exc


@analytics_router.get("/products")
async def analytics_products(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().monetization.products(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@analytics_router.get("/customers")
async def analytics_customers(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().monetization.customers(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


# Ingest helpers (backend-only; not UI)
@monetization_router.post("/ledger")
async def record_ledger(
    body: LedgerRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().revenue.record(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@monetization_router.post("/sales")
async def record_sale(
    body: SaleRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().sales.record(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@monetization_router.post("/product-metrics")
async def record_product_metric(
    body: ProductMetricRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().marketplace.track(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc
