"""Multi-tenant organization / workspace / team / member / invite APIs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.config import settings
from app.services import multi_tenant as mt
from app.services.multi_tenant.validation import ValidationError

router = APIRouter(prefix="/organizations", tags=["multi-tenant"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    expected = (settings.ai_backend_secret or "").strip()
    if not expected:
        return
    if (x_rtas_backend_secret or "").strip() != expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _svc():
    return mt.get_multi_tenant_service()


def _map_error(exc: Exception) -> HTTPException:
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, LookupError):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=500, detail="Multi-tenant operation failed")


class CreateOrganizationRequest(BaseModel):
    name: str = Field(..., min_length=1)
    owner_id: str = Field(..., alias="ownerId", min_length=1)
    slug: str | None = None
    plan: str | None = "free"
    metadata: dict[str, Any] | None = None

    model_config = {"populate_by_name": True}


class CreateWorkspaceRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId", min_length=1)
    name: str = Field(..., min_length=1)
    slug: str | None = None
    metadata: dict[str, Any] | None = None

    model_config = {"populate_by_name": True}


class CreateTeamRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId", min_length=1)
    name: str = Field(..., min_length=1)
    slug: str | None = None
    workspace_id: str | None = Field(None, alias="workspaceId")

    model_config = {"populate_by_name": True}


class AddMemberRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId", min_length=1)
    user_id: str = Field(..., alias="userId", min_length=1)
    role: str = "viewer"
    workspace_id: str | None = Field(None, alias="workspaceId")

    model_config = {"populate_by_name": True}


class UpdateMemberRoleRequest(BaseModel):
    role: str = Field(..., min_length=1)


class AddTeamMemberRequest(BaseModel):
    team_id: str = Field(..., alias="teamId", min_length=1)
    user_id: str = Field(..., alias="userId", min_length=1)

    model_config = {"populate_by_name": True}


class CreateInviteRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId", min_length=1)
    email: str = Field(..., min_length=3)
    invited_by_id: str = Field(..., alias="invitedById", min_length=1)
    role: str = "viewer"
    workspace_id: str | None = Field(None, alias="workspaceId")

    model_config = {"populate_by_name": True}


class AcceptInviteRequest(BaseModel):
    token: str = Field(..., min_length=1)
    user_id: str = Field(..., alias="userId", min_length=1)

    model_config = {"populate_by_name": True}


class CheckPermissionRequest(BaseModel):
    organization_id: str = Field(..., alias="organizationId", min_length=1)
    user_id: str = Field(..., alias="userId", min_length=1)
    permission: str = Field(..., min_length=1)

    model_config = {"populate_by_name": True}


@router.get("/status")
async def organizations_status(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return _svc().status()


@router.post("")
async def create_organization(
    body: CreateOrganizationRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().create_organization(body.model_dump(by_alias=True))
    except Exception as exc:
        raise _map_error(exc) from exc


@router.get("")
async def list_organizations(
    owner_id: str | None = Query(None, alias="ownerId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return _svc().list_organizations(owner_id=owner_id)


@router.get("/roles")
async def list_roles(
    organization_id: str | None = Query(None, alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return _svc().list_roles(organization_id=organization_id)


@router.get("/permissions")
async def list_permissions(
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return _svc().list_permissions()


@router.post("/workspaces")
async def create_workspace(
    body: CreateWorkspaceRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().create_workspace(body.model_dump(by_alias=True))
    except Exception as exc:
        raise _map_error(exc) from exc


@router.get("/workspaces")
async def list_workspaces(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().list_workspaces(organization_id)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/teams")
async def create_team(
    body: CreateTeamRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().create_team(body.model_dump(by_alias=True))
    except Exception as exc:
        raise _map_error(exc) from exc


@router.get("/teams")
async def list_teams(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().list_teams(organization_id, workspace_id=workspace_id)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/teams/members")
async def add_team_member(
    body: AddTeamMemberRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().add_team_member(team_id=body.team_id, user_id=body.user_id)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/members")
async def add_member(
    body: AddMemberRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().add_member(body.model_dump(by_alias=True))
    except Exception as exc:
        raise _map_error(exc) from exc


@router.get("/members")
async def list_members(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().list_members(organization_id, workspace_id=workspace_id)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.patch("/members/{member_id}/role")
async def update_member_role(
    member_id: str,
    body: UpdateMemberRoleRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().update_member_role(member_id, body.role)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/invites")
async def create_invite(
    body: CreateInviteRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().create_invite(body.model_dump(by_alias=True))
    except Exception as exc:
        raise _map_error(exc) from exc


@router.get("/invites")
async def list_invites(
    organization_id: str = Query(..., alias="organizationId"),
    status: str | None = Query(None),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().list_invites(organization_id, status=status)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/invites/accept")
async def accept_invite(
    body: AcceptInviteRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().accept_invite(body.token, body.user_id)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/permissions/check")
async def check_permission(
    body: CheckPermissionRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    return _svc().check_permission(
        organization_id=body.organization_id,
        user_id=body.user_id,
        permission=body.permission,
    )


@router.get("/{org_id}")
async def get_organization(
    org_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _svc().get_organization(org_id)
    except Exception as exc:
        raise _map_error(exc) from exc
