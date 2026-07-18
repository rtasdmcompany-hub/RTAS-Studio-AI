"""System Diagnostics Engine."""

from __future__ import annotations

from typing import Any

from app.services.monitoring_observability import health_monitor, store
from app.services.monitoring_observability.models import MonitoringEvent, new_id


def run_diagnostics() -> dict[str, Any]:
    report = health_monitor.collect_health()
    workers = store.workers()
    stuck = store.stuck_jobs()
    findings = []
    for c in report.components:
        if c.status == "unhealthy":
            findings.append(f"{c.name}: {c.detail}")
        elif c.status == "degraded":
            findings.append(f"{c.name} degraded: {c.detail}")
    if stuck:
        findings.append(f"stuck jobs: {len(stuck)}")
    offline_workers = [w for w in workers if w.get("status") != "online"]
    if offline_workers:
        findings.append(f"offline workers: {len(offline_workers)}")

    store.add_event(
        MonitoringEvent(
            event_id=new_id("mevt"),
            category="diagnostics",
            message=f"diagnostics complete findings={len(findings)}",
            severity="warning" if findings else "info",
            metadata={"findings": findings[:20]},
        )
    )
    return {
        "ok": report.overall != "unhealthy",
        "overall": report.overall,
        "findings": findings,
        "components": [c.to_dict() for c in report.components],
        "workers": workers,
        "stuck_jobs": stuck,
        "queue_depth": store.queue_depth(),
        "uptime_sec": store.uptime_sec(),
    }
