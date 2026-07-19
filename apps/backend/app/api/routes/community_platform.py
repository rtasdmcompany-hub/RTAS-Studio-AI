"""Community Platform & Social Collaboration APIs — Phase 9 Sprint 3."""

from __future__ import annotations

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.backend_auth import require_backend_secret
from app.core.config import settings
from app.services import community_platform as cm_svc
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

community_router = APIRouter(prefix="/community", tags=["community"])


def _auth(secret: str | None) -> None:
    require_backend_secret(x_rtas_backend_secret=secret)


def _svc():
    return cm_svc.get_community_platform_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Community operation failed")


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class ProfileCreateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    display_name: str = Field(..., alias="displayName")
    handle: str
    bio: str = ""
    avatar_uri: str = Field("", alias="avatarUri")
    model_config = {"populate_by_name": True}


class ProfileUpdateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    display_name: str | None = Field(None, alias="displayName")
    bio: str | None = None
    avatar_uri: str | None = Field(None, alias="avatarUri")
    model_config = {"populate_by_name": True}


class VerifyMemberRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    user_id: str = Field(..., alias="userId")
    model_config = {"populate_by_name": True}


class FollowRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    target_user_id: str = Field(..., alias="targetUserId")
    model_config = {"populate_by_name": True}


class RatingRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    asset_id: str = Field(..., alias="assetId")
    value: int
    asset_owner_user_id: str = Field("", alias="assetOwnerUserId")
    model_config = {"populate_by_name": True}


class ReviewRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    asset_id: str = Field(..., alias="assetId")
    rating: int
    title: str = ""
    body: str = ""
    asset_category: str = Field("", alias="assetCategory")
    asset_owner_user_id: str = Field("", alias="assetOwnerUserId")
    model_config = {"populate_by_name": True}


class CommentRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    subject_id: str = Field(..., alias="subjectId")
    body: str
    parent_id: str | None = Field(None, alias="parentId")
    mentions: list[str] = Field(default_factory=list)
    model_config = {"populate_by_name": True}


class ModerateRequest(BaseModel):
    status: str


class EngageRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    asset_id: str = Field(..., alias="assetId")
    kind: str = "like"
    asset_category: str = Field("", alias="assetCategory")
    asset_owner_user_id: str = Field("", alias="assetOwnerUserId")
    model_config = {"populate_by_name": True}


class FeaturedRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    creators: list[str] = Field(default_factory=list)
    assets: list[str] = Field(default_factory=list)
    model_config = {"populate_by_name": True}


# --- Profiles ---


@community_router.post("/profile")
async def create_profile(
    body: ProfileCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().profiles.create(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@community_router.get("/profile")
async def get_profile(
    organization_id: str = Query(..., alias="organizationId"),
    user_id: str | None = Query(None, alias="userId"),
    handle: str | None = Query(None),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().profiles.get(
            actor_id=actor, organization_id=organization_id,
            user_id=user_id, handle=handle,
        )
    except Exception as exc:
        raise _map(exc) from exc


@community_router.patch("/profile")
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
        return _svc().profiles.update(
            payload, actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@community_router.post("/profile/verify")
async def verify_member(
    body: VerifyMemberRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().profiles.verify_member(
            body.user_id, actor_id=actor, organization_id=body.organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


# --- Follow system ---


@community_router.post("/follow")
async def follow(
    body: FollowRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().follows.follow(
            body.target_user_id, actor_id=actor, organization_id=body.organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@community_router.delete("/unfollow")
async def unfollow(
    organization_id: str = Query(..., alias="organizationId"),
    target_user_id: str = Query(..., alias="targetUserId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().follows.unfollow(
            target_user_id, actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@community_router.get("/followers")
async def followers(
    organization_id: str = Query(..., alias="organizationId"),
    user_id: str | None = Query(None, alias="userId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().follows.followers(
            actor_id=actor, organization_id=organization_id, user_id=user_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@community_router.get("/following")
async def following(
    organization_id: str = Query(..., alias="organizationId"),
    user_id: str | None = Query(None, alias="userId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().follows.following(
            actor_id=actor, organization_id=organization_id, user_id=user_id
        )
    except Exception as exc:
        raise _map(exc) from exc


# --- Ratings & reviews ---


@community_router.post("/rate")
async def rate_asset(
    body: RatingRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().reviews.rate(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@community_router.post("/review")
async def create_review(
    body: ReviewRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().reviews.review(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@community_router.get("/reviews")
async def list_reviews(
    organization_id: str = Query(..., alias="organizationId"),
    asset_id: str | None = Query(None, alias="assetId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().reviews.list(
            actor_id=actor, organization_id=organization_id, asset_id=asset_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@community_router.post("/reviews/{review_id}/moderate")
async def moderate_review(
    review_id: str,
    body: ModerateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().reviews.moderate(review_id, body.status, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


# --- Comments ---


@community_router.post("/comment")
async def create_comment(
    body: CommentRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().comments.create(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@community_router.get("/comments")
async def list_comments(
    organization_id: str = Query(..., alias="organizationId"),
    subject_id: str | None = Query(None, alias="subjectId"),
    parent_id: str | None = Query(None, alias="parentId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().comments.list(
            actor_id=actor, organization_id=organization_id,
            subject_id=subject_id, parent_id=parent_id,
        )
    except Exception as exc:
        raise _map(exc) from exc


@community_router.post("/comments/{comment_id}/moderate")
async def moderate_comment(
    comment_id: str,
    body: ModerateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().comments.moderate(comment_id, body.status, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


# --- Engagement (likes / favorites / bookmarks) ---


@community_router.post("/engage")
async def engage(
    body: EngageRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().engage(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@community_router.delete("/engage")
async def unengage(
    organization_id: str = Query(..., alias="organizationId"),
    asset_id: str = Query(..., alias="assetId"),
    kind: str = Query("like"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().unengage(
            {"organizationId": organization_id, "assetId": asset_id, "kind": kind},
            actor_id=actor,
        )
    except Exception as exc:
        raise _map(exc) from exc


@community_router.get("/engagements")
async def list_engagements(
    organization_id: str = Query(..., alias="organizationId"),
    kind: str | None = Query(None),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().list_engagements(
            actor_id=actor, organization_id=organization_id, kind=kind
        )
    except Exception as exc:
        raise _map(exc) from exc


# --- Feed, timeline & discovery ---


@community_router.get("/feed")
async def feed(
    organization_id: str = Query(..., alias="organizationId"),
    limit: int = Query(50, ge=1, le=200),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().feed(
            actor_id=actor, organization_id=organization_id, limit=limit
        )
    except Exception as exc:
        raise _map(exc) from exc


@community_router.get("/timeline")
async def timeline(
    organization_id: str = Query(..., alias="organizationId"),
    user_id: str | None = Query(None, alias="userId"),
    limit: int = Query(50, ge=1, le=200),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().timeline(
            actor_id=actor, organization_id=organization_id,
            user_id=user_id, limit=limit,
        )
    except Exception as exc:
        raise _map(exc) from exc


@community_router.get("/trending")
async def trending(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().trending(actor_id=actor, organization_id=organization_id)
    except Exception as exc:
        raise _map(exc) from exc


@community_router.get("/discovery")
async def discovery(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().discovery(actor_id=actor, organization_id=organization_id)
    except Exception as exc:
        raise _map(exc) from exc


@community_router.post("/featured")
async def set_featured(
    body: FeaturedRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().set_featured(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


# --- Notifications ---


@community_router.get("/notifications")
async def notifications(
    organization_id: str = Query(..., alias="organizationId"),
    unread_only: bool = Query(False, alias="unreadOnly"),
    limit: int = Query(100, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().notifications.list(
            actor_id=actor, organization_id=organization_id,
            unread_only=unread_only, limit=limit,
        )
    except Exception as exc:
        raise _map(exc) from exc


@community_router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().notifications.mark_read(notification_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@community_router.post("/notifications/read-all")
async def mark_all_notifications_read(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().notifications.mark_all_read(
            actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@community_router.get("/status")
async def community_status():
    return _svc().status()
