"""Security helpers — isolation, role validation, permission enforcement, audit."""

from __future__ import annotations

from typing import Any

from app.services.enterprise_auth.audit import log_auth_event
from app.services.enterprise_auth.errors import AccessError, ForbiddenError, NotFoundError
from app.services.enterprise_auth.middleware import require_access
from app.services.enterprise_auth.permission_engine import get_permission_engine
from app.services.multi_tenant.repository import get_repository


def enforce(
    *,
    actor_id: str,
    organization_id: str,
    permission: str | None = None,
    workspace_id: str | None = None,
    require_owner: bool = False,
) -> dict[str, Any]:
    ctx = require_access(
        user_id=actor_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        permission=permission,
        require_owner=require_owner,
    )
    return ctx.to_dict()


def assert_org_isolation(entity_org_id: str, request_org_id: str) -> None:
    if entity_org_id != request_org_id:
        raise ForbiddenError("organization isolation violation")


def assert_workspace_isolation(workspace_id: str, organization_id: str) -> None:
    ws = get_repository().get_workspace(workspace_id)
    if ws is None:
        raise NotFoundError("workspace not found")
    if ws.organization_id != organization_id:
        raise ForbiddenError("workspace isolation violation")


def assert_team_in_org(team_id: str, organization_id: str) -> Any:
    team = get_repository().get_team(team_id)
    if team is None:
        raise NotFoundError("team not found")
    if team.organization_id != organization_id:
        raise ForbiddenError("team authorization failure")
    return team


def validate_role(role_key: str) -> str:
    engine = get_permission_engine()
    key = role_key.strip().lower()
    if key not in engine.catalog()["roles"]:
        raise ForbiddenError(f"invalid role: {role_key}")
    return key


def audit(
    action: str,
    *,
    actor_id: str,
    organization_id: str | None = None,
    workspace_id: str | None = None,
    success: bool = True,
    detail: str = "",
    metadata: dict[str, Any] | None = None,
) -> None:
    log_auth_event(
        action,
        actor_id=actor_id,
        organization_id=organization_id,
        workspace_id=workspace_id,
        success=success,
        detail=detail,
        metadata=metadata,
    )


__all__ = [
    "AccessError",
    "ForbiddenError",
    "NotFoundError",
    "enforce",
    "assert_org_isolation",
    "assert_workspace_isolation",
    "assert_team_in_org",
    "validate_role",
    "audit",
]
