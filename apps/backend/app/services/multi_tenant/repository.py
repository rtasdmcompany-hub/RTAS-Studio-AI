"""Repository layer over the multi-tenant store."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from secrets import token_urlsafe
from typing import Any

from app.services.multi_tenant import store
from app.services.multi_tenant.models import (
    Invite,
    Member,
    Organization,
    Permission,
    Role,
    Team,
    TeamMember,
    Workspace,
    new_id,
)
from app.services.multi_tenant.roles import (
    PERMISSION_CATALOG,
    ROLE_PERMISSIONS,
    SYSTEM_ROLES,
)
from app.services.multi_tenant.version import DEFAULT_INVITE_TTL_HOURS


class MultiTenantRepository:
    """Persistence abstraction for organizations, workspaces, teams, RBAC, invites."""

    def ensure_system_rbac(self) -> None:
        if store.is_seeded():
            return
        for key, name, category in PERMISSION_CATALOG:
            if store.get_permission_by_key(key) is None:
                store.save_permission(
                    Permission(
                        id=new_id("perm_"),
                        key=key,
                        name=name,
                        category=category,
                        description=name,
                    )
                )
        for spec in SYSTEM_ROLES:
            existing = store.get_role_by_key(spec["key"], organization_id=None)
            if existing is None:
                store.save_role(
                    Role(
                        id=new_id("role_"),
                        key=spec["key"],
                        name=spec["name"],
                        description=spec["description"],
                        organization_id=None,
                        is_system=True,
                        rank=spec["rank"],
                        permission_keys=sorted(ROLE_PERMISSIONS.get(spec["key"], frozenset())),
                    )
                )
        store.mark_seeded()

    # --- Organizations ---

    def create_organization(
        self,
        *,
        name: str,
        slug: str,
        owner_id: str,
        plan: str = "free",
        metadata: dict[str, Any] | None = None,
    ) -> Organization:
        self.ensure_system_rbac()
        org = Organization(
            id=new_id("org_"),
            name=name,
            slug=slug,
            owner_id=owner_id,
            plan=plan,
            metadata=dict(metadata or {}),
        )
        store.save_organization(org)
        owner_role = store.get_role_by_key("owner")
        assert owner_role is not None
        self.add_member(
            organization_id=org.id,
            user_id=owner_id,
            role_key="owner",
            workspace_id=None,
        )
        return org

    def get_organization(self, org_id: str) -> Organization | None:
        return store.get_organization(org_id)

    def get_organization_by_slug(self, slug: str) -> Organization | None:
        return store.get_organization_by_slug(slug)

    def list_organizations(self, *, owner_id: str | None = None) -> list[Organization]:
        return store.list_organizations(owner_id=owner_id)

    def count_organizations_for_owner(self, owner_id: str) -> int:
        return store.count_organizations_for_owner(owner_id)

    # --- Workspaces ---

    def create_workspace(
        self,
        *,
        organization_id: str,
        name: str,
        slug: str,
        metadata: dict[str, Any] | None = None,
    ) -> Workspace:
        ws = Workspace(
            id=new_id("ws_"),
            organization_id=organization_id,
            name=name,
            slug=slug,
            metadata=dict(metadata or {}),
        )
        return store.save_workspace(ws)

    def get_workspace(self, workspace_id: str) -> Workspace | None:
        return store.get_workspace(workspace_id)

    def get_workspace_by_slug(self, org_id: str, slug: str) -> Workspace | None:
        return store.get_workspace_by_slug(org_id, slug)

    def list_workspaces(self, organization_id: str) -> list[Workspace]:
        return store.list_workspaces(organization_id)

    def count_workspaces(self, organization_id: str) -> int:
        return store.count_workspaces(organization_id)

    # --- Teams ---

    def create_team(
        self,
        *,
        organization_id: str,
        name: str,
        slug: str,
        workspace_id: str | None = None,
    ) -> Team:
        team = Team(
            id=new_id("team_"),
            organization_id=organization_id,
            workspace_id=workspace_id,
            name=name,
            slug=slug,
        )
        return store.save_team(team)

    def get_team(self, team_id: str) -> Team | None:
        return store.get_team(team_id)

    def get_team_by_slug(self, org_id: str, slug: str) -> Team | None:
        return store.get_team_by_slug(org_id, slug)

    def list_teams(
        self, organization_id: str, *, workspace_id: str | None = None
    ) -> list[Team]:
        return store.list_teams(organization_id, workspace_id=workspace_id)

    def count_teams(self, organization_id: str) -> int:
        return store.count_teams(organization_id)

    def add_team_member(self, *, team_id: str, user_id: str) -> TeamMember:
        existing = store.get_team_member(team_id, user_id)
        if existing:
            return existing
        tm = TeamMember(id=new_id("tm_"), team_id=team_id, user_id=user_id)
        return store.save_team_member(tm)

    def list_team_members(self, team_id: str) -> list[TeamMember]:
        return store.list_team_members(team_id)

    # --- Members ---

    def add_member(
        self,
        *,
        organization_id: str,
        user_id: str,
        role_key: str,
        workspace_id: str | None = None,
    ) -> Member:
        self.ensure_system_rbac()
        existing = store.get_member_by_org_user(organization_id, user_id)
        if existing:
            return existing
        role = store.get_role_by_key(role_key)
        if role is None:
            raise ValueError(f"unknown role: {role_key}")
        member = Member(
            id=new_id("mem_"),
            organization_id=organization_id,
            workspace_id=workspace_id,
            user_id=user_id,
            role_id=role.id,
            role_key=role.key,
        )
        return store.save_member(member)

    def get_member(self, member_id: str) -> Member | None:
        return store.get_member(member_id)

    def get_member_by_org_user(self, org_id: str, user_id: str) -> Member | None:
        return store.get_member_by_org_user(org_id, user_id)

    def list_members(
        self, organization_id: str, *, workspace_id: str | None = None
    ) -> list[Member]:
        return store.list_members(organization_id, workspace_id=workspace_id)

    def count_members(self, organization_id: str) -> int:
        return store.count_members(organization_id)

    def update_member_role(self, member_id: str, role_key: str) -> Member | None:
        member = store.get_member(member_id)
        if member is None:
            return None
        role = store.get_role_by_key(role_key)
        if role is None:
            raise ValueError(f"unknown role: {role_key}")
        member.role_id = role.id
        member.role_key = role.key
        member.updated_at = datetime.now(timezone.utc)
        return store.save_member(member)

    # --- Roles / Permissions ---

    def list_roles(self, *, organization_id: str | None = None) -> list[Role]:
        self.ensure_system_rbac()
        return store.list_roles(organization_id=organization_id)

    def get_role_by_key(self, key: str) -> Role | None:
        self.ensure_system_rbac()
        return store.get_role_by_key(key)

    def list_permissions(self) -> list[Permission]:
        self.ensure_system_rbac()
        return store.list_permissions()

    # --- Invites ---

    def create_invite(
        self,
        *,
        organization_id: str,
        email: str,
        role_key: str,
        invited_by_id: str,
        workspace_id: str | None = None,
        ttl_hours: int = DEFAULT_INVITE_TTL_HOURS,
    ) -> Invite:
        self.ensure_system_rbac()
        role = store.get_role_by_key(role_key)
        if role is None:
            raise ValueError(f"unknown role: {role_key}")
        now = datetime.now(timezone.utc)
        invite = Invite(
            id=new_id("inv_"),
            organization_id=organization_id,
            workspace_id=workspace_id,
            email=email,
            role_id=role.id,
            role_key=role.key,
            token=token_urlsafe(24),
            invited_by_id=invited_by_id,
            expires_at=now + timedelta(hours=ttl_hours),
        )
        return store.save_invite(invite)

    def get_invite(self, invite_id: str) -> Invite | None:
        return store.get_invite(invite_id)

    def get_invite_by_token(self, token: str) -> Invite | None:
        return store.get_invite_by_token(token)

    def list_invites(
        self, organization_id: str, *, status: str | None = None
    ) -> list[Invite]:
        return store.list_invites(organization_id, status=status)

    def count_invites(self, organization_id: str) -> int:
        return store.count_invites(organization_id)

    def accept_invite(self, token: str, user_id: str) -> dict[str, Any]:
        invite = store.get_invite_by_token(token)
        if invite is None:
            raise ValueError("invite not found")
        if invite.status != "pending":
            raise ValueError(f"invite is {invite.status}")
        now = datetime.now(timezone.utc)
        expires = invite.expires_at
        if expires.tzinfo is None:
            expires = expires.replace(tzinfo=timezone.utc)
        if expires < now:
            invite.status = "expired"
            invite.updated_at = now
            store.save_invite(invite)
            raise ValueError("invite expired")
        member = self.add_member(
            organization_id=invite.organization_id,
            user_id=user_id,
            role_key=invite.role_key,
            workspace_id=invite.workspace_id,
        )
        invite.status = "accepted"
        invite.accepted_at = now
        invite.updated_at = now
        store.save_invite(invite)
        return {"invite": invite, "member": member}

    def stats(self) -> dict[str, int]:
        self.ensure_system_rbac()
        return store.stats()


_repo: MultiTenantRepository | None = None


def get_repository() -> MultiTenantRepository:
    global _repo
    if _repo is None:
        _repo = MultiTenantRepository()
        _repo.ensure_system_rbac()
    return _repo


def reset_repository() -> None:
    global _repo
    store.reset_store()
    _repo = None
