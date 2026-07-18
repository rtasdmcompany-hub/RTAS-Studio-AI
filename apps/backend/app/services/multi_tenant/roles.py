"""System roles and permission catalog for multi-tenant RBAC."""

from __future__ import annotations

from typing import Final

# Canonical system role keys
ROLE_OWNER = "owner"
ROLE_ADMIN = "admin"
ROLE_MANAGER = "manager"
ROLE_EDITOR = "editor"
ROLE_VIEWER = "viewer"

SYSTEM_ROLE_KEYS: Final[tuple[str, ...]] = (
    ROLE_OWNER,
    ROLE_ADMIN,
    ROLE_MANAGER,
    ROLE_EDITOR,
    ROLE_VIEWER,
)

SYSTEM_ROLES: Final[list[dict]] = [
    {
        "key": ROLE_OWNER,
        "name": "Owner",
        "description": "Full control of the organization, billing, and membership",
        "rank": 100,
    },
    {
        "key": ROLE_ADMIN,
        "name": "Admin",
        "description": "Administer workspaces, teams, members, and invites",
        "rank": 80,
    },
    {
        "key": ROLE_MANAGER,
        "name": "Manager",
        "description": "Manage teams and day-to-day workspace operations",
        "rank": 60,
    },
    {
        "key": ROLE_EDITOR,
        "name": "Editor",
        "description": "Create and edit studio content within assigned workspaces",
        "rank": 40,
    },
    {
        "key": ROLE_VIEWER,
        "name": "Viewer",
        "description": "Read-only access to assigned workspaces",
        "rank": 20,
    },
]

# Permission catalog (key, name, category)
PERMISSION_CATALOG: Final[list[tuple[str, str, str]]] = [
    ("org.read", "Read organization", "organization"),
    ("org.update", "Update organization", "organization"),
    ("org.delete", "Delete organization", "organization"),
    ("org.billing", "Manage billing", "organization"),
    ("workspace.create", "Create workspace", "workspace"),
    ("workspace.read", "Read workspace", "workspace"),
    ("workspace.update", "Update workspace", "workspace"),
    ("workspace.delete", "Delete workspace", "workspace"),
    ("team.create", "Create team", "team"),
    ("team.read", "Read team", "team"),
    ("team.update", "Update team", "team"),
    ("team.delete", "Delete team", "team"),
    ("member.invite", "Invite members", "member"),
    ("member.read", "Read members", "member"),
    ("member.update", "Update members", "member"),
    ("member.remove", "Remove members", "member"),
    ("role.assign", "Assign roles", "role"),
    ("role.read", "Read roles", "role"),
    ("content.read", "Read content", "content"),
    ("content.write", "Write content", "content"),
    ("content.publish", "Publish content", "content"),
]

ROLE_PERMISSIONS: Final[dict[str, frozenset[str]]] = {
    ROLE_OWNER: frozenset(p[0] for p in PERMISSION_CATALOG),
    ROLE_ADMIN: frozenset(
        p[0]
        for p in PERMISSION_CATALOG
        if p[0] not in {"org.delete", "org.billing"}
    ),
    ROLE_MANAGER: frozenset(
        {
            "org.read",
            "workspace.read",
            "workspace.update",
            "team.create",
            "team.read",
            "team.update",
            "team.delete",
            "member.invite",
            "member.read",
            "member.update",
            "role.read",
            "content.read",
            "content.write",
            "content.publish",
        }
    ),
    ROLE_EDITOR: frozenset(
        {
            "org.read",
            "workspace.read",
            "team.read",
            "member.read",
            "role.read",
            "content.read",
            "content.write",
        }
    ),
    ROLE_VIEWER: frozenset(
        {
            "org.read",
            "workspace.read",
            "team.read",
            "member.read",
            "role.read",
            "content.read",
        }
    ),
}


def permissions_for_role(role_key: str) -> frozenset[str]:
    return ROLE_PERMISSIONS.get(role_key.lower(), frozenset())


def role_has_permission(role_key: str, permission_key: str) -> bool:
    return permission_key in permissions_for_role(role_key)
