"""Monitoring Engine facade — health, metrics, incidents, alerts, recovery, status."""

from __future__ import annotations

from typing import Any

from app.services.monitoring_observability import (
    alerts,
    diagnostics,
    health_monitor,
    incidents,
    metrics,
    predictive,
    self_healing,
    store,
)
from app.services.monitoring_observability.models import MonitoringEvent, new_id
from app.services.monitoring_observability.version import ENGINE_LABEL, ENGINE_NAME, ENGINE_VERSION


class MonitoringObservabilityEngine:
    def __init__(self) -> None:
        # Seed a default online worker pool for dashboards
        if not store.workers():
            for i in range(3):
                store.set_worker(f"worker_{i}", "online")

    def refresh(self) -> dict[str, Any]:
        """Collect health, raise alerts, open incidents, run predictive analysis."""
        report = health_monitor.collect_health()
        raised = alerts.evaluate_components(report.components)
        opened = incidents.open_from_unhealthy(report.components)
        prediction = predictive.analyze()
        if prediction.get("predicted_failure"):
            store.add_event(
                MonitoringEvent(
                    event_id=new_id("mevt"),
                    category="predictive",
                    message=f"predicted failure risk={prediction['risk_score']}",
                    severity="warning",
                    metadata=prediction,
                )
            )
        return {
            "health": report.to_dict(),
            "alerts_raised": len(raised),
            "incidents_opened": len(opened),
            "prediction": prediction,
        }

    def health(self) -> dict[str, Any]:
        self.refresh()
        payload = health_monitor.health_payload()
        return {
            "ok": payload.get("ok", True),
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            **payload,
            "prediction": predictive.analyze(),
        }

    def metrics(self) -> dict[str, Any]:
        return {
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            **metrics.metrics_payload(),
            "prediction": predictive.analyze(),
        }

    def incidents(self, *, limit: int = 50, status: str | None = None) -> dict[str, Any]:
        result = incidents.list_incidents(limit=limit, status=status)
        return {
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            **result,
        }

    def alerts(self, *, limit: int = 50, level: str | None = None) -> dict[str, Any]:
        result = alerts.list_alerts(limit=limit, level=level)
        return {
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            **result,
        }

    def recovery(self, payload: dict[str, Any] | None = None) -> dict[str, Any]:
        body = payload or {}
        result = self_healing.run_recovery(
            actions=body.get("actions"),
            component=body.get("component"),
            job_ids=body.get("job_ids") or body.get("jobIds"),
        )
        # Post-recovery health refresh
        health = health_monitor.collect_health()
        return {
            "ok": result.get("ok", True),
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            **result,
            "health_after": health.to_dict(),
            "diagnostics": diagnostics.run_diagnostics(),
        }

    def status(self) -> dict[str, Any]:
        refreshed = self.refresh()
        snap = metrics.performance_snapshot()
        return {
            "ok": refreshed["health"]["overall"] != "unhealthy",
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "overall": refreshed["health"]["overall"],
            "uptime_sec": store.uptime_sec(),
            "health": refreshed["health"],
            "metrics": snap.to_dict(),
            "prediction": refreshed["prediction"],
            "open_incidents": incidents.list_incidents(status="open", limit=20),
            "recent_alerts": alerts.list_alerts(limit=20),
            "recent_recoveries": [r.to_dict() for r in store.recoveries(limit=20)],
            "dashboard": metrics.metrics_payload().get("dashboard"),
            "self_healing": {
                "enabled": True,
                "actions": [
                    "restart_worker",
                    "retry_job",
                    "reconnect_service",
                    "refresh_token",
                    "recover_queue",
                    "detect_deadlock",
                    "recover_stuck_job",
                    "failover",
                ],
            },
        }

    # Test helpers
    def record_request(self, *, success: bool = True, latency_ms: float = 50.0) -> None:
        store.record_request(success, latency_ms)

    def simulate_failure(self, component: str) -> None:
        store.force_failure(component)

    def clear_failure(self, component: str) -> None:
        store.clear_failure(component)


_engine: MonitoringObservabilityEngine | None = None


def get_monitoring_engine() -> MonitoringObservabilityEngine:
    global _engine
    if _engine is None:
        _engine = MonitoringObservabilityEngine()
    return _engine


def reset_engine() -> None:
    global _engine
    store.clear()
    _engine = None
