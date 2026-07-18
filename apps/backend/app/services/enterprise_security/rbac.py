"""Access Control Manager — Role-Based Access Control."""

from __future__ import annotations

from typing import Iterable

from app.services.enterprise_security.models import Principal, Role

ROLE_RANK: dict[Role, int] = {
    "user": 1,
    "team": 2,
    "service": 3,
    "admin": 4,
}

ROLE_PERMISSIONS: dict[Role, frozenset[str]] = {
    "user": frozenset(
        {
            "read:own",
            "write:own",
            "job:create",
            "prompt:submit",
            "export:request",
            "download:own",
        }
    ),
    "team": frozenset(
        {
            "read:own",
            "write:own",
            "read:team",
            "write:team",
            "job:create",
            "job:cancel",
            "prompt:submit",
            "export:request",
            "download:own",
            "provider:use",
        }
    ),
    "service": frozenset(
        {
            "read:own",
            "write:own",
            "job:create",
            "job:cancel",
            "provider:use",
            "api:call",
            "service:execute",
        }
    ),
    "admin": frozenset(
        {
            "read:own",
            "write:own",
            "read:team",
            "write:team",
            "read:all",
            "write:all",
            "job:create",
            "job:cancel",
            "prompt:submit",
            "export:request",
            "download:own",
            "provider:use",
            "api:call",
            "admin:action",
            "security:manage",
            "audit:read",
            "compliance:read",
        }
    ),
}


class AccessDenied(PermissionError):
    pass


def permissions_for(role: Role | str) -> frozenset[str]:
    return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["user"])  # type: ignore[arg-type]


def has_permission(principal: Principal, permission: str) -> bool:
    return permission in permissions_for(principal.role)


def require_permission(principal: Principal, permission: str) -> None:
    if not has_permission(principal, permission):
        raise AccessDenied(f"role {principal.role} missing permission {permission}")


def require_role(principal: Principal, minimum: Role) -> None:
    if ROLE_RANK.get(principal.role, 0) < ROLE_RANK.get(minimum, 99):
        raise AccessDenied(f"requires role {minimum} or higher")


def authorize(
    principal: Principal,
    *,
    permission: str | None = None,
    roles: Iterable[Role] | None = None,
) -> bool:
    if roles is not None and principal.role not in set(roles):
        raise AccessDenied(f"role {principal.role} not in allowed roles")
    if permission:
        require_permission(principal, permission)
    return True
