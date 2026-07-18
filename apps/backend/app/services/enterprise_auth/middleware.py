"""Access middleware — validates session + org/workspace context + permissions."""

from __future__ import annotations

from typing import Any

from app.services.enterprise_auth.audit import log_auth_event
from app.services.enterprise_auth.errors import AccessError, ForbiddenError, UnauthorizedError
from app.services.enterprise_auth.models import AccessContext
from app.services.enterprise_auth.permission_engine import get_permission_engine
from app.services.enterprise_auth.sessions import validate_session
from app.services.enterprise_auth.validators import (
    validate_organization_access,
    validate_organization_ownership,
    validate_team_access,
    validate_workspace_membership,
)


class AccessMiddleware:
    """
    Modular access guard for multi-tenant API requests.

    Every protected request should call authorize() with organization context.
    Workspace-scoped requests should also pass workspace_id.
    """

    def authorize(
        self,
        *,
        user_id: str | None = None,
        organization_id: str | None = None,
        workspace_id: str | None = None,
        team_id: str | None = None,
        session_token: str | None = None,
        permission: str | None = None,
        action: str | None = None,
        require_owner: bool = False,
        ip: str | None = None,
    ) -> AccessContext:
        # Session validation (optional but preferred)
        session = None
        if session_token:
            session = validate_session(session_token)
            user_id = user_id or session.user_id
            organization_id = organization_id or session.organization_id
            workspace_id = workspace_id or session.workspace_id
            team_id = team_id or session.team_id

        if not user_id:
            log_auth_event(
                "unauthorized",
                actor_id="anonymous",
                organization_id=organization_id,
                success=False,
                detail="missing userId",
                ip=ip,
            )
            raise UnauthorizedError("userId or valid session required")

        if not organization_id:
            log_auth_event(
                "org_context_missing",
                actor_id=user_id,
                success=False,
                detail="organizationId required",
                ip=ip,
            )
            raise ForbiddenError("organization context is required")

        required = permission
        if action and not required:
            engine = get_permission_engine()
            from app.services.enterprise_auth.permission_engine import ACTION_PERMISSIONS

            required = ACTION_PERMISSIONS.get(action, action)

        try:
            if require_owner:
                validate_organization_ownership(
                    organization_id=organization_id, user_id=user_id
                )

            if workspace_id:
                access = validate_workspace_membership(
                    organization_id=organization_id,
                    workspace_id=workspace_id,
                    user_id=user_id,
                    require_permission=required or "workspace.read",
                )
            else:
                access = validate_organization_access(
                    organization_id=organization_id,
                    user_id=user_id,
                    require_permission=required,
                )

            if team_id:
                validate_team_access(team_id=team_id, user_id=user_id)

            role_key = access["roleKey"]
            engine = get_permission_engine()
            if required and not engine.has_permission(role_key, required):
                raise ForbiddenError(f"missing permission: {required}")

            ctx = AccessContext(
                user_id=user_id,
                organization_id=organization_id,
                workspace_id=workspace_id,
                team_id=team_id,
                role_key=role_key,
                session_id=session.id if session else None,
                permissions=list(access.get("permissions") or engine.permissions_for(role_key)),
                is_owner=bool(access.get("isOwner") or engine.is_owner(role_key)),
                auth_provider=session.auth_provider if session else "credentials",
            )
            log_auth_event(
                "authorize_success",
                actor_id=user_id,
                organization_id=organization_id,
                workspace_id=workspace_id,
                success=True,
                detail=required or action or "access",
                ip=ip,
                metadata={"roleKey": role_key, "permission": required},
            )
            return ctx
        except AccessError as exc:
            log_auth_event(
                "authorize_denied",
                actor_id=user_id,
                organization_id=organization_id,
                workspace_id=workspace_id,
                success=False,
                detail=str(exc),
                ip=ip,
                metadata={"code": exc.code, "permission": required},
            )
            raise


_middleware: AccessMiddleware | None = None


def get_access_middleware() -> AccessMiddleware:
    global _middleware
    if _middleware is None:
        _middleware = AccessMiddleware()
    return _middleware


def require_access(**kwargs: Any) -> AccessContext:
    return get_access_middleware().authorize(**kwargs)
