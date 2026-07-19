"""Marketplace, template store & digital commerce APIs — Phase 8 Sprint 9."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import marketplace as mk_svc
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

marketplace_router = APIRouter(prefix="/marketplace", tags=["marketplace"])


def _auth(secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if expected and (secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _svc():
    return mk_svc.get_marketplace_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Marketplace operation failed")


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class ProductPublishRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    name: str
    product_type: str = Field("custom", alias="productType")
    description: str = ""
    category: str = "other"
    tags: list[str] = Field(default_factory=list)
    pricing_model: str = Field("free", alias="pricingModel")
    price_credits: float = Field(0.0, alias="priceCredits")
    license_type: str = Field("personal", alias="licenseType")
    featured: bool = False
    workspace_id: str | None = Field(None, alias="workspaceId")
    asset_uri: str | None = Field(None, alias="assetUri")
    model_config = {"populate_by_name": True}


class ProductUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    featured: bool | None = None
    pricing_model: str | None = Field(None, alias="pricingModel")
    price_credits: float | None = Field(None, alias="priceCredits")
    status: str | None = None
    version: str | None = None
    changelog: str | None = None
    asset_uri: str | None = Field(None, alias="assetUri")
    model_config = {"populate_by_name": True}


class PurchaseRequest(BaseModel):
    product_id: str = Field(..., alias="productId")
    organization_id: str = Field(..., alias="organizationId")
    workspace_id: str | None = Field(None, alias="workspaceId")
    model_config = {"populate_by_name": True}


class ReviewRequest(BaseModel):
    product_id: str = Field(..., alias="productId")
    rating: int
    title: str = ""
    body: str = ""
    model_config = {"populate_by_name": True}


class LicenseValidateRequest(BaseModel):
    license_key: str = Field(..., alias="licenseKey")
    model_config = {"populate_by_name": True}


class DownloadRedeemRequest(BaseModel):
    token: str


@marketplace_router.post("/products")
async def publish_product(
    body: ProductPublishRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().templates.publish(
            body.model_dump(by_alias=True, exclude_none=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@marketplace_router.get("/products")
async def list_products(
    organization_id: str | None = Query(None, alias="organizationId"),
    category: str | None = Query(None),
    product_type: str | None = Query(None, alias="productType"),
    pricing_model: str | None = Query(None, alias="pricingModel"),
    status: str = Query("published"),
    limit: int = Query(100, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    try:
        return _svc().catalog.list(
            organization_id=organization_id,
            category=category,
            product_type=product_type,
            pricing_model=pricing_model,
            status=status,
            limit=limit,
        )
    except Exception as exc:
        raise _map(exc) from exc


@marketplace_router.get("/products/{product_id}")
async def get_product(
    product_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    try:
        return _svc().catalog.get(product_id, viewer_id=x_rtas_user_id)
    except Exception as exc:
        raise _map(exc) from exc


@marketplace_router.patch("/products/{product_id}")
async def update_product(
    product_id: str,
    body: ProductUpdateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        payload: dict[str, Any] = body.model_dump(by_alias=True, exclude_none=True)
        return _svc().templates.update(product_id, payload, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@marketplace_router.delete("/products/{product_id}")
async def delete_product(
    product_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().templates.delete(product_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@marketplace_router.get("/products/{product_id}/versions")
async def product_versions(
    product_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    try:
        return _svc().templates.versions(product_id)
    except Exception as exc:
        raise _map(exc) from exc


@marketplace_router.post("/purchase")
async def purchase_product(
    body: PurchaseRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().commerce.purchase(
            body.model_dump(by_alias=True, exclude_none=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@marketplace_router.get("/purchases")
async def list_purchases(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().commerce.purchases(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@marketplace_router.post("/purchases/{purchase_id}/refund")
async def refund_purchase(
    purchase_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().commerce.refund(purchase_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@marketplace_router.post("/products/{product_id}/download")
async def request_download(
    product_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().commerce.request_download(product_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@marketplace_router.post("/download/redeem")
async def redeem_download(
    body: DownloadRedeemRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().commerce.redeem_download(body.token, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@marketplace_router.post("/license/validate")
async def validate_license(
    body: LicenseValidateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    try:
        return _svc().commerce.validate_license(body.license_key)
    except Exception as exc:
        raise _map(exc) from exc


@marketplace_router.post("/reviews")
async def create_review(
    body: ReviewRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().commerce.review(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@marketplace_router.get("/search")
async def search_products(
    q: str = Query(""),
    category: str | None = Query(None),
    tag: str | None = Query(None),
    product_type: str | None = Query(None, alias="productType"),
    semantic: bool = Query(False),
    limit: int = Query(50, ge=1, le=200),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    try:
        return _svc().search.search(
            q,
            category=category,
            tag=tag,
            product_type=product_type,
            semantic=semantic,
            limit=limit,
        )
    except Exception as exc:
        raise _map(exc) from exc


@marketplace_router.get("/discovery")
async def discovery(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    try:
        return _svc().search.discovery(x_rtas_user_id)
    except Exception as exc:
        raise _map(exc) from exc


@marketplace_router.get("/categories")
async def categories(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().catalog.categories()


@marketplace_router.get("/tags")
async def tags(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().catalog.tags()


@marketplace_router.get("/analytics")
async def marketplace_analytics(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().analytics.analytics(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@marketplace_router.get("/status")
async def engine_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().status()
