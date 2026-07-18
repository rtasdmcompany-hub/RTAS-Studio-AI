"""Incident Manager — open, mitigate, resolve incidents."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from app.services.monitoring_observability import store
from app.services.monitoring_observability.models import (
    Incident,
    IncidentSeverity,
    IncidentStatus,
    new_id,
)


def open_incident(
    title: str,
    *,
    component: str,
    severity: IncidentSeverity = "medium",
    description: str = "",
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    # Dedupe open incident for same component+title
    for existing in store.all_incidents(limit=100):
        if (
            existing.status in ("open", "acknowledged", "mitigating")
            and existing.component == component
            and existing.title == title
        ):
            return existing.to_dict()
    inc = Incident(
        incident_id=new_id("inc"),
        title=title,
        severity=severity,
        status="open",
        component=component,
        description=description or title,
        metadata=dict(metadata or {}),
    )
    store.save_incident(inc)
    return inc.to_dict()


def update_status(
    incident_id: str,
    status: IncidentStatus,
    *,
    recovery_action: str | None = None,
) -> dict[str, Any]:
    inc = store.get_incident(incident_id)
    if not inc:
        raise ValueError("incident not found")
    inc.status = status
    if recovery_action:
        inc.recovery_actions.append(recovery_action)
    if status == "resolved":
        inc.resolved_at = datetime.now(timezone.utc).isoformat()
    store.save_incident(inc)
    return inc.to_dict()


def list_incidents(*, limit: int = 50, status: str | None = None) -> dict[str, Any]:
    items = store.all_incidents(limit=limit)
    if status:
        items = [i for i in items if i.status == status]
    return {
        "ok": True,
        "count": len(items),
        "incidents": [i.to_dict() for i in items],
    }


def open_from_unhealthy(components: list) -> list[dict[str, Any]]:
    opened = []
    for c in components:
        if getattr(c, "status", None) != "unhealthy":
            continue
        sev: IncidentSeverity = "critical" if c.name in ("api", "database") else "high"
        opened.append(
            open_incident(
                f"{c.name} unhealthy",
                component=c.name,
                severity=sev,
                description=c.detail,
            )
        )
    return opened
