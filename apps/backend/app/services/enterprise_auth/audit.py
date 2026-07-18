"""Authentication audit logging."""

from __future__ import annotations

from typing import Any

from app.services.enterprise_auth import store
from app.services.enterprise_auth.models import AuthAuditEvent, new_id


def log_auth_event(
    event_type: str,
    *,
    actor_id: str,
    organization_id: str | None = None,
    workspace_id: str | None = None,
    success: bool = True,
    detail: str = "",
    ip: str | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    event = AuthAuditEvent(
        id=new_id("authaudit_"),
        event_type=event_type,
        actor_id=actor_id or "anonymous",
        organization_id=organization_id,
        workspace_id=workspace_id,
        success=success,
        detail=detail,
        ip=ip,
        metadata=dict(metadata or {}),
    )
    store.add_audit(event)
    return event.to_dict()


def list_auth_audits(
    *,
    limit: int = 50,
    organization_id: str | None = None,
    event_type: str | None = None,
) -> dict[str, Any]:
    items = store.list_audits(
        limit=limit, organization_id=organization_id, event_type=event_type
    )
    return {
        "ok": True,
        "count": len(items),
        "audits": [e.to_dict() for e in items],
    }
