"""Notifications, Comments & Activity APIs — Phase 7 Sprint 6."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import enterprise_comms as ec
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

notifications_router = APIRouter(prefix="/notifications", tags=["enterprise-comms"])
activity_router = APIRouter(prefix="/activity", tags=["enterprise-comms"])
comments_router = APIRouter(prefix="/comments", tags=["enterprise-comms"])
announcements_router = APIRouter(prefix="/announcements", tags=["enterprise-comms"])


def _auth(secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if expected and (secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _svc():
    return ec.get_enterprise_comms_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Comms operation failed")


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class ReadNotificationsRequest(BaseModel):
    ids: list[str] = Field(default_factory=list)
    organization_id: str | None = Field(None, alias="organizationId")
    model_config = {"populate_by_name": True}


class CommentCreateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    resource_type: str = Field("project", alias="resourceType")
    resource_id: str = Field(..., alias="resourceId")
    body: str
    workspace_id: str | None = Field(None, alias="workspaceId")
    parent_id: str | None = Field(None, alias="parentId")
    notify_user_id: str | None = Field(None, alias="notifyUserId")
    model_config = {"populate_by_name": True}


class CommentUpdateRequest(BaseModel):
    body: str | None = None
    is_pinned: bool | None = Field(None, alias="isPinned")
    is_resolved: bool | None = Field(None, alias="isResolved")
    reaction: str | None = None
    emoji: str | None = None
    model_config = {"populate_by_name": True}


class PreferenceUpdateRequest(BaseModel):
    organization_id: str | None = Field(None, alias="organizationId")
    channel_email: bool | None = Field(None, alias="channelEmail")
    channel_in_app: bool | None = Field(None, alias="channelInApp")
    muted_types: list[str] | None = Field(None, alias="mutedTypes")
    digests_enabled: bool | None = Field(None, alias="digestsEnabled")
    model_config = {"populate_by_name": True}


class AnnouncementCreateRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    title: str
    body: str
    workspace_id: str | None = Field(None, alias="workspaceId")
    scope: str = "organization"
    is_pinned: bool = Field(False, alias="isPinned")
    model_config = {"populate_by_name": True}


class ActivityEmitRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    category: str
    action: str
    summary: str
    workspace_id: str | None = Field(None, alias="workspaceId")
    resource_type: str | None = Field(None, alias="resourceType")
    resource_id: str | None = Field(None, alias="resourceId")
    metadata: dict[str, Any] | None = None
    model_config = {"populate_by_name": True}


# --- Notifications ---


@notifications_router.get("/status")
async def notifications_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().status()


@notifications_router.get("/observability")
async def notifications_observability(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().observability()


@notifications_router.get("")
async def list_notifications(
    organization_id: str | None = Query(None, alias="organizationId"),
    unread_only: bool = Query(False, alias="unreadOnly"),
    limit: int = Query(50, ge=1, le=200),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().notifications.list(
            actor_id=actor,
            organization_id=organization_id,
            unread_only=unread_only,
            limit=limit,
        )
    except Exception as exc:
        raise _map(exc) from exc


@notifications_router.patch("/read")
async def mark_notifications_read(
    body: ReadNotificationsRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().notifications.mark_read(body.ids, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@notifications_router.patch("/read-all")
async def mark_all_notifications_read(
    organization_id: str | None = Query(None, alias="organizationId"),
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


@notifications_router.get("/preferences")
async def get_preferences(
    organization_id: str | None = Query(None, alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().preferences.get(user_id=actor, organization_id=organization_id)
    except Exception as exc:
        raise _map(exc) from exc


@notifications_router.patch("/preferences")
async def update_preferences(
    body: PreferenceUpdateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().preferences.update(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


# --- Activity ---


@activity_router.get("")
async def list_activity(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    category: str | None = Query(None),
    limit: int = Query(50, ge=1, le=200),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().activity.list(
            actor_id=actor,
            organization_id=organization_id,
            workspace_id=workspace_id,
            category=category,
            limit=limit,
        )
    except Exception as exc:
        raise _map(exc) from exc


@activity_router.post("")
async def emit_activity(
    body: ActivityEmitRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        from app.services.enterprise_auth.middleware import require_access

        require_access(
            user_id=actor,
            organization_id=body.organization_id,
            permission="content.write",
        )
        return _svc().activity.emit(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


# --- Comments ---


@comments_router.post("")
async def create_comment(
    body: CommentCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().comments.create(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@comments_router.patch("/{comment_id}")
async def update_comment(
    comment_id: str,
    body: CommentUpdateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().comments.update(
            comment_id, body.model_dump(exclude_none=True, by_alias=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@comments_router.delete("/{comment_id}")
async def delete_comment(
    comment_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().comments.delete(comment_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@comments_router.get("/{resource_id}")
async def list_comments_for_resource(
    resource_id: str,
    organization_id: str | None = Query(None, alias="organizationId"),
    resource_type: str | None = Query(None, alias="resourceType"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().comments.list_for_resource(
            resource_id,
            actor_id=actor,
            organization_id=organization_id,
            resource_type=resource_type,
        )
    except Exception as exc:
        raise _map(exc) from exc


# --- Announcements ---


@announcements_router.post("")
async def create_announcement(
    body: AnnouncementCreateRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().announcements.create(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@announcements_router.get("")
async def list_announcements(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().announcements.list(
            actor_id=actor,
            organization_id=organization_id,
            workspace_id=workspace_id,
        )
    except Exception as exc:
        raise _map(exc) from exc
