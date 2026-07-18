"""Memory isolation, access control, and audit logging."""

from __future__ import annotations

from typing import Any

from app.services.memory_knowledge import store
from app.services.memory_knowledge.models import AuditLogEntry, new_id


class AccessDenied(PermissionError):
    pass


def assert_user(user_id: str | None) -> str:
    uid = (user_id or "").strip()
    if not uid:
        raise AccessDenied("user_id required for memory isolation")
    return uid


def can_access_project(user_id: str, project_id: str | None, owner_id: str) -> bool:
    if owner_id != user_id:
        return False
    # Project scoping: user owns records; optional project membership map
    if project_id:
        members = store.project_members(project_id)
        if members and user_id not in members:
            return False
    return True


def require_access(
    user_id: str,
    *,
    owner_id: str,
    project_id: str | None = None,
) -> None:
    if not can_access_project(user_id, project_id, owner_id):
        raise AccessDenied("project access denied")


def audit(
    user_id: str,
    action: str,
    resource_type: str,
    resource_id: str,
    *,
    project_id: str | None = None,
    detail: str = "",
) -> dict[str, Any]:
    entry = AuditLogEntry(
        audit_id=new_id("audit"),
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        project_id=project_id,
        detail=detail,
    )
    store.save_audit(entry)
    return entry.to_dict()
