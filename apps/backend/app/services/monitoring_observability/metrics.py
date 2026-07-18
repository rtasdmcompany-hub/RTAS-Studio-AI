"""Observability metrics aggregation."""

from __future__ import annotations

from typing import Any

from app.services.monitoring_observability import store
from app.services.monitoring_observability.models import PerformanceSnapshot


def performance_snapshot() -> PerformanceSnapshot:
    samples = store.request_samples(300)
    total = len(samples)
    successes = sum(1 for s in samples if s[1])
    failures = total - successes
    avg = (sum(s[2] for s in samples) / total) if total else 0.0
    # request rate per minute
    rate = (total / 5.0) if total else 0.0  # window 300s => per minute approx total/5
    workers = store.workers()
    online = sum(1 for w in workers if w.get("status") == "online")
    error_categories: dict[str, int] = {}
    if failures:
        error_categories["request_failure"] = failures
    if store.stuck_jobs():
        error_categories["stuck_jobs"] = len(store.stuck_jobs())
    for a in store.alerts(limit=100):
        error_categories[a.alert_type] = error_categories.get(a.alert_type, 0) + 1

    provider_lat = 0.0
    states = store.provider_states()
    if states:
        provider_lat = 120.0 if all(v == "healthy" for v in states.values()) else 400.0

    return PerformanceSnapshot(
        request_rate=round(rate, 2),
        success_rate=round((successes / total * 100.0) if total else 100.0, 2),
        failure_rate=round((failures / total * 100.0) if total else 0.0, 2),
        avg_response_ms=round(avg, 2),
        queue_latency_ms=round(10.0 + store.queue_depth() * 2.0, 2),
        provider_latency_ms=provider_lat,
        active_jobs=store.queue_depth() + len(store.stuck_jobs()),
        workers_online=online,
        workers_total=max(len(workers), online),
        uptime_sec=round(store.uptime_sec(), 2),
        error_categories=error_categories,
    )


def metrics_payload() -> dict[str, Any]:
    snap = performance_snapshot()
    return {
        "ok": True,
        **snap.to_dict(),
        "dashboard": {
            "charts": {
                "success_rate": snap.success_rate,
                "failure_rate": snap.failure_rate,
                "response_time": snap.avg_response_ms,
                "request_rate": snap.request_rate,
            },
            "panels": {
                "active_jobs": snap.active_jobs,
                "workers": f"{snap.workers_online}/{snap.workers_total}",
                "uptime_sec": snap.uptime_sec,
            },
        },
    }
