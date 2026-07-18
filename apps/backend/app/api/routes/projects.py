"""Project Management & Collaboration APIs — Phase 7 Sprint 4."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import project_collaboration as pc
from app.services.enterprise_auth.errors import AccessError
from app.services.multi_tenant.validation import ValidationError

router = APIRouter(prefix="/projects", tags=["project-collaboration"])


def _auth(secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if expected and (secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _svc():
    return pc.get_project_collaboration_service()


def _map(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    return HTTPException(status_code=500, detail="Project operation failed")


def _require_user(user_id: str | None) -> str:
    if not user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    return user_id


class CreateProjectRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId")
    name: str
    owner_id: str | None = Field(None, alias="ownerId")
    workspace_id: str | None = Field(None, alias="workspaceId")
    slug: str | None = None
    description: str | None = None
    status: str | None = "draft"
    template: str | None = "blank"
    is_shared: bool = Field(False, alias="isShared")
    metadata: dict[str, Any] | None = None
    model_config = {"populate_by_name": True}


class UpdateProjectRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    status: str | None = None
    is_shared: bool | None = Field(None, alias="isShared")
    metadata: dict[str, Any] | None = None
    model_config = {"populate_by_name": True}


class AddMemberRequest(BaseModel):
    user_id: str = Field(..., alias="userId")
    role: str = "contributor"
    model_config = {"populate_by_name": True}


class RemoveMemberRequest(BaseModel):
    user_id: str = Field(..., alias="userId")
    model_config = {"populate_by_name": True}


class NoteRequest(BaseModel):
    body: str
    is_internal: bool = Field(True, alias="isInternal")
    model_config = {"populate_by_name": True}


class TaskRequest(BaseModel):
    title: str
    description: str | None = None
    assignee_id: str | None = Field(None, alias="assigneeId")
    model_config = {"populate_by_name": True}


class TimelineEmitRequest(BaseModel):
    action: str
    event_type: str = Field(..., alias="eventType")
    summary: str
    detail: str | None = None
    metadata: dict[str, Any] | None = None
    model_config = {"populate_by_name": True}


@router.get("/status")
async def projects_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().status()


@router.get("/observability")
async def projects_observability(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().observability()


@router.get("/templates")
async def project_templates(
    organization_id: str | None = Query(None, alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().projects.templates(organization_id=organization_id)


@router.get("/roles")
async def project_roles(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _auth(x_rtas_backend_secret)
    return _svc().collaboration.roles()


@router.post("")
async def create_project(
    body: CreateProjectRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _require_user(x_rtas_user_id or body.owner_id)
    try:
        return _svc().projects.create(body.model_dump(by_alias=True), actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.get("")
async def list_projects(
    organization_id: str | None = Query(None, alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    owner_id: str | None = Query(None, alias="ownerId"),
    status: str | None = Query(None),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    try:
        return _svc().projects.list(
            {
                "organizationId": organization_id,
                "workspaceId": workspace_id,
                "ownerId": owner_id,
                "status": status,
            },
            actor_id=x_rtas_user_id,
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/{project_id}")
async def get_project(
    project_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _require_user(x_rtas_user_id)
    try:
        return _svc().projects.get(project_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.patch("/{project_id}")
async def update_project(
    project_id: str,
    body: UpdateProjectRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _require_user(x_rtas_user_id)
    try:
        return _svc().projects.update(
            project_id, body.model_dump(by_alias=True, exclude_none=True), actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.delete("/{project_id}")
async def delete_project(
    project_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _require_user(x_rtas_user_id)
    try:
        return _svc().archive.soft_delete(project_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/{project_id}/duplicate")
async def duplicate_project(
    project_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _require_user(x_rtas_user_id)
    try:
        return _svc().projects.duplicate(project_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/{project_id}/archive")
async def archive_project(
    project_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _require_user(x_rtas_user_id)
    try:
        return _svc().archive.archive(project_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/{project_id}/restore")
async def restore_project(
    project_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _require_user(x_rtas_user_id)
    try:
        return _svc().archive.restore(project_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/{project_id}/favorite")
async def favorite_project(
    project_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _require_user(x_rtas_user_id)
    try:
        return _svc().projects.favorite(project_id, actor_id=actor, favorite=True)
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/{project_id}/members")
async def add_project_member(
    project_id: str,
    body: AddMemberRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _require_user(x_rtas_user_id)
    try:
        return _svc().collaboration.add_member(
            project_id, user_id=body.user_id, role_key=body.role, actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.delete("/{project_id}/members")
async def remove_project_member(
    project_id: str,
    body: RemoveMemberRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _require_user(x_rtas_user_id)
    try:
        return _svc().collaboration.remove_member(
            project_id, body.user_id, actor_id=actor
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/{project_id}/activity")
async def project_activity(
    project_id: str,
    limit: int = Query(50, ge=1, le=200),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _require_user(x_rtas_user_id)
    try:
        return _svc().timeline.activity(project_id, actor_id=actor, limit=limit)
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/{project_id}/timeline")
async def project_timeline(
    project_id: str,
    limit: int = Query(50, ge=1, le=200),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _require_user(x_rtas_user_id)
    try:
        return _svc().timeline.timeline(project_id, actor_id=actor, limit=limit)
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/{project_id}/timeline/emit")
async def emit_timeline(
    project_id: str,
    body: TimelineEmitRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _require_user(x_rtas_user_id)
    try:
        return _svc().timeline.emit(
            project_id,
            actor_id=actor,
            action=body.action,
            event_type=body.event_type,
            summary=body.summary,
            detail=body.detail,
            metadata=body.metadata,
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/{project_id}/notes")
async def add_note(
    project_id: str,
    body: NoteRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _require_user(x_rtas_user_id)
    try:
        return _svc().collaboration.add_note(
            project_id, body=body.body, actor_id=actor, is_internal=body.is_internal
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/{project_id}/notes")
async def list_notes(
    project_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _require_user(x_rtas_user_id)
    try:
        return _svc().collaboration.list_notes(project_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc


@router.post("/{project_id}/tasks")
async def assign_task(
    project_id: str,
    body: TaskRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _require_user(x_rtas_user_id)
    try:
        return _svc().tasks.assign(
            project_id,
            title=body.title,
            actor_id=actor,
            assignee_id=body.assignee_id,
            description=body.description,
        )
    except Exception as exc:
        raise _map(exc) from exc


@router.get("/{project_id}/tasks")
async def list_tasks(
    project_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _auth(x_rtas_backend_secret)
    actor = _require_user(x_rtas_user_id)
    try:
        return _svc().tasks.list(project_id, actor_id=actor)
    except Exception as exc:
        raise _map(exc) from exc
