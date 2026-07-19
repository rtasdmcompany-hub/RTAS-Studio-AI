"""Multi-tenant organization / workspace / team / member / invite APIs."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Header, HTTPException, Query
from pydantic import BaseModel, Field

from app.core.backend_auth import require_backend_secret
from app.core.config import settings
from app.services import multi_tenant as mt
from app.services.enterprise_auth.errors import AccessError
from app.services.enterprise_auth.middleware import require_access
from app.services.multi_tenant.validation import ValidationError

router = APIRouter(prefix="/organizations", tags=["multi-tenant"])


def _require_backend_auth(x_rtas_backend_secret: str | None) -> None:
    require_backend_secret(x_rtas_backend_secret=x_rtas_backend_secret)


def _svc():
    return mt.get_multi_tenant_service()


def _map_error(exc: Exception) -> HTTPException:
    if isinstance(exc, AccessError):
        return HTTPException(
            status_code=exc.status_code,
            detail={"error": exc.code, "message": exc.message},
        )
    if isinstance(exc, ValidationError):
        return HTTPException(status_code=400, detail=str(exc))
    if isinstance(exc, LookupError):
        return HTTPException(status_code=404, detail=str(exc))
    return HTTPException(status_code=500, detail="Multi-tenant operation failed")


def _enforce_tenant_access(
    *,
    organization_id: str | None,
    user_id: str | None,
    session_token: str | None,
    permission: str | None = None,
    workspace_id: str | None = None,
    require_context: bool = False,
) -> None:
    """Validate organization context when actor/session headers are present."""
    if not user_id and not session_token:
        if require_context:
            raise HTTPException(
                status_code=401,
                detail={"error": "unauthorized", "message": "X-Rtas-User-Id or X-Rtas-Session required"},
            )
        return
    if not organization_id and not session_token:
        raise HTTPException(
            status_code=403,
            detail={"error": "forbidden", "message": "organization context is required"},
        )
    try:
        require_access(
            user_id=user_id,
            organization_id=organization_id,
            workspace_id=workspace_id,
            session_token=session_token,
            permission=permission,
        )
    except AccessError as exc:
        raise _map_error(exc) from exc


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
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        return _om().organizations.create(
            body.model_dump(by_alias=True),
            actor_id=x_rtas_user_id or body.owner_id,
        )
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
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
    x_rtas_session: str | None = Header(None, alias="X-Rtas-Session"),
):
    _require_backend_auth(x_rtas_backend_secret)
    _enforce_tenant_access(
        organization_id=body.organization_id,
        user_id=x_rtas_user_id,
        session_token=x_rtas_session,
        permission="workspace.create",
    )
    try:
        return _svc().create_workspace(body.model_dump(by_alias=True))
    except Exception as exc:
        raise _map_error(exc) from exc


@router.get("/workspaces")
async def list_workspaces(
    organization_id: str = Query(..., alias="organizationId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
    x_rtas_session: str | None = Header(None, alias="X-Rtas-Session"),
):
    _require_backend_auth(x_rtas_backend_secret)
    _enforce_tenant_access(
        organization_id=organization_id,
        user_id=x_rtas_user_id,
        session_token=x_rtas_session,
        permission="workspace.read",
    )
    try:
        return _svc().list_workspaces(organization_id)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/teams")
async def create_team(
    body: CreateTeamRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
    x_rtas_session: str | None = Header(None, alias="X-Rtas-Session"),
):
    _require_backend_auth(x_rtas_backend_secret)
    _enforce_tenant_access(
        organization_id=body.organization_id,
        user_id=x_rtas_user_id,
        session_token=x_rtas_session,
        permission="team.create",
        workspace_id=body.workspace_id,
    )
    try:
        return _svc().create_team(body.model_dump(by_alias=True))
    except Exception as exc:
        raise _map_error(exc) from exc


@router.get("/teams")
async def list_teams(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
    x_rtas_session: str | None = Header(None, alias="X-Rtas-Session"),
):
    _require_backend_auth(x_rtas_backend_secret)
    _enforce_tenant_access(
        organization_id=organization_id,
        user_id=x_rtas_user_id,
        session_token=x_rtas_session,
        permission="team.read",
        workspace_id=workspace_id,
    )
    try:
        return _svc().list_teams(organization_id, workspace_id=workspace_id)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/teams/members")
async def add_team_member(
    body: AddTeamMemberRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
    x_rtas_session: str | None = Header(None, alias="X-Rtas-Session"),
):
    _require_backend_auth(x_rtas_backend_secret)
    if x_rtas_user_id or x_rtas_session:
        from app.services.multi_tenant.repository import get_repository

        team = get_repository().get_team(body.team_id)
        if team is None:
            raise HTTPException(status_code=404, detail="team not found")
        _enforce_tenant_access(
            organization_id=team.organization_id,
            user_id=x_rtas_user_id,
            session_token=x_rtas_session,
            permission="team.update",
        )
    try:
        return _svc().add_team_member(team_id=body.team_id, user_id=body.user_id)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/members")
async def add_member(
    body: AddMemberRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
    x_rtas_session: str | None = Header(None, alias="X-Rtas-Session"),
):
    _require_backend_auth(x_rtas_backend_secret)
    _enforce_tenant_access(
        organization_id=body.organization_id,
        user_id=x_rtas_user_id,
        session_token=x_rtas_session,
        permission="member.invite",
        workspace_id=body.workspace_id,
    )
    try:
        return _svc().add_member(body.model_dump(by_alias=True))
    except Exception as exc:
        raise _map_error(exc) from exc


@router.get("/members")
async def list_members(
    organization_id: str = Query(..., alias="organizationId"),
    workspace_id: str | None = Query(None, alias="workspaceId"),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
    x_rtas_session: str | None = Header(None, alias="X-Rtas-Session"),
):
    _require_backend_auth(x_rtas_backend_secret)
    _enforce_tenant_access(
        organization_id=organization_id,
        user_id=x_rtas_user_id,
        session_token=x_rtas_session,
        permission="member.read",
        workspace_id=workspace_id,
    )
    try:
        return _svc().list_members(organization_id, workspace_id=workspace_id)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.patch("/members/{member_id}/role")
async def update_member_role(
    member_id: str,
    body: UpdateMemberRoleRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
    x_rtas_session: str | None = Header(None, alias="X-Rtas-Session"),
):
    _require_backend_auth(x_rtas_backend_secret)
    if x_rtas_user_id or x_rtas_session:
        from app.services.multi_tenant.repository import get_repository

        member = get_repository().get_member(member_id)
        if member is None:
            raise HTTPException(status_code=404, detail="member not found")
        _enforce_tenant_access(
            organization_id=member.organization_id,
            user_id=x_rtas_user_id,
            session_token=x_rtas_session,
            permission="role.assign",
        )
    try:
        return _svc().update_member_role(member_id, body.role)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/invites")
async def create_invite(
    body: CreateInviteRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
    x_rtas_session: str | None = Header(None, alias="X-Rtas-Session"),
):
    _require_backend_auth(x_rtas_backend_secret)
    actor = x_rtas_user_id or body.invited_by_id
    _enforce_tenant_access(
        organization_id=body.organization_id,
        user_id=actor,
        session_token=x_rtas_session,
        permission="member.invite",
        workspace_id=body.workspace_id,
    )
    try:
        return _svc().create_invite(body.model_dump(by_alias=True))
    except Exception as exc:
        raise _map_error(exc) from exc


@router.get("/invites")
async def list_invites(
    organization_id: str = Query(..., alias="organizationId"),
    status: str | None = Query(None),
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
    x_rtas_session: str | None = Header(None, alias="X-Rtas-Session"),
):
    _require_backend_auth(x_rtas_backend_secret)
    _enforce_tenant_access(
        organization_id=organization_id,
        user_id=x_rtas_user_id,
        session_token=x_rtas_session,
        permission="member.read",
    )
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


class UpdateOrganizationRequest(BaseModel):
    name: str | None = None
    slug: str | None = None
    plan: str | None = None
    status: str | None = None
    metadata: dict[str, Any] | None = None


class TransferOwnershipRequest(BaseModel):
    new_owner_id: str = Field(..., alias="newOwnerId", min_length=1)
    model_config = {"populate_by_name": True}


class OrgSettingsRequest(BaseModel):
    timezone: str | None = None
    locale: str | None = None
    allow_invites: bool | None = Field(None, alias="allowInvites")
    default_role: str | None = Field(None, alias="defaultRole")
    settings: dict[str, Any] | None = None
    model_config = {"populate_by_name": True}


def _om():
    from app.services import org_management as om

    return om.get_org_management_service()


@router.patch("/{org_id}")
async def update_organization(
    org_id: str,
    body: UpdateOrganizationRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _require_backend_auth(x_rtas_backend_secret)
    if not x_rtas_user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    try:
        return _om().organizations.update(
            org_id, body.model_dump(exclude_none=True), actor_id=x_rtas_user_id
        )
    except Exception as exc:
        raise _map_error(exc) from exc


@router.delete("/{org_id}")
async def delete_organization(
    org_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _require_backend_auth(x_rtas_backend_secret)
    if not x_rtas_user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    try:
        return _om().organizations.delete(org_id, actor_id=x_rtas_user_id)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/{org_id}/transfer")
async def transfer_ownership(
    org_id: str,
    body: TransferOwnershipRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _require_backend_auth(x_rtas_backend_secret)
    if not x_rtas_user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    try:
        return _om().organizations.transfer_ownership(
            org_id, actor_id=x_rtas_user_id, new_owner_id=body.new_owner_id
        )
    except Exception as exc:
        raise _map_error(exc) from exc


@router.get("/{org_id}/settings")
async def get_org_settings(
    org_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _require_backend_auth(x_rtas_backend_secret)
    if x_rtas_user_id:
        _enforce_tenant_access(
            organization_id=org_id,
            user_id=x_rtas_user_id,
            session_token=None,
            permission="org.read",
        )
    return {"ok": True, "settings": _om().settings.get_org_settings(org_id)}


@router.patch("/{org_id}/settings")
async def update_org_settings(
    org_id: str,
    body: OrgSettingsRequest,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _require_backend_auth(x_rtas_backend_secret)
    if not x_rtas_user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    try:
        return _om().settings.update_org_settings(
            org_id, body.model_dump(by_alias=True, exclude_none=True), actor_id=x_rtas_user_id
        )
    except Exception as exc:
        raise _map_error(exc) from exc


@router.delete("/members/{member_id}")
async def remove_member(
    member_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _require_backend_auth(x_rtas_backend_secret)
    if not x_rtas_user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    try:
        return _om().members.remove(member_id, actor_id=x_rtas_user_id)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/members/{member_id}/suspend")
async def suspend_member(
    member_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _require_backend_auth(x_rtas_backend_secret)
    if not x_rtas_user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    try:
        return _om().members.suspend(member_id, actor_id=x_rtas_user_id)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.post("/members/{member_id}/reactivate")
async def reactivate_member(
    member_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _require_backend_auth(x_rtas_backend_secret)
    if not x_rtas_user_id:
        raise HTTPException(status_code=401, detail="X-Rtas-User-Id required")
    try:
        return _om().members.reactivate(member_id, actor_id=x_rtas_user_id)
    except Exception as exc:
        raise _map_error(exc) from exc


@router.get("/{org_id}")
async def get_organization(
    org_id: str,
    x_rtas_backend_secret: str | None = Header(None, alias="X-Rtas-Backend-Secret"),
    x_rtas_user_id: str | None = Header(None, alias="X-Rtas-User-Id"),
):
    _require_backend_auth(x_rtas_backend_secret)
    try:
        if x_rtas_user_id:
            return _om().organizations.get(org_id, actor_id=x_rtas_user_id)
        return _svc().get_organization(org_id)
    except Exception as exc:
        raise _map_error(exc) from exc
