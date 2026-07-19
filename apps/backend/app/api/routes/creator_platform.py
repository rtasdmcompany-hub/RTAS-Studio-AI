"""Creator Platform & Publisher Ecosystem APIs — Phase 9 Sprint 2."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.backend_auth import require_backend_secret
from app.core.config import settings
from app.services import creator_platform as cp_svc
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

creator_router = APIRouter(prefix="/creator", tags=["creator-platform"])
publisher_router = APIRouter(prefix="/publisher", tags=["publisher"])


def _auth(secret: str | None) -> None:
    require_backend_secret(x_rtas_backend_secret=secret)


def _svc():
    return cp_svc.get_creator_platform_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Creator platform operation failed")


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class ProfileCreateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    display_name: str = Field(..., alias="displayName")
    bio: str = ""
    avatar_uri: str = Field("", alias="avatarUri")
    social_links: dict[str, str] = Field(default_factory=dict, alias="socialLinks")
    categories: list[str] = Field(default_factory=list)
    model_config = {"populate_by_name": True}


class ProfileUpdateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    display_name: str | None = Field(None, alias="displayName")
    bio: str | None = None
    avatar_uri: str | None = Field(None, alias="avatarUri")
    social_links: dict[str, str] | None = Field(None, alias="socialLinks")
    categories: list[str] | None = None
    model_config = {"populate_by_name": True}


class VerificationRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    note: str = ""
    model_config = {"populate_by_name": True}


class VerificationReviewRequest(BaseModel):
    creator_id: str = Field(..., alias="creatorId")
    approve: bool
    note: str = ""
    model_config = {"populate_by_name": True}


class FollowRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    creator_id: str = Field(..., alias="creatorId")
    model_config = {"populate_by_name": True}


class PortfolioItemRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    title: str
    description: str = ""
    media_uri: str = Field("", alias="mediaUri")
    asset_id: str | None = Field(None, alias="assetId")
    model_config = {"populate_by_name": True}


class FeaturedRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    asset_ids: list[str] = Field(default_factory=list, alias="assetIds")
    model_config = {"populate_by_name": True}


class EngagementEventRequest(BaseModel):
    creator_id: str = Field(..., alias="creatorId")
    event_type: str = Field(..., alias="eventType")
    asset_id: str | None = Field(None, alias="assetId")
    amount_credits: float = Field(0.0, alias="amountCredits")
    rating: int = 0
    model_config = {"populate_by_name": True}


class PublishRequest(BaseModel):
    organization_id: str | None = Field(None, alias="organizationId")
    asset_id: str | None = Field(None, alias="assetId")
    name: str | None = None
    asset_type: str = Field("custom", alias="assetType")
    description: str = ""
    category: str = "other"
    tags: list[str] = Field(default_factory=list)
    visibility: str = "public"
    asset_uri: str | None = Field(None, alias="assetUri")
    price_credits: float = Field(0.0, alias="priceCredits")
    publish_at: str | None = Field(None, alias="publishAt")
    draft: bool = False
    metadata: dict[str, Any] = Field(default_factory=dict)
    model_config = {"populate_by_name": True}


class AssetUpdateRequest(BaseModel):
    asset_id: str = Field(..., alias="assetId")
    name: str | None = None
    description: str | None = None
    category: str | None = None
    tags: list[str] | None = None
    visibility: str | None = None
    asset_uri: str | None = Field(None, alias="assetUri")
    price_credits: float | None = Field(None, alias="priceCredits")
    version: str | None = None
    changelog: str | None = None
    status: str | None = None
    model_config = {"populate_by_name": True}


# --- Creator endpoints ---


@creator_router.post("/profile")
async def create_profile(
    body: ProfileCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().creators.create_profile(
            body.model_dump(by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@creator_router.get("/profile")
async def get_profile(
    organization_id: str = Query(..., alias="organizationId"),
    creator_id: str | None = Query(None, alias="creatorId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().creators.get_profile(
            actor_id=actor, organization_id=organization_id, creator_id=creator_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@creator_router.patch("/profile")
async def update_profile(
    body: ProfileUpdateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        payload = body.model_dump(by_alias=True, exclude_unset=True)
        organization_id = payload.pop("organizationId")
        return _svc().creators.update_profile(
            payload, actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@creator_router.get("/analytics")
async def creator_analytics(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().analytics.summary(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@creator_router.post("/analytics/events")
async def record_engagement_event(
    body: EngagementEventRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    try:
        return _svc().analytics.record_event(
            body.model_dump(by_alias=True), actor_id=x_rtas_user_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@creator_router.post("/verification/request")
async def request_verification(
    body: VerificationRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().verification.request(
            actor_id=actor,
            organization_id=body.organization_id,
            note=body.note,
        )
    except Exception as exc:
        raise _map(exc) from exc


@creator_router.post("/verification/review")
async def review_verification(
    body: VerificationReviewRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().verification.review(
            body.creator_id, actor_id=actor, approve=body.approve, note=body.note
        )
    except Exception as exc:
        raise _map(exc) from exc


@creator_router.post("/follow")
async def follow_creator(
    body: FollowRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().creators.follow(
            body.creator_id, actor_id=actor, organization_id=body.organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@creator_router.post("/unfollow")
async def unfollow_creator(
    body: FollowRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().creators.unfollow(
            body.creator_id, actor_id=actor, organization_id=body.organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@creator_router.get("/portfolio")
async def get_portfolio(
    organization_id: str = Query(..., alias="organizationId"),
    creator_id: str | None = Query(None, alias="creatorId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().portfolio.get(
            actor_id=actor, organization_id=organization_id, creator_id=creator_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@creator_router.post("/portfolio")
async def add_portfolio_item(
    body: PortfolioItemRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        payload = body.model_dump(by_alias=True)
        organization_id = payload.pop("organizationId")
        return _svc().portfolio.add_item(
            payload, actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@creator_router.delete("/portfolio/{item_id}")
async def remove_portfolio_item(
    item_id: str,
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().portfolio.remove_item(
            item_id, actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@creator_router.post("/portfolio/featured")
async def set_featured_assets(
    body: FeaturedRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().portfolio.set_featured(
            body.asset_ids, actor_id=actor, organization_id=body.organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@creator_router.get("/status")
async def creator_platform_status():
    return _svc().status()


# --- Publisher endpoints ---


@publisher_router.post("/publish")
async def publish_asset(
    body: PublishRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().publishing.publish(
            body.model_dump(by_alias=True, exclude_none=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@publisher_router.patch("/update")
async def update_asset(
    body: AssetUpdateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        payload = body.model_dump(by_alias=True, exclude_unset=True)
        asset_id = payload.pop("assetId")
        return _svc().publisher.update(asset_id, payload, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@publisher_router.get("/assets")
async def list_publisher_assets(
    organization_id: str = Query(..., alias="organizationId"),
    status: str | None = Query(None),
    creator_id: str | None = Query(None, alias="creatorId"),
    limit: int = Query(100, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().publisher.list(
            actor_id=actor,
            organization_id=organization_id,
            status=status,
            creator_id=creator_id,
            limit=limit,
        )
    except Exception as exc:
        raise _map(exc) from exc


@publisher_router.delete("/assets/{asset_id}")
async def delete_publisher_asset(
    asset_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().publisher.delete(asset_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@publisher_router.post("/schedule/run")
async def run_publishing_schedule(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    try:
        return _svc().publishing.process_due()
    except Exception as exc:
        raise _map(exc) from exc


@publisher_router.get("/status")
async def publisher_status():
    return _svc().status()
