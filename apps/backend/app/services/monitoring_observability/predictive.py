"""Predictive Failure Analyzer — simple trend-based risk scoring."""

from __future__ import annotations

from typing import Any

from app.services.monitoring_observability import store
from app.services.monitoring_observability.version import (
    CPU_HIGH_THRESHOLD,
    MEMORY_HIGH_THRESHOLD,
    RESPONSE_SLOW_MS,
)


def analyze() -> dict[str, Any]:
    samples = store.request_samples(300)
    total = len(samples)
    failures = sum(1 for s in samples if not s[1])
    avg_latency = (sum(s[2] for s in samples) / total) if total else 0.0
    fail_rate = (failures / total * 100.0) if total else 0.0

    # Recent half vs older half latency trend
    risk = 0.0
    reasons: list[str] = []
    if total >= 10:
        mid = total // 2
        older = samples[:mid]
        newer = samples[mid:]
        old_lat = sum(s[2] for s in older) / len(older)
        new_lat = sum(s[2] for s in newer) / len(newer)
        if new_lat > old_lat * 1.5 and new_lat > 200:
            risk += 25
            reasons.append("rising response latency trend")
        new_fail = sum(1 for s in newer if not s[1]) / len(newer)
        old_fail = sum(1 for s in older if not s[1]) / len(older)
        if new_fail > old_fail + 0.1:
            risk += 30
            reasons.append("rising failure rate trend")

    if avg_latency >= RESPONSE_SLOW_MS * 0.6:
        risk += 15
        reasons.append("elevated average latency")
    if fail_rate >= 10:
        risk += 25
        reasons.append("failure rate above 10%")
    if store.queue_depth() > 50:
        risk += 15
        reasons.append("queue depth elevated")
    if store.stuck_jobs():
        risk += 20
        reasons.append("stuck jobs present")

    # Resource projection from request pressure
    load = min(100.0, total * 2.0)
    cpu = 20.0 + load * 0.4
    mem = 25.0 + load * 0.35
    if cpu >= CPU_HIGH_THRESHOLD * 0.8:
        risk += 10
        reasons.append("cpu approaching threshold")
    if mem >= MEMORY_HIGH_THRESHOLD * 0.8:
        risk += 10
        reasons.append("memory approaching threshold")

    risk = min(100.0, risk)
    level = "low"
    if risk >= 70:
        level = "critical"
    elif risk >= 45:
        level = "high"
    elif risk >= 25:
        level = "medium"

    return {
        "ok": True,
        "risk_score": round(risk, 2),
        "risk_level": level,
        "predicted_failure": risk >= 45,
        "reasons": reasons,
        "signals": {
            "sample_count": total,
            "failure_rate": round(fail_rate, 2),
            "avg_latency_ms": round(avg_latency, 2),
            "queue_depth": store.queue_depth(),
            "stuck_jobs": len(store.stuck_jobs()),
            "cpu_estimate": round(cpu, 2),
            "memory_estimate": round(mem, 2),
        },
        "recommendation": (
            "run recovery suite"
            if risk >= 45
            else ("monitor closely" if risk >= 25 else "healthy")
        ),
    }
