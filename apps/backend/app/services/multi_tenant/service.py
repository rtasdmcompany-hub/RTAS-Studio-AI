"""Multi-tenant SaaS foundation service / engine."""

from __future__ import annotations

from typing import Any

from app.services.multi_tenant.repository import (
    MultiTenantRepository,
    get_repository,
    reset_repository,
)
from app.services.multi_tenant.roles import SYSTEM_ROLE_KEYS, role_has_permission
from app.services.multi_tenant.validation import (
    ValidationError,
    validate_add_member,
    validate_create_invite,
    validate_create_organization,
    validate_create_team,
    validate_create_workspace,
    validate_role_key,
)
from app.services.multi_tenant.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    MAX_INVITES_PER_ORG,
    MAX_MEMBERS_PER_ORG,
    MAX_ORGS_PER_OWNER,
    MAX_TEAMS_PER_ORG,
    MAX_WORKSPACES_PER_ORG,
    PHASE,
    SPRINT,
)


class MultiTenantService:
    """Business logic for organizations, workspaces, teams, members, invites, RBAC."""

    def __init__(self, repo: MultiTenantRepository | None = None) -> None:
        self._repo = repo

    @property
    def repo(self) -> MultiTenantRepository:
        # Always resolve through the factory so resets cannot leave a stale repo handle.
        return self._repo or get_repository()

    def status(self) -> dict[str, Any]:
        stats = self.repo.stats()
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "roles": list(SYSTEM_ROLE_KEYS),
            "stats": stats,
            "limits": {
                "maxOrgsPerOwner": MAX_ORGS_PER_OWNER,
                "maxWorkspacesPerOrg": MAX_WORKSPACES_PER_ORG,
                "maxTeamsPerOrg": MAX_TEAMS_PER_ORG,
                "maxMembersPerOrg": MAX_MEMBERS_PER_ORG,
                "maxInvitesPerOrg": MAX_INVITES_PER_ORG,
            },
        }

    def create_organization(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = validate_create_organization(payload)
        if self.repo.get_organization_by_slug(data["slug"]):
            raise ValidationError(f"slug '{data['slug']}' is already taken")
        if self.repo.count_organizations_for_owner(data["owner_id"]) >= MAX_ORGS_PER_OWNER:
            raise ValidationError("organization limit reached for owner")
        org = self.repo.create_organization(**data)
        # Default workspace
        ws = self.repo.create_workspace(
            organization_id=org.id,
            name="Default",
            slug="default",
        )
        return {
            "ok": True,
            "organization": org.to_dict(),
            "defaultWorkspace": ws.to_dict(),
        }

    def list_organizations(self, *, owner_id: str | None = None) -> dict[str, Any]:
        orgs = self.repo.list_organizations(owner_id=owner_id)
        return {
            "ok": True,
            "count": len(orgs),
            "organizations": [o.to_dict() for o in orgs],
        }

    def get_organization(self, org_id: str) -> dict[str, Any]:
        org = self.repo.get_organization(org_id)
        if org is None:
            raise LookupError("organization not found")
        return {
            "ok": True,
            "organization": org.to_dict(),
            "workspaces": [w.to_dict() for w in self.repo.list_workspaces(org_id)],
            "teams": [t.to_dict() for t in self.repo.list_teams(org_id)],
            "members": [m.to_dict() for m in self.repo.list_members(org_id)],
        }

    def create_workspace(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = validate_create_workspace(payload)
        org = self.repo.get_organization(data["organization_id"])
        if org is None:
            raise LookupError("organization not found")
        if self.repo.get_workspace_by_slug(data["organization_id"], data["slug"]):
            raise ValidationError(f"workspace slug '{data['slug']}' already exists")
        if self.repo.count_workspaces(data["organization_id"]) >= MAX_WORKSPACES_PER_ORG:
            raise ValidationError("workspace limit reached for organization")
        ws = self.repo.create_workspace(**data)
        return {"ok": True, "workspace": ws.to_dict()}

    def list_workspaces(self, organization_id: str) -> dict[str, Any]:
        if self.repo.get_organization(organization_id) is None:
            raise LookupError("organization not found")
        items = self.repo.list_workspaces(organization_id)
        return {
            "ok": True,
            "organizationId": organization_id,
            "count": len(items),
            "workspaces": [w.to_dict() for w in items],
        }

    def create_team(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = validate_create_team(payload)
        org = self.repo.get_organization(data["organization_id"])
        if org is None:
            raise LookupError("organization not found")
        if data["workspace_id"]:
            ws = self.repo.get_workspace(data["workspace_id"])
            if ws is None or ws.organization_id != data["organization_id"]:
                raise ValidationError("workspace does not belong to organization")
        if self.repo.get_team_by_slug(data["organization_id"], data["slug"]):
            raise ValidationError(f"team slug '{data['slug']}' already exists")
        if self.repo.count_teams(data["organization_id"]) >= MAX_TEAMS_PER_ORG:
            raise ValidationError("team limit reached for organization")
        team = self.repo.create_team(**data)
        return {"ok": True, "team": team.to_dict()}

    def list_teams(
        self, organization_id: str, *, workspace_id: str | None = None
    ) -> dict[str, Any]:
        if self.repo.get_organization(organization_id) is None:
            raise LookupError("organization not found")
        items = self.repo.list_teams(organization_id, workspace_id=workspace_id)
        return {
            "ok": True,
            "organizationId": organization_id,
            "count": len(items),
            "teams": [t.to_dict() for t in items],
        }

    def add_team_member(
        self, *, team_id: str, user_id: str
    ) -> dict[str, Any]:
        team = self.repo.get_team(team_id)
        if team is None:
            raise LookupError("team not found")
        member = self.repo.get_member_by_org_user(team.organization_id, user_id)
        if member is None:
            raise ValidationError("user is not a member of the organization")
        tm = self.repo.add_team_member(team_id=team_id, user_id=user_id)
        return {"ok": True, "teamMember": tm.to_dict()}

    def add_member(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = validate_add_member(payload)
        org = self.repo.get_organization(data["organization_id"])
        if org is None:
            raise LookupError("organization not found")
        if data["workspace_id"]:
            ws = self.repo.get_workspace(data["workspace_id"])
            if ws is None or ws.organization_id != data["organization_id"]:
                raise ValidationError("workspace does not belong to organization")
        if self.repo.count_members(data["organization_id"]) >= MAX_MEMBERS_PER_ORG:
            raise ValidationError("member limit reached for organization")
        existing = self.repo.get_member_by_org_user(
            data["organization_id"], data["user_id"]
        )
        if existing:
            raise ValidationError("user is already a member of the organization")
        member = self.repo.add_member(**data)
        return {"ok": True, "member": member.to_dict()}

    def list_members(
        self, organization_id: str, *, workspace_id: str | None = None
    ) -> dict[str, Any]:
        if self.repo.get_organization(organization_id) is None:
            raise LookupError("organization not found")
        items = self.repo.list_members(organization_id, workspace_id=workspace_id)
        return {
            "ok": True,
            "organizationId": organization_id,
            "count": len(items),
            "members": [m.to_dict() for m in items],
        }

    def update_member_role(self, member_id: str, role: str) -> dict[str, Any]:
        role_key = validate_role_key(role)
        member = self.repo.get_member(member_id)
        if member is None:
            raise LookupError("member not found")
        if member.role_key == "owner" and role_key != "owner":
            raise ValidationError("cannot demote organization owner via role update")
        updated = self.repo.update_member_role(member_id, role_key)
        assert updated is not None
        return {"ok": True, "member": updated.to_dict()}

    def create_invite(self, payload: dict[str, Any]) -> dict[str, Any]:
        data = validate_create_invite(payload)
        org = self.repo.get_organization(data["organization_id"])
        if org is None:
            raise LookupError("organization not found")
        if data["workspace_id"]:
            ws = self.repo.get_workspace(data["workspace_id"])
            if ws is None or ws.organization_id != data["organization_id"]:
                raise ValidationError("workspace does not belong to organization")
        if self.repo.count_invites(data["organization_id"]) >= MAX_INVITES_PER_ORG:
            raise ValidationError("invite limit reached for organization")
        invite = self.repo.create_invite(**data)
        return {"ok": True, "invite": invite.to_dict()}

    def list_invites(
        self, organization_id: str, *, status: str | None = None
    ) -> dict[str, Any]:
        if self.repo.get_organization(organization_id) is None:
            raise LookupError("organization not found")
        items = self.repo.list_invites(organization_id, status=status)
        return {
            "ok": True,
            "organizationId": organization_id,
            "count": len(items),
            "invites": [i.to_dict() for i in items],
        }

    def accept_invite(self, token: str, user_id: str) -> dict[str, Any]:
        if not token or not str(token).strip():
            raise ValidationError("token is required")
        if not user_id or not str(user_id).strip():
            raise ValidationError("userId is required")
        try:
            result = self.repo.accept_invite(str(token).strip(), str(user_id).strip())
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return {
            "ok": True,
            "invite": result["invite"].to_dict(),
            "member": result["member"].to_dict(),
        }

    def list_roles(self, *, organization_id: str | None = None) -> dict[str, Any]:
        roles = self.repo.list_roles(organization_id=organization_id)
        return {
            "ok": True,
            "count": len(roles),
            "roles": [r.to_dict() for r in roles],
        }

    def list_permissions(self) -> dict[str, Any]:
        perms = self.repo.list_permissions()
        return {
            "ok": True,
            "count": len(perms),
            "permissions": [p.to_dict() for p in perms],
        }

    def check_permission(
        self, *, organization_id: str, user_id: str, permission: str
    ) -> dict[str, Any]:
        member = self.repo.get_member_by_org_user(organization_id, user_id)
        if member is None:
            return {
                "ok": True,
                "allowed": False,
                "reason": "not_a_member",
            }
        allowed = role_has_permission(member.role_key, permission)
        return {
            "ok": True,
            "allowed": allowed,
            "roleKey": member.role_key,
            "permission": permission,
        }


_service: MultiTenantService | None = None


def get_multi_tenant_service() -> MultiTenantService:
    global _service
    if _service is None:
        _service = MultiTenantService()
    return _service


def reset_engine() -> None:
    global _service
    reset_repository()
    _service = None


# Aliases used by routes / package exports
get_engine = get_multi_tenant_service
