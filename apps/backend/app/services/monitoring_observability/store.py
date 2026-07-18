"""Thread-safe monitoring / incident / alert / recovery store."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import TYPE_CHECKING

from app.services.monitoring_observability.version import MAX_ALERTS, MAX_INCIDENTS

if TYPE_CHECKING:
    from app.services.monitoring_observability.models import (
        Alert,
        HealthReport,
        Incident,
        MonitoringEvent,
        RecoveryRecord,
    )

_lock = threading.Lock()
_started_at = time.time()
_health_reports: list["HealthReport"] = []
_events: list["MonitoringEvent"] = []
_incidents: OrderedDict[str, "Incident"] = OrderedDict()
_alerts: list["Alert"] = []
_recoveries: list["RecoveryRecord"] = []
_request_samples: list[tuple[float, bool, float]] = []  # ts, success, latency_ms
_workers: dict[str, dict] = {}
_stuck_jobs: set[str] = set()
_queue_depth = 0
_provider_states: dict[str, str] = {}
_forced_failures: set[str] = set()


def uptime_sec() -> float:
    return time.time() - _started_at


def save_health(report: "HealthReport") -> None:
    with _lock:
        _health_reports.append(report)
        if len(_health_reports) > 200:
            del _health_reports[:50]


def latest_health() -> "HealthReport | None":
    with _lock:
        return _health_reports[-1] if _health_reports else None


def add_event(event: "MonitoringEvent") -> None:
    with _lock:
        _events.append(event)
        if len(_events) > 5000:
            del _events[:1000]


def events(limit: int = 50) -> list["MonitoringEvent"]:
    with _lock:
        return list(reversed(_events[-max(1, min(500, limit)) :]))


def save_incident(inc: "Incident") -> "Incident":
    with _lock:
        _incidents[inc.incident_id] = inc
        while len(_incidents) > MAX_INCIDENTS:
            _incidents.popitem(last=False)
        return inc


def get_incident(incident_id: str) -> "Incident | None":
    with _lock:
        return _incidents.get(incident_id)


def all_incidents(limit: int = 50) -> list["Incident"]:
    with _lock:
        items = list(_incidents.values())
        return list(reversed(items[-max(1, min(500, limit)) :]))


def add_alert(alert: "Alert") -> None:
    with _lock:
        _alerts.append(alert)
        if len(_alerts) > MAX_ALERTS:
            del _alerts[:1000]


def alerts(limit: int = 50, level: str | None = None) -> list["Alert"]:
    with _lock:
        items = [a for a in _alerts if not level or a.level == level]
        return list(reversed(items[-max(1, min(500, limit)) :]))


def add_recovery(rec: "RecoveryRecord") -> None:
    with _lock:
        _recoveries.append(rec)
        if len(_recoveries) > 3000:
            del _recoveries[:500]


def recoveries(limit: int = 50) -> list["RecoveryRecord"]:
    with _lock:
        return list(reversed(_recoveries[-max(1, min(500, limit)) :]))


def record_request(success: bool, latency_ms: float) -> None:
    with _lock:
        _request_samples.append((time.time(), success, latency_ms))
        if len(_request_samples) > 5000:
            del _request_samples[:1000]


def request_samples(window_sec: float = 300.0) -> list[tuple[float, bool, float]]:
    with _lock:
        cutoff = time.time() - window_sec
        return [s for s in _request_samples if s[0] >= cutoff]


def set_worker(worker_id: str, status: str, **extra) -> None:
    with _lock:
        _workers[worker_id] = {"worker_id": worker_id, "status": status, **extra}


def workers() -> list[dict]:
    with _lock:
        return list(_workers.values())


def mark_stuck_job(job_id: str) -> None:
    with _lock:
        _stuck_jobs.add(job_id)


def clear_stuck_job(job_id: str) -> None:
    with _lock:
        _stuck_jobs.discard(job_id)


def stuck_jobs() -> list[str]:
    with _lock:
        return list(_stuck_jobs)


def set_queue_depth(n: int) -> None:
    global _queue_depth
    with _lock:
        _queue_depth = max(0, int(n))


def queue_depth() -> int:
    with _lock:
        return _queue_depth


def set_provider_state(name: str, state: str) -> None:
    with _lock:
        _provider_states[name] = state


def provider_states() -> dict[str, str]:
    with _lock:
        return dict(_provider_states)


def force_failure(component: str) -> None:
    with _lock:
        _forced_failures.add(component)


def clear_failure(component: str) -> None:
    with _lock:
        _forced_failures.discard(component)


def is_forced_failure(component: str) -> bool:
    with _lock:
        return component in _forced_failures


def clear() -> None:
    global _started_at, _queue_depth
    with _lock:
        _started_at = time.time()
        _health_reports.clear()
        _events.clear()
        _incidents.clear()
        _alerts.clear()
        _recoveries.clear()
        _request_samples.clear()
        _workers.clear()
        _stuck_jobs.clear()
        _queue_depth = 0
        _provider_states.clear()
        _forced_failures.clear()
