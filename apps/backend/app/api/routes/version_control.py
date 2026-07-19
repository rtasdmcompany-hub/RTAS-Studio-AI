"""Version Control, Approval & Review APIs — Phase 7 Sprint 7."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.backend_auth import require_backend_secret
from app.core.config import settings
from app.services import version_control as vc
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

versions_router = APIRouter(prefix="/versions", tags=["version-control"])
reviews_router = APIRouter(prefix="/reviews", tags=["version-control"])
changelog_router = APIRouter(prefix="/changelog", tags=["version-control"])


def _auth(secret: str | None) -> None:
    require_backend_secret(x_rtas_backend_secret=secret)


def _svc():
    return vc.get_version_control_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Version control operation failed")


def _user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class CreateVersionRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    project_id: str = Field(..., alias="projectId")
    workspace_id: str | None = Field(None, alias="workspaceId")
    label: str | None = None
    notes: str | None = None
    status: str | None = "draft"
    snapshot: dict[str, Any] | None = None
    payload: dict[str, Any] | None = None
    parent_version_id: str | None = Field(None, alias="parentVersionId")
    is_current: bool = Field(True, alias="isCurrent")
    metadata: dict[str, Any] | None = None
    model_config = {"populate_by_name": True}


class RestoreVersionRequest(BaseModel):
    version_id: str = Field(..., alias="versionId")
    note: str | None = None
    notes: str | None = None
    create_new_version: bool = Field(False, alias="createNewVersion")
    label: str | None = None
    model_config = {"populate_by_name": True}


class CreateReviewRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    project_id: str = Field(..., alias="projectId")
    workspace_id: str | None = Field(None, alias="workspaceId")
    version_id: str | None = Field(None, alias="versionId")
    review_type: str = Field("internal", alias="reviewType")
    assignee_id: str | None = Field(None, alias="assigneeId")
    reviewer_id: str | None = Field(None, alias="reviewerId")
    title: str | None = None
    summary: str | None = None
    notes: str | None = None
    comment: str | None = None
    model_config = {"populate_by_name": True}


class DecideReviewRequest(BaseModel):
    review_id: str | None = Field(None, alias="reviewId")
    approval_id: str | None = Field(None, alias="approvalId")
    notes: str | None = None
    model_config = {"populate_by_name": True}


# --- Versions ---


@versions_router.get("/status")
async def versions_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().status()


@versions_router.get("/observability")
async def versions_observability(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().observability()


@versions_router.post("/create")
async def create_version(
    body: CreateVersionRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().versions.create(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@versions_router.post("/restore")
async def restore_version(
    body: RestoreVersionRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().rollbacks.restore(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@versions_router.get("/{project_id}")
async def list_versions(
    project_id: str,
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().versions.list(
            project_id, actor_id=actor, organization_id=organization_id
        )
    except Exception as exc:
        raise _map(exc) from exc


# --- Reviews ---


@reviews_router.post("/create")
async def create_review(
    body: CreateReviewRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().reviews.create(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@reviews_router.post("/approve")
async def approve_review(
    body: DecideReviewRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().reviews.approve(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@reviews_router.post("/reject")
async def reject_review(
    body: DecideReviewRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().reviews.reject(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@reviews_router.get("/history")
async def review_history(
    organization_id: str = Query(..., alias="organizationId"),
    project_id: str | None = Query(None, alias="projectId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().reviews.history(
            actor_id=actor,
            organization_id=organization_id,
            project_id=project_id,
        )
    except Exception as exc:
        raise _map(exc) from exc


# --- Changelog ---


@changelog_router.get("/{project_id}")
async def get_changelog(
    project_id: str,
    organization_id: str = Query(..., alias="organizationId"),
    limit: int = Query(100, ge=1, le=500),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _user(x_rtas_user_id)
    try:
        return _svc().changes.list(
            project_id,
            actor_id=actor,
            organization_id=organization_id,
            limit=limit,
        )
    except Exception as exc:
        raise _map(exc) from exc
