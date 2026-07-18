"""Permission Engine — evaluates RBAC permissions for multi-tenant access."""

from __future__ import annotations

from typing import Any

from app.services.multi_tenant.roles import (
    ROLE_ADMIN,
    ROLE_EDITOR,
    ROLE_MANAGER,
    ROLE_OWNER,
    ROLE_VIEWER,
    ROLE_PERMISSIONS,
    permissions_for_role,
    role_has_permission,
)


# Action → required permission mapping for access checks
ACTION_PERMISSIONS: dict[str, str] = {
    "org.read": "org.read",
    "org.update": "org.update",
    "org.delete": "org.delete",
    "org.billing": "org.billing",
    "workspace.create": "workspace.create",
    "workspace.read": "workspace.read",
    "workspace.update": "workspace.update",
    "workspace.delete": "workspace.delete",
    "team.create": "team.create",
    "team.read": "team.read",
    "team.update": "team.update",
    "team.delete": "team.delete",
    "member.invite": "member.invite",
    "member.read": "member.read",
    "member.update": "member.update",
    "member.remove": "member.remove",
    "role.assign": "role.assign",
    "content.read": "content.read",
    "content.write": "content.write",
    "content.publish": "content.publish",
    "project.manage": "content.write",  # managers manage assigned projects
}


class PermissionEngine:
    """Evaluates whether a role may perform an action."""

    def permissions_for(self, role_key: str) -> list[str]:
        return sorted(permissions_for_role(role_key))

    def has_permission(self, role_key: str, permission: str) -> bool:
        return role_has_permission(role_key, permission)

    def can(self, role_key: str, action: str) -> bool:
        permission = ACTION_PERMISSIONS.get(action, action)
        return self.has_permission(role_key, permission)

    def require(self, role_key: str, action: str) -> bool:
        return self.can(role_key, action)

    def is_owner(self, role_key: str) -> bool:
        return role_key == ROLE_OWNER

    def is_admin_or_above(self, role_key: str) -> bool:
        return role_key in {ROLE_OWNER, ROLE_ADMIN}

    def can_manage_members(self, role_key: str) -> bool:
        return self.has_permission(role_key, "member.update") or self.has_permission(
            role_key, "member.invite"
        )

    def can_manage_workspaces(self, role_key: str) -> bool:
        return self.has_permission(role_key, "workspace.create") or self.has_permission(
            role_key, "workspace.update"
        )

    def can_manage_projects(self, role_key: str) -> bool:
        """Managers (and above) manage assigned projects."""
        return role_key in {ROLE_OWNER, ROLE_ADMIN, ROLE_MANAGER} or self.has_permission(
            role_key, "content.write"
        )

    def is_read_only(self, role_key: str) -> bool:
        return role_key == ROLE_VIEWER

    def can_write(self, role_key: str) -> bool:
        return self.has_permission(role_key, "content.write")

    def evaluate(
        self, *, role_key: str, action: str, permission: str | None = None
    ) -> dict[str, Any]:
        perm = permission or ACTION_PERMISSIONS.get(action, action)
        allowed = self.has_permission(role_key, perm)
        return {
            "ok": True,
            "allowed": allowed,
            "roleKey": role_key,
            "action": action,
            "permission": perm,
            "permissions": self.permissions_for(role_key),
            "capabilities": {
                "isOwner": self.is_owner(role_key),
                "isAdminOrAbove": self.is_admin_or_above(role_key),
                "canManageMembers": self.can_manage_members(role_key),
                "canManageWorkspaces": self.can_manage_workspaces(role_key),
                "canManageProjects": self.can_manage_projects(role_key),
                "canWrite": self.can_write(role_key),
                "isReadOnly": self.is_read_only(role_key),
                "isEditor": role_key == ROLE_EDITOR,
            },
        }

    def catalog(self) -> dict[str, Any]:
        return {
            "ok": True,
            "roles": {
                key: sorted(perms) for key, perms in ROLE_PERMISSIONS.items()
            },
            "actions": dict(ACTION_PERMISSIONS),
        }


_engine: PermissionEngine | None = None


def get_permission_engine() -> PermissionEngine:
    global _engine
    if _engine is None:
        _engine = PermissionEngine()
    return _engine
