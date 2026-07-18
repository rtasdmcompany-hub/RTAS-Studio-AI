"""Project roles and permission catalog."""

from __future__ import annotations

from typing import Final

PROJECT_STATUSES: Final[tuple[str, ...]] = (
    "draft",
    "active",
    "in_progress",
    "review",
    "completed",
    "archived",
    "deleted",
)

ROLE_OWNER = "owner"
ROLE_LEAD = "lead"
ROLE_EDITOR = "editor"
ROLE_CONTRIBUTOR = "contributor"
ROLE_VIEWER = "viewer"

PROJECT_ROLE_KEYS: Final[tuple[str, ...]] = (
    ROLE_OWNER,
    ROLE_LEAD,
    ROLE_EDITOR,
    ROLE_CONTRIBUTOR,
    ROLE_VIEWER,
)

PROJECT_ROLES: Final[list[dict]] = [
    {"key": ROLE_OWNER, "name": "Owner", "description": "Full project control"},
    {"key": ROLE_LEAD, "name": "Lead", "description": "Lead collaboration and assignments"},
    {"key": ROLE_EDITOR, "name": "Editor", "description": "Edit project content and notes"},
    {"key": ROLE_CONTRIBUTOR, "name": "Contributor", "description": "Contribute and comment"},
    {"key": ROLE_VIEWER, "name": "Viewer", "description": "Read-only access"},
]

PROJECT_PERMISSIONS: Final[dict[str, frozenset[str]]] = {
    ROLE_OWNER: frozenset(
        {
            "project.read",
            "project.update",
            "project.delete",
            "project.archive",
            "project.restore",
            "project.duplicate",
            "project.favorite",
            "member.assign",
            "member.remove",
            "member.role",
            "note.write",
            "note.read",
            "task.assign",
            "task.update",
            "activity.read",
        }
    ),
    ROLE_LEAD: frozenset(
        {
            "project.read",
            "project.update",
            "project.archive",
            "project.duplicate",
            "project.favorite",
            "member.assign",
            "member.remove",
            "note.write",
            "note.read",
            "task.assign",
            "task.update",
            "activity.read",
        }
    ),
    ROLE_EDITOR: frozenset(
        {
            "project.read",
            "project.update",
            "project.favorite",
            "note.write",
            "note.read",
            "task.update",
            "activity.read",
        }
    ),
    ROLE_CONTRIBUTOR: frozenset(
        {
            "project.read",
            "note.write",
            "note.read",
            "task.update",
            "activity.read",
        }
    ),
    ROLE_VIEWER: frozenset(
        {
            "project.read",
            "note.read",
            "activity.read",
        }
    ),
}

SYSTEM_TEMPLATES: Final[list[dict]] = [
    {
        "key": "blank",
        "name": "Blank Project",
        "description": "Empty collaborative project",
        "defaultStatus": "draft",
    },
    {
        "key": "ai_production",
        "name": "AI Production",
        "description": "Standard AI video production workflow",
        "defaultStatus": "active",
    },
    {
        "key": "review_pipeline",
        "name": "Review Pipeline",
        "description": "Draft → review → complete pipeline",
        "defaultStatus": "draft",
    },
]


def role_has_permission(role_key: str, permission: str) -> bool:
    return permission in PROJECT_PERMISSIONS.get(role_key.lower(), frozenset())
