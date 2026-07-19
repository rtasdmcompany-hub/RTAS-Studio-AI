"""Workspace Management APIs — Phase 7 Sprint 3."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.backend_auth import require_backend_secret
from app.core.config import settings
from app.services import org_management as om
from app.services.multi_tenant.validation import ValidationError
from app.services.org_management.security import AccessError

router = APIRouter(prefix="/workspaces", tags=["workspace-management"])


def _auth(secret: str | None) -> None:
    require_backend_secret(x_rtas_backend_secret=secret)


def _svc():
    return om.get_org_management_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, LookupError):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=500, detail="Workspace operation failed")


class CreateWorkspaceRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    name: str
    slug: str | None = None
    metadata: dict[str, Any] | None = None
    model_config = {"populate_by_name": True}


class UpdateWorkspaceRequest(BaseModel):
    name: str | None = None
    slug: str | None = None
    status: str | None = None
    metadata: dict[str, Any] | None = None


class WorkspaceSettingsRequest(BaseModel):
    visibility: str | None = None
    default_model: str | None = Field(None, alias="defaultModel")
    settings: dict[str, Any] | None = None
    model_config = {"populate_by_name": True}


@router.get("/status")
async def workspace_engine_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    status = _svc().status()
    return {
        "ok": True,
        "engine": "workspace",
        "status": status["engines"]["workspace"],
        "phase": status["phase"],
        "sprint": status["sprint"],
    }


@router.post("")
async def create_workspace(
    body: CreateWorkspaceRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    if not x_rtas_user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    try:
        return _svc().workspaces.create(
            body.model_dump(by_alias=True), actor_id=x_rtas_user_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.get("")
async def list_workspaces(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    try:
        return _svc().workspaces.list(organization_id, actor_id=x_rtas_user_id)
    except Exception as exc:
        raise _map(exc) from exc


@router.patch("/{workspace_id}")
async def update_workspace(
    workspace_id: str,
    body: UpdateWorkspaceRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    if not x_rtas_user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    try:
        return _svc().workspaces.update(
            workspace_id, body.model_dump(exclude_none=True), actor_id=x_rtas_user_id
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/{workspace_id}/archive")
async def archive_workspace(
    workspace_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    if not x_rtas_user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    try:
        return _svc().workspaces.archive(workspace_id, actor_id=x_rtas_user_id)
    except Exception as exc:
        raise _map(exc) from exc


@router.delete("/{workspace_id}")
async def delete_workspace(
    workspace_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    if not x_rtas_user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    try:
        return _svc().workspaces.delete(workspace_id, actor_id=x_rtas_user_id)
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/{workspace_id}/members")
async def workspace_members(
    workspace_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    if not x_rtas_user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    try:
        return _svc().workspaces.members(workspace_id, actor_id=x_rtas_user_id)
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/{workspace_id}/activity")
async def workspace_activity(
    workspace_id: str,
    limit: int = Query(50, ge=1, le=200),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    if not x_rtas_user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    try:
        return _svc().workspaces.activity(
            workspace_id, actor_id=x_rtas_user_id, limit=limit
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.patch("/{workspace_id}/settings")
async def workspace_settings(
    workspace_id: str,
    body: WorkspaceSettingsRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    if not x_rtas_user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    try:
        return _svc().settings.update_ws_settings(
            workspace_id, body.model_dump(by_alias=True, exclude_none=True), actor_id=x_rtas_user_id
        )
    except Exception as exc:
        raise _map(exc) from exc
