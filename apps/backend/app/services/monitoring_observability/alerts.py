"""Alert Manager — generate and list system alerts."""

from __future__ import annotations

from typing import Any

from app.services.monitoring_observability import store
from app.services.monitoring_observability.models import (
    Alert,
    AlertLevel,
    ComponentHealth,
    MonitoringEvent,
    new_id,
)
from app.services.monitoring_observability.version import (
    CPU_HIGH_THRESHOLD,
    MEMORY_HIGH_THRESHOLD,
    RESPONSE_SLOW_MS,
)

ALERT_TYPES = (
    "api_failure",
    "queue_failure",
    "provider_offline",
    "database_error",
    "high_memory",
    "high_cpu",
    "slow_response",
    "auth_failure",
    "payment_failure",
    "storage_failure",
)


def raise_alert(
    alert_type: str,
    message: str,
    *,
    component: str,
    level: AlertLevel = "warning",
) -> dict[str, Any]:
    alert = Alert(
        alert_id=new_id("alert"),
        level=level,
        alert_type=alert_type,
        message=message,
        component=component,
    )
    store.add_alert(alert)
    store.add_event(
        MonitoringEvent(
            event_id=new_id("mevt"),
            category="alert",
            message=message,
            severity=level,
            component=component,
            metadata={"alert_type": alert_type},
        )
    )
    return alert.to_dict()


def evaluate_components(components: list[ComponentHealth]) -> list[dict[str, Any]]:
    raised = []
    for c in components:
        if c.name == "api" and c.status == "unhealthy":
            raised.append(raise_alert("api_failure", c.detail, component="api", level="critical"))
        if c.name == "queue" and c.status == "unhealthy":
            raised.append(raise_alert("queue_failure", c.detail, component="queue", level="error"))
        if c.name == "ai_providers" and c.status == "unhealthy":
            raised.append(
                raise_alert("provider_offline", c.detail, component="ai_providers", level="error")
            )
        if c.name == "database" and c.status == "unhealthy":
            raised.append(
                raise_alert("database_error", c.detail, component="database", level="critical")
            )
        if c.name == "memory" and float(c.metrics.get("memory_usage") or 0) >= MEMORY_HIGH_THRESHOLD:
            raised.append(
                raise_alert("high_memory", f"memory {c.metrics.get('memory_usage')}%", component="memory", level="warning")
            )
        if c.name == "cpu" and float(c.metrics.get("cpu_usage") or 0) >= CPU_HIGH_THRESHOLD:
            raised.append(
                raise_alert("high_cpu", f"cpu {c.metrics.get('cpu_usage')}%", component="cpu", level="warning")
            )
        if c.name == "paddle" and c.status == "unhealthy":
            raised.append(
                raise_alert("payment_failure", c.detail, component="paddle", level="error")
            )
        if c.name == "storage" and c.status == "unhealthy":
            raised.append(
                raise_alert("storage_failure", c.detail, component="storage", level="error")
            )
    samples = store.request_samples(60)
    if samples:
        avg = sum(s[2] for s in samples) / len(samples)
        if avg >= RESPONSE_SLOW_MS:
            raised.append(
                raise_alert(
                    "slow_response",
                    f"avg response {avg:.0f}ms",
                    component="api",
                    level="warning",
                )
            )
    return raised


def list_alerts(*, limit: int = 50, level: str | None = None) -> dict[str, Any]:
    items = store.alerts(limit=limit, level=level)
    return {
        "ok": True,
        "count": len(items),
        "alerts": [a.to_dict() for a in items],
        "alert_types": list(ALERT_TYPES),
    }
