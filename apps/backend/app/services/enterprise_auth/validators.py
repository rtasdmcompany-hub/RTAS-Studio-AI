"""Organization, workspace, team, membership, and ownership validators."""

from __future__ import annotations

from typing import Any

from app.services.enterprise_auth.errors import ForbiddenError, NotFoundError
from app.services.enterprise_auth.permission_engine import get_permission_engine
from app.services.multi_tenant.repository import get_repository


def validate_organization_access(
    *,
    organization_id: str,
    user_id: str,
    require_permission: str | None = None,
) -> dict[str, Any]:
    repo = get_repository()
    org = repo.get_organization(organization_id)
    if org is None:
        raise NotFoundError("organization not found")
    member = repo.get_member_by_org_user(organization_id, user_id)
    if member is None or member.status != "active":
        raise ForbiddenError("not a member of this organization")
    engine = get_permission_engine()
    if require_permission and not engine.has_permission(member.role_key, require_permission):
        raise ForbiddenError(f"missing permission: {require_permission}")
    return {
        "ok": True,
        "organization": org.to_dict(),
        "member": member.to_dict(),
        "roleKey": member.role_key,
        "isOwner": org.owner_id == user_id or member.role_key == "owner",
        "permissions": engine.permissions_for(member.role_key),
    }


def validate_organization_ownership(*, organization_id: str, user_id: str) -> dict[str, Any]:
    repo = get_repository()
    org = repo.get_organization(organization_id)
    if org is None:
        raise NotFoundError("organization not found")
    if org.owner_id != user_id:
        # Also allow role=owner membership
        member = repo.get_member_by_org_user(organization_id, user_id)
        if member is None or member.role_key != "owner":
            raise ForbiddenError("organization ownership required")
    return {
        "ok": True,
        "organizationId": organization_id,
        "ownerId": org.owner_id,
        "isOwner": True,
    }


def validate_workspace_membership(
    *,
    organization_id: str,
    workspace_id: str,
    user_id: str,
    require_permission: str | None = "workspace.read",
) -> dict[str, Any]:
    repo = get_repository()
    org_access = validate_organization_access(
        organization_id=organization_id,
        user_id=user_id,
        require_permission=require_permission,
    )
    ws = repo.get_workspace(workspace_id)
    if ws is None:
        raise NotFoundError("workspace not found")
    if ws.organization_id != organization_id:
        raise ForbiddenError("workspace does not belong to organization")
    member = repo.get_member_by_org_user(organization_id, user_id)
    assert member is not None
    # Workspace-scoped members may only access their assigned workspace
    # (unless owner/admin — full org access)
    engine = get_permission_engine()
    if (
        member.workspace_id
        and member.workspace_id != workspace_id
        and not engine.is_admin_or_above(member.role_key)
    ):
        raise ForbiddenError("not a member of this workspace")
    return {
        "ok": True,
        "organization": org_access["organization"],
        "workspace": ws.to_dict(),
        "member": member.to_dict(),
        "roleKey": member.role_key,
        "permissions": org_access["permissions"],
    }


def validate_team_access(
    *,
    team_id: str,
    user_id: str,
    require_org_member: bool = True,
) -> dict[str, Any]:
    repo = get_repository()
    team = repo.get_team(team_id)
    if team is None:
        raise NotFoundError("team not found")
    if require_org_member:
        validate_organization_access(
            organization_id=team.organization_id,
            user_id=user_id,
            require_permission="team.read",
        )
    team_members = repo.list_team_members(team_id)
    is_team_member = any(tm.user_id == user_id and tm.status == "active" for tm in team_members)
    member = repo.get_member_by_org_user(team.organization_id, user_id)
    engine = get_permission_engine()
    # Admins/owners can access any team; others need team membership or org membership with team.read
    if not is_team_member and member and not engine.is_admin_or_above(member.role_key):
        # Org members with team.read can still view team metadata
        if not engine.has_permission(member.role_key, "team.read"):
            raise ForbiddenError("not a member of this team")
    return {
        "ok": True,
        "team": team.to_dict(),
        "isTeamMember": is_team_member,
        "roleKey": member.role_key if member else None,
        "organizationId": team.organization_id,
    }
