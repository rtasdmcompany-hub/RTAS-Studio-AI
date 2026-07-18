"""Thread-safe in-memory store for multi-tenant entities."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.multi_tenant.models import (
        Invite,
        Member,
        Organization,
        Permission,
        Role,
        Team,
        TeamMember,
        Workspace,
    )

_lock = threading.RLock()

_organizations: OrderedDict[str, "Organization"] = OrderedDict()
_workspaces: OrderedDict[str, "Workspace"] = OrderedDict()
_teams: OrderedDict[str, "Team"] = OrderedDict()
_members: OrderedDict[str, "Member"] = OrderedDict()
_team_members: OrderedDict[str, "TeamMember"] = OrderedDict()
_roles: OrderedDict[str, "Role"] = OrderedDict()
_permissions: OrderedDict[str, "Permission"] = OrderedDict()
_invites: OrderedDict[str, "Invite"] = OrderedDict()

_slug_org: dict[str, str] = {}
_slug_workspace: dict[tuple[str, str], str] = {}
_slug_team: dict[tuple[str, str], str] = {}
_member_org_user: dict[tuple[str, str], str] = {}
_team_member_key: dict[tuple[str, str], str] = {}
_invite_token: dict[str, str] = {}
_role_key_index: dict[tuple[str | None, str], str] = {}
_permission_key_index: dict[str, str] = {}

_seeded = False


def reset_store() -> None:
    global _seeded
    with _lock:
        _organizations.clear()
        _workspaces.clear()
        _teams.clear()
        _members.clear()
        _team_members.clear()
        _roles.clear()
        _permissions.clear()
        _invites.clear()
        _slug_org.clear()
        _slug_workspace.clear()
        _slug_team.clear()
        _member_org_user.clear()
        _team_member_key.clear()
        _invite_token.clear()
        _role_key_index.clear()
        _permission_key_index.clear()
        _seeded = False


def is_seeded() -> bool:
    with _lock:
        return _seeded


def mark_seeded() -> None:
    global _seeded
    with _lock:
        _seeded = True


# --- Organizations ---

def save_organization(org: "Organization") -> "Organization":
    with _lock:
        _organizations[org.id] = org
        _slug_org[org.slug] = org.id
        return org


def get_organization(org_id: str) -> "Organization | None":
    with _lock:
        return _organizations.get(org_id)


def get_organization_by_slug(slug: str) -> "Organization | None":
    with _lock:
        oid = _slug_org.get(slug)
        return _organizations.get(oid) if oid else None


def list_organizations(*, owner_id: str | None = None) -> list["Organization"]:
    with _lock:
        items = list(_organizations.values())
    if owner_id:
        items = [o for o in items if o.owner_id == owner_id]
    return items


def count_organizations_for_owner(owner_id: str) -> int:
    with _lock:
        return sum(1 for o in _organizations.values() if o.owner_id == owner_id)


def delete_organization(org_id: str) -> bool:
    with _lock:
        org = _organizations.pop(org_id, None)
        if org is None:
            return False
        _slug_org.pop(org.slug, None)
        # cascade workspaces
        for wid, ws in list(_workspaces.items()):
            if ws.organization_id == org_id:
                _slug_workspace.pop((org_id, ws.slug), None)
                _workspaces.pop(wid, None)
        for tid, team in list(_teams.items()):
            if team.organization_id == org_id:
                _slug_team.pop((org_id, team.slug), None)
                for tmid, tm in list(_team_members.items()):
                    if tm.team_id == tid:
                        _team_member_key.pop((tm.team_id, tm.user_id), None)
                        _team_members.pop(tmid, None)
                _teams.pop(tid, None)
        for mid, m in list(_members.items()):
            if m.organization_id == org_id:
                _member_org_user.pop((org_id, m.user_id), None)
                _members.pop(mid, None)
        for iid, inv in list(_invites.items()):
            if inv.organization_id == org_id:
                _invite_token.pop(inv.token, None)
                _invites.pop(iid, None)
        return True


# --- Workspaces ---

def save_workspace(ws: "Workspace") -> "Workspace":
    with _lock:
        _workspaces[ws.id] = ws
        _slug_workspace[(ws.organization_id, ws.slug)] = ws.id
        return ws


def get_workspace(workspace_id: str) -> "Workspace | None":
    with _lock:
        return _workspaces.get(workspace_id)


def get_workspace_by_slug(org_id: str, slug: str) -> "Workspace | None":
    with _lock:
        wid = _slug_workspace.get((org_id, slug))
        return _workspaces.get(wid) if wid else None


def list_workspaces(organization_id: str) -> list["Workspace"]:
    with _lock:
        return [w for w in _workspaces.values() if w.organization_id == organization_id]


def count_workspaces(organization_id: str) -> int:
    with _lock:
        return sum(1 for w in _workspaces.values() if w.organization_id == organization_id)


def delete_workspace(workspace_id: str) -> bool:
    with _lock:
        ws = _workspaces.pop(workspace_id, None)
        if ws is None:
            return False
        _slug_workspace.pop((ws.organization_id, ws.slug), None)
        return True


# --- Teams ---

def save_team(team: "Team") -> "Team":
    with _lock:
        _teams[team.id] = team
        _slug_team[(team.organization_id, team.slug)] = team.id
        return team


def get_team(team_id: str) -> "Team | None":
    with _lock:
        return _teams.get(team_id)


def get_team_by_slug(org_id: str, slug: str) -> "Team | None":
    with _lock:
        tid = _slug_team.get((org_id, slug))
        return _teams.get(tid) if tid else None


def list_teams(
    organization_id: str, *, workspace_id: str | None = None
) -> list["Team"]:
    with _lock:
        items = [t for t in _teams.values() if t.organization_id == organization_id]
    if workspace_id is not None:
        items = [t for t in items if t.workspace_id == workspace_id]
    return items


def count_teams(organization_id: str) -> int:
    with _lock:
        return sum(1 for t in _teams.values() if t.organization_id == organization_id)


def delete_team(team_id: str) -> bool:
    with _lock:
        team = _teams.pop(team_id, None)
        if team is None:
            return False
        _slug_team.pop((team.organization_id, team.slug), None)
        for tmid, tm in list(_team_members.items()):
            if tm.team_id == team_id:
                _team_member_key.pop((tm.team_id, tm.user_id), None)
                _team_members.pop(tmid, None)
        return True


# --- Members ---

def save_member(member: "Member") -> "Member":
    with _lock:
        _members[member.id] = member
        _member_org_user[(member.organization_id, member.user_id)] = member.id
        return member


def get_member(member_id: str) -> "Member | None":
    with _lock:
        return _members.get(member_id)


def get_member_by_org_user(org_id: str, user_id: str) -> "Member | None":
    with _lock:
        mid = _member_org_user.get((org_id, user_id))
        return _members.get(mid) if mid else None


def list_members(
    organization_id: str, *, workspace_id: str | None = None
) -> list["Member"]:
    with _lock:
        items = [m for m in _members.values() if m.organization_id == organization_id]
    if workspace_id is not None:
        items = [
            m
            for m in items
            if m.workspace_id == workspace_id or m.workspace_id is None
        ]
    return items


def count_members(organization_id: str) -> int:
    with _lock:
        return sum(1 for m in _members.values() if m.organization_id == organization_id)


def delete_member(member_id: str) -> bool:
    with _lock:
        member = _members.pop(member_id, None)
        if member is None:
            return False
        _member_org_user.pop((member.organization_id, member.user_id), None)
        return True


# --- Team members ---

def save_team_member(tm: "TeamMember") -> "TeamMember":
    with _lock:
        _team_members[tm.id] = tm
        _team_member_key[(tm.team_id, tm.user_id)] = tm.id
        return tm


def get_team_member(team_id: str, user_id: str) -> "TeamMember | None":
    with _lock:
        tid = _team_member_key.get((team_id, user_id))
        return _team_members.get(tid) if tid else None


def list_team_members(team_id: str) -> list["TeamMember"]:
    with _lock:
        return [t for t in _team_members.values() if t.team_id == team_id]


def delete_team_member(team_id: str, user_id: str) -> bool:
    with _lock:
        tid = _team_member_key.pop((team_id, user_id), None)
        if tid is None:
            return False
        _team_members.pop(tid, None)
        return True


# --- Roles / Permissions ---

def save_role(role: "Role") -> "Role":
    with _lock:
        _roles[role.id] = role
        _role_key_index[(role.organization_id, role.key)] = role.id
        return role


def get_role(role_id: str) -> "Role | None":
    with _lock:
        return _roles.get(role_id)


def get_role_by_key(key: str, organization_id: str | None = None) -> "Role | None":
    with _lock:
        rid = _role_key_index.get((organization_id, key))
        if rid:
            return _roles.get(rid)
        # fall back to system roles (org_id None)
        rid = _role_key_index.get((None, key))
        return _roles.get(rid) if rid else None


def list_roles(*, organization_id: str | None = None) -> list["Role"]:
    with _lock:
        items = list(_roles.values())
    if organization_id is None:
        return [r for r in items if r.organization_id is None]
    return [r for r in items if r.organization_id is None or r.organization_id == organization_id]


def save_permission(perm: "Permission") -> "Permission":
    with _lock:
        _permissions[perm.id] = perm
        _permission_key_index[perm.key] = perm.id
        return perm


def get_permission_by_key(key: str) -> "Permission | None":
    with _lock:
        pid = _permission_key_index.get(key)
        return _permissions.get(pid) if pid else None


def list_permissions() -> list["Permission"]:
    with _lock:
        return list(_permissions.values())


# --- Invites ---

def save_invite(invite: "Invite") -> "Invite":
    with _lock:
        _invites[invite.id] = invite
        _invite_token[invite.token] = invite.id
        return invite


def get_invite(invite_id: str) -> "Invite | None":
    with _lock:
        return _invites.get(invite_id)


def get_invite_by_token(token: str) -> "Invite | None":
    with _lock:
        iid = _invite_token.get(token)
        return _invites.get(iid) if iid else None


def list_invites(organization_id: str, *, status: str | None = None) -> list["Invite"]:
    with _lock:
        items = [i for i in _invites.values() if i.organization_id == organization_id]
    if status:
        items = [i for i in items if i.status == status]
    return items


def count_invites(organization_id: str) -> int:
    with _lock:
        return sum(1 for i in _invites.values() if i.organization_id == organization_id)


def stats() -> dict[str, int]:
    with _lock:
        return {
            "organizations": len(_organizations),
            "workspaces": len(_workspaces),
            "teams": len(_teams),
            "members": len(_members),
            "teamMembers": len(_team_members),
            "roles": len(_roles),
            "permissions": len(_permissions),
            "invites": len(_invites),
        }
