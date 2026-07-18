"""Audit Engine — enterprise audit logging."""

from __future__ import annotations

from typing import Any

from app.services.enterprise_security import store
from app.services.enterprise_security.models import (
    AccessLogEntry,
    AuditAction,
    AuditLogEntry,
    Role,
    SecurityEvent,
    new_id,
)


def record(
    action: AuditAction,
    *,
    actor_id: str,
    role: Role | str = "user",
    resource: str,
    detail: str = "",
    ip: str | None = None,
    success: bool = True,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    entry = AuditLogEntry(
        audit_id=new_id("audit"),
        action=action,
        actor_id=actor_id or "anonymous",
        role=role,
        resource=resource,
        detail=detail,
        ip=ip,
        success=success,
        metadata=dict(metadata or {}),
    )
    store.add_audit(entry)
    if not success or action in ("security_violation", "unauthorized"):
        store.add_event(
            SecurityEvent(
                event_id=new_id("evt"),
                event_type=action,
                severity="high" if action == "security_violation" else "medium",
                actor_id=actor_id,
                message=detail or action,
                metadata={"resource": resource},
            )
        )
    return entry.to_dict()


def record_access(
    *,
    actor_id: str,
    method: str,
    path: str,
    status: int,
    authorized: bool,
) -> dict[str, Any]:
    entry = AccessLogEntry(
        access_id=new_id("access"),
        actor_id=actor_id,
        method=method,
        path=path,
        status=status,
        authorized=authorized,
    )
    store.add_access(entry)
    return entry.to_dict()


def list_audits(*, limit: int = 50, action: str | None = None) -> dict[str, Any]:
    items = store.audits(limit=limit, action=action)
    return {
        "ok": True,
        "count": len(items),
        "audits": [a.to_dict() for a in items],
    }


def list_events(*, limit: int = 50, severity: str | None = None) -> dict[str, Any]:
    items = store.events(limit=limit, severity=severity)
    return {
        "ok": True,
        "count": len(items),
        "events": [e.to_dict() for e in items],
    }


def audit_health() -> dict[str, Any]:
    items = store.audits(limit=500)
    events = store.events(limit=500)
    failures = sum(1 for a in items if not a.success)
    return {
        "audit_count": len(items),
        "event_count": len(events),
        "failure_count": failures,
        "healthy": True,
        "secure_logging": True,
    }
