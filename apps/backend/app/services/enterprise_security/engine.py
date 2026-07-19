"""Security Engine facade — status, audit, events, compliance, validate."""

from __future__ import annotations

import hashlib
import hmac
from typing import Any

from app.services.enterprise_security import (
    api_security,
    audit,
    auth,
    compliance,
    observability,
    policies,
    rbac,
    secrets,
    store,
)
from app.services.enterprise_security.models import AuthMethod, Role
from app.services.enterprise_security.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION


class SecurityEngine:
    def __init__(self) -> None:
        policies.ensure_default_policies()

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "policies": policies.list_policies(),
            "secrets": secrets.secret_validation_report(),
            "observability": observability.metrics(),
            "secure_headers": api_security.secure_headers(),
            "auth_methods": ["jwt", "session", "api_key", "service_account"],
            "roles": ["admin", "team", "user", "service"],
        }

    def audit_logs(self, *, limit: int = 50, action: str | None = None) -> dict[str, Any]:
        result = audit.list_audits(limit=limit, action=action)
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            **result,
            "access_logs": [a.to_dict() for a in store.access_logs(limit=min(20, limit))],
        }

    def events(self, *, limit: int = 50, severity: str | None = None) -> dict[str, Any]:
        result = audit.list_events(limit=limit, severity=severity)
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            **result,
            "observability": observability.metrics(),
        }

    def compliance(self) -> dict[str, Any]:
        result = compliance.compliance_status()
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            **result,
        }

    def validate(self, payload: dict[str, Any]) -> dict[str, Any]:
        """
        Validate authentication + API security + authorization for a request.
        Expected payload fields vary by checks requested.
        """
        checks: dict[str, Any] = {}
        errors: list[str] = []
        principal = None

        try:
            clean = api_security.validate_request_payload(payload or {})
        except api_security.ApiSecurityError as exc:
            errors.append(str(exc))
            clean = payload or {}

        actor = str(clean.get("actor_id") or clean.get("subject") or "anonymous")
        try:
            api_security.check_rate_limit(actor)
            checks["rate_limit"] = True
        except api_security.ApiSecurityError as exc:
            checks["rate_limit"] = False
            errors.append(str(exc))
            audit.record(
                "security_violation",
                actor_id=actor,
                resource="rate_limit",
                detail=str(exc),
                success=False,
            )

        # Auth
        method = clean.get("auth_method") or clean.get("method")
        credential = clean.get("credential") or clean.get("token") or ""
        if method:
            try:
                principal = auth.authenticate(
                    method=method,  # type: ignore[arg-type]
                    credential=str(credential),
                    subject=clean.get("subject") or clean.get("account_id"),
                )
                checks["authentication"] = True
                audit.record(
                    "login" if method in ("jwt", "session") else "api_call",
                    actor_id=principal.subject,
                    role=principal.role,
                    resource="auth",
                    detail=f"{method} ok",
                )
            except auth.AuthError as exc:
                checks["authentication"] = False
                errors.append(str(exc))
                audit.record(
                    "unauthorized",
                    actor_id=actor,
                    resource="auth",
                    detail=str(exc),
                    success=False,
                )

        # RBAC
        permission = clean.get("permission")
        if principal and permission:
            try:
                rbac.require_permission(principal, str(permission))
                checks["authorization"] = True
            except rbac.AccessDenied as exc:
                checks["authorization"] = False
                errors.append(str(exc))
                audit.record(
                    "unauthorized",
                    actor_id=principal.subject,
                    role=principal.role,
                    resource=str(permission),
                    detail=str(exc),
                    success=False,
                )

        # Signature / CSRF / CORS / Replay / sanitize prompt
        if clean.get("signature") is not None:
            try:
                api_security.validate_api_signature(
                    body=str(clean.get("body") or ""),
                    signature=str(clean.get("signature")),
                    timestamp=str(clean.get("timestamp") or ""),
                )
                checks["signature"] = True
            except api_security.ApiSecurityError as exc:
                checks["signature"] = False
                errors.append(str(exc))

        if clean.get("csrf_token") is not None or clean.get("session_token"):
            try:
                api_security.validate_csrf(
                    clean.get("csrf_token"),
                    clean.get("session_token"),
                )
                checks["csrf"] = True
            except api_security.ApiSecurityError as exc:
                checks["csrf"] = False
                errors.append(str(exc))

        if clean.get("origin") is not None:
            try:
                api_security.validate_cors_origin(clean.get("origin"))
                checks["cors"] = True
            except api_security.ApiSecurityError as exc:
                checks["cors"] = False
                errors.append(str(exc))

        if clean.get("nonce"):
            try:
                api_security.check_replay_protection(
                    str(clean.get("nonce")),
                    timestamp=str(clean.get("timestamp")) if clean.get("timestamp") else None,
                )
                checks["replay"] = True
            except api_security.ApiSecurityError as exc:
                checks["replay"] = False
                errors.append(str(exc))

        if clean.get("prompt") is not None:
            try:
                api_security.sanitize_input(str(clean.get("prompt")))
                checks["input_sanitization"] = True
                audit.record(
                    "prompt_submission",
                    actor_id=actor,
                    role=principal.role if principal else "user",
                    resource="prompt",
                    detail="prompt sanitized",
                )
            except api_security.ApiSecurityError as exc:
                checks["input_sanitization"] = False
                errors.append(str(exc))

        # Track common enterprise actions if requested
        action = clean.get("track_action")
        if action and principal:
            audit.record(
                action,  # type: ignore[arg-type]
                actor_id=principal.subject,
                role=principal.role,
                resource=str(clean.get("resource") or action),
                detail=str(clean.get("detail") or ""),
            )
            checks["audit_tracked"] = True

        audit.record_access(
            actor_id=principal.subject if principal else actor,
            method="VALIDATE",
            path="/api/security/validate",
            status=200 if not errors else 403,
            authorized=not errors,
        )

        return {
            "ok": len(errors) == 0,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "valid": len(errors) == 0,
            "checks": checks,
            "errors": errors,
            "principal": principal.to_dict() if principal else None,
            "secure_headers": api_security.secure_headers(),
            "secrets_ok": secrets.secret_validation_report()["healthy"],
        }

    # Helpers used by tests / internal integrations
    def issue_token(self, *, subject: str, role: Role = "user", **kwargs: Any) -> dict[str, Any]:
        return auth.issue_jwt(subject=subject, role=role, **kwargs)

    def login(self, *, subject: str, role: Role = "user") -> dict[str, Any]:
        sess = auth.create_session(subject=subject, role=role)
        audit.record("login", actor_id=subject, role=role, resource="session", detail="login")
        return sess

    def logout(self, session_token: str) -> dict[str, Any]:
        auth.logout_session(session_token)
        audit.record("logout", actor_id="session", resource="session", detail="logout")
        return {"ok": True}


_engine: SecurityEngine | None = None


def get_security_engine() -> SecurityEngine:
    global _engine
    if _engine is None:
        _engine = SecurityEngine()
    return _engine


def reset_engine() -> None:
    global _engine
    store.clear()
    _engine = None


def sign_body(body: str, timestamp: str = "") -> str:
    try:
        secret = secrets.jwt_signing_secret()
    except ValueError:
        secret = "rtas-dev-only-jwt"
    msg = f"{timestamp}.{body}".encode("utf-8")
    return hmac.new(secret.encode("utf-8"), msg, hashlib.sha256).hexdigest()
