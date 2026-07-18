"""Project Permissions Engine."""

from __future__ import annotations

from typing import Any

from app.services.enterprise_auth.errors import ForbiddenError, NotFoundError
from app.services.project_collaboration import store
from app.services.project_collaboration.roles import (
    PROJECT_PERMISSIONS,
    PROJECT_ROLE_KEYS,
    role_has_permission,
)


class ProjectPermissionsEngine:
    def permissions_for(self, role_key: str) -> list[str]:
        return sorted(PROJECT_PERMISSIONS.get(role_key.lower(), frozenset()))

    def has(self, role_key: str, permission: str) -> bool:
        return role_has_permission(role_key, permission)

    def catalog(self) -> dict[str, Any]:
        return {
            "ok": True,
            "roles": list(PROJECT_ROLE_KEYS),
            "permissions": {k: sorted(v) for k, v in PROJECT_PERMISSIONS.items()},
        }

    def require_project_access(
        self,
        *,
        project_id: str,
        user_id: str,
        permission: str,
    ) -> dict[str, Any]:
        project = store.get_project(project_id)
        if project is None or (
            project.status == "deleted" and permission != "project.restore"
        ):
            if project is None:
                raise NotFoundError("project not found")
            if project.status == "deleted" and permission not in {
                "project.restore",
                "project.read",
            }:
                raise NotFoundError("project not found")
        member = store.get_member(project_id, user_id)
        if member is None or member.status != "active":
            # Owner always has access even if membership row missing
            if project.owner_id != user_id:
                raise ForbiddenError("not a project member")
            role_key = "owner"
        else:
            role_key = member.role_key
        if project.owner_id == user_id:
            role_key = "owner"
        if not self.has(role_key, permission):
            raise ForbiddenError(f"missing project permission: {permission}")
        return {
            "project": project,
            "roleKey": role_key,
            "permissions": self.permissions_for(role_key),
            "isOwner": project.owner_id == user_id,
        }


_engine: ProjectPermissionsEngine | None = None


def get_project_permissions_engine() -> ProjectPermissionsEngine:
    global _engine
    if _engine is None:
        _engine = ProjectPermissionsEngine()
    return _engine
