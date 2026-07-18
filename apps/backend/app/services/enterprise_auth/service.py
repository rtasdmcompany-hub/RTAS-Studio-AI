"""Enterprise Authentication & Access Control service."""

from __future__ import annotations

from typing import Any

from app.services.enterprise_auth import sessions as session_svc
from app.services.enterprise_auth.audit import list_auth_audits, log_auth_event
from app.services.enterprise_auth.errors import AccessError, ForbiddenError, UnauthorizedError
from app.services.enterprise_auth.middleware import get_access_middleware
from app.services.enterprise_auth.permission_engine import get_permission_engine
from app.services.enterprise_auth import store
from app.services.enterprise_auth.sso import begin_sso_login, list_sso_providers
from app.services.enterprise_auth.validators import (
    validate_organization_access,
    validate_organization_ownership,
    validate_team_access,
    validate_workspace_membership,
)
from app.services.enterprise_auth.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PHASE,
    SPRINT,
    SSO_READY,
)
from app.services.multi_tenant.repository import get_repository
from app.services.multi_tenant.service import get_multi_tenant_service
from app.services.multi_tenant.validation import ValidationError


class EnterpriseAuthService:
    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "ssoReady": SSO_READY,
            "stats": store.stats(),
            "components": [
                "organization_auth",
                "workspace_auth",
                "team_auth",
                "rbac",
                "permission_engine",
                "invite_acceptance",
                "workspace_membership",
                "organization_ownership",
                "session_validation",
                "access_middleware",
                "audit_logging",
                "sso_ready",
            ],
        }

    def create_session(self, payload: dict[str, Any]) -> dict[str, Any]:
        user_id = (payload.get("userId") or payload.get("user_id") or "").strip()
        organization_id = payload.get("organizationId") or payload.get("organization_id")
        workspace_id = payload.get("workspaceId") or payload.get("workspace_id")
        team_id = payload.get("teamId") or payload.get("team_id")
        auth_provider = payload.get("authProvider") or payload.get("auth_provider") or "credentials"
        sso_provider = payload.get("ssoProvider") or payload.get("sso_provider")
        if not user_id:
            raise UnauthorizedError("userId is required")

        role_key = None
        if organization_id:
            access = validate_organization_access(
                organization_id=str(organization_id), user_id=user_id
            )
            role_key = access["roleKey"]
            if workspace_id:
                validate_workspace_membership(
                    organization_id=str(organization_id),
                    workspace_id=str(workspace_id),
                    user_id=user_id,
                )

        session = session_svc.create_session(
            user_id=user_id,
            organization_id=str(organization_id) if organization_id else None,
            workspace_id=str(workspace_id) if workspace_id else None,
            team_id=str(team_id) if team_id else None,
            role_key=role_key,
            auth_provider=str(auth_provider),
            sso_provider=str(sso_provider) if sso_provider else None,
            metadata=payload.get("metadata") or {},
        )
        log_auth_event(
            "session_created",
            actor_id=user_id,
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
            success=True,
            detail="session created",
            metadata={"authProvider": session.auth_provider},
        )
        return {"ok": True, "session": session.to_dict()}

    def validate_session(self, token: str) -> dict[str, Any]:
        session = session_svc.validate_session(token)
        log_auth_event(
            "session_validated",
            actor_id=session.user_id,
            organization_id=session.organization_id,
            workspace_id=session.workspace_id,
            success=True,
            detail="session valid",
        )
        return {"ok": True, "valid": True, "session": session.to_dict()}

    def revoke_session(
        self, *, token: str | None = None, session_id: str | None = None
    ) -> dict[str, Any]:
        session = session_svc.revoke_session(token, session_id=session_id)
        log_auth_event(
            "session_revoked",
            actor_id=session.user_id,
            organization_id=session.organization_id,
            success=True,
            detail="session revoked",
        )
        return {"ok": True, "session": session.to_dict()}

    def authorize(self, payload: dict[str, Any]) -> dict[str, Any]:
        ctx = get_access_middleware().authorize(
            user_id=payload.get("userId") or payload.get("user_id"),
            organization_id=payload.get("organizationId") or payload.get("organization_id"),
            workspace_id=payload.get("workspaceId") or payload.get("workspace_id"),
            team_id=payload.get("teamId") or payload.get("team_id"),
            session_token=payload.get("sessionToken") or payload.get("session_token"),
            permission=payload.get("permission"),
            action=payload.get("action"),
            require_owner=bool(payload.get("requireOwner") or payload.get("require_owner")),
            ip=payload.get("ip"),
        )
        return {"ok": True, "allowed": True, "context": ctx.to_dict()}

    def validate_organization(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = validate_organization_access(
            organization_id=str(payload.get("organizationId") or payload.get("organization_id")),
            user_id=str(payload.get("userId") or payload.get("user_id")),
            require_permission=payload.get("permission"),
        )
        log_auth_event(
            "org_access_validated",
            actor_id=str(payload.get("userId") or payload.get("user_id")),
            organization_id=result["organization"]["id"],
            success=True,
        )
        return result

    def validate_workspace(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = validate_workspace_membership(
            organization_id=str(payload.get("organizationId") or payload.get("organization_id")),
            workspace_id=str(payload.get("workspaceId") or payload.get("workspace_id")),
            user_id=str(payload.get("userId") or payload.get("user_id")),
            require_permission=payload.get("permission") or "workspace.read",
        )
        log_auth_event(
            "workspace_access_validated",
            actor_id=str(payload.get("userId") or payload.get("user_id")),
            organization_id=result["organization"]["id"],
            workspace_id=result["workspace"]["id"],
            success=True,
        )
        return result

    def validate_team(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = validate_team_access(
            team_id=str(payload.get("teamId") or payload.get("team_id")),
            user_id=str(payload.get("userId") or payload.get("user_id")),
        )
        log_auth_event(
            "team_access_validated",
            actor_id=str(payload.get("userId") or payload.get("user_id")),
            organization_id=result.get("organizationId"),
            success=True,
        )
        return result

    def validate_ownership(self, payload: dict[str, Any]) -> dict[str, Any]:
        result = validate_organization_ownership(
            organization_id=str(payload.get("organizationId") or payload.get("organization_id")),
            user_id=str(payload.get("userId") or payload.get("user_id")),
        )
        log_auth_event(
            "ownership_validated",
            actor_id=str(payload.get("userId") or payload.get("user_id")),
            organization_id=result["organizationId"],
            success=True,
        )
        return result

    def check_permission(self, payload: dict[str, Any]) -> dict[str, Any]:
        role_key = payload.get("role") or payload.get("roleKey") or payload.get("role_key")
        user_id = payload.get("userId") or payload.get("user_id")
        organization_id = payload.get("organizationId") or payload.get("organization_id")
        action = payload.get("action") or "content.read"
        permission = payload.get("permission")

        if user_id and organization_id:
            access = validate_organization_access(
                organization_id=str(organization_id), user_id=str(user_id)
            )
            role_key = access["roleKey"]

        if not role_key:
            raise UnauthorizedError("role or userId+organizationId required")

        result = get_permission_engine().evaluate(
            role_key=str(role_key),
            action=str(action),
            permission=str(permission) if permission else None,
        )
        log_auth_event(
            "permission_checked",
            actor_id=str(user_id or "role"),
            organization_id=str(organization_id) if organization_id else None,
            success=bool(result["allowed"]),
            detail=result["permission"],
            metadata={"roleKey": role_key, "allowed": result["allowed"]},
        )
        return result

    def accept_invite(self, payload: dict[str, Any]) -> dict[str, Any]:
        """Authenticated invitation acceptance with audit logging."""
        token = (payload.get("token") or "").strip()
        user_id = (payload.get("userId") or payload.get("user_id") or "").strip()
        session_token = payload.get("sessionToken") or payload.get("session_token")

        if not token:
            raise UnauthorizedError("invite token is required")
        if not user_id:
            raise UnauthorizedError("userId is required")

        # Optional session binding — if provided, must match user
        if session_token:
            session = session_svc.validate_session(session_token)
            if session.user_id != user_id:
                raise ForbiddenError("session user does not match invite acceptor")

        mt = get_multi_tenant_service()
        try:
            result = mt.accept_invite(token, user_id)
        except ValidationError as exc:
            log_auth_event(
                "invite_accept_failed",
                actor_id=user_id,
                success=False,
                detail=str(exc),
            )
            raise ForbiddenError(str(exc)) from exc

        org_id = result["invite"]["organizationId"]
        log_auth_event(
            "invite_accepted",
            actor_id=user_id,
            organization_id=org_id,
            workspace_id=result["invite"].get("workspaceId"),
            success=True,
            detail=f"role={result['member']['roleKey']}",
        )
        # Issue a session in the new org context
        session = session_svc.create_session(
            user_id=user_id,
            organization_id=org_id,
            workspace_id=result["invite"].get("workspaceId"),
            role_key=result["member"]["roleKey"],
            auth_provider="invite",
        )
        return {
            "ok": True,
            "invite": result["invite"],
            "member": result["member"],
            "session": session.to_dict(),
        }

    def list_audits(
        self,
        *,
        limit: int = 50,
        organization_id: str | None = None,
        event_type: str | None = None,
    ) -> dict[str, Any]:
        return list_auth_audits(
            limit=limit, organization_id=organization_id, event_type=event_type
        )

    def sso_providers(self) -> dict[str, Any]:
        return list_sso_providers()

    def sso_begin(self, payload: dict[str, Any]) -> dict[str, Any]:
        provider = payload.get("provider") or payload.get("providerKey") or "oidc_generic"
        org_id = payload.get("organizationId") or payload.get("organization_id") or ""
        result = begin_sso_login(provider_key=str(provider), organization_id=str(org_id))
        log_auth_event(
            "sso_begin",
            actor_id=str(payload.get("userId") or "anonymous"),
            organization_id=str(org_id) if org_id else None,
            success=bool(result.get("ok")),
            detail=str(provider),
        )
        return result

    def permission_catalog(self) -> dict[str, Any]:
        return get_permission_engine().catalog()


_service: EnterpriseAuthService | None = None


def get_enterprise_auth_service() -> EnterpriseAuthService:
    global _service
    # Ensure multi-tenant RBAC is seeded
    get_repository().ensure_system_rbac()
    if _service is None:
        _service = EnterpriseAuthService()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    from app.services.multi_tenant.engine import reset_engine as reset_mt

    reset_mt()
    _service = None


get_engine = get_enterprise_auth_service
