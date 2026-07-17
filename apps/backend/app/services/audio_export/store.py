"""In-memory export job store, history, analytics."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.audio_export.models import ExportJob

_lock = threading.Lock()
_jobs: OrderedDict[str, "ExportJob"] = OrderedDict()
_history: list[dict[str, Any]] = []
_analytics: list[dict[str, Any]] = []
_audit: list[dict[str, Any]] = []
_MAX = 2000
_HISTORY_MAX = 5000


def save(job: "ExportJob") -> "ExportJob":
    with _lock:
        _jobs[job.job_id] = job
        while len(_jobs) > _MAX:
            _jobs.popitem(last=False)
        return job


def get(job_id: str) -> "ExportJob | None":
    with _lock:
        return _jobs.get(job_id)


def append_history(entry: dict[str, Any]) -> None:
    with _lock:
        _history.append({**entry, "ts": entry.get("ts") or time.time()})
        while len(_history) > _HISTORY_MAX:
            _history.pop(0)


def append_analytics(entry: dict[str, Any]) -> None:
    with _lock:
        _analytics.append({**entry, "ts": entry.get("ts") or time.time()})
        while len(_analytics) > _HISTORY_MAX:
            _analytics.pop(0)


def append_audit(entry: dict[str, Any]) -> None:
    with _lock:
        _audit.append({**entry, "ts": entry.get("ts") or time.time()})
        while len(_audit) > _HISTORY_MAX:
            _audit.pop(0)


def history(
    *,
    limit: int = 50,
    parent_generation_id: str | None = None,
) -> list[dict[str, Any]]:
    with _lock:
        items = list(_history)
    if parent_generation_id:
        items = [
            h
            for h in items
            if h.get("parent_generation_id") == parent_generation_id
            or h.get("parentGenerationId") == parent_generation_id
        ]
    return list(reversed(items[-max(1, min(500, limit)) :]))


def analytics(limit: int = 50) -> list[dict[str, Any]]:
    with _lock:
        items = list(_analytics)
    return list(reversed(items[-max(1, min(500, limit)) :]))


def audit_logs(limit: int = 50) -> list[dict[str, Any]]:
    with _lock:
        items = list(_audit)
    return list(reversed(items[-max(1, min(500, limit)) :]))


def clear() -> None:
    with _lock:
        _jobs.clear()
        _history.clear()
        _analytics.clear()
        _audit.clear()
