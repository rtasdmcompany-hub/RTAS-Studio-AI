"""Dead-letter queue for exhausted orchestration jobs."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any

_lock = threading.Lock()
_DLQ: OrderedDict[str, dict[str, Any]] = OrderedDict()
_MAX_DLQ = 2000


def push(job_id: str, *, error: str, payload: dict[str, Any] | None = None) -> dict[str, Any]:
    entry = {
        "jobId": job_id,
        "error": (error or "")[:500],
        "payload": dict(payload or {}),
        "enqueuedAt": time.time(),
        "recovered": False,
    }
    with _lock:
        _DLQ[job_id] = entry
        while len(_DLQ) > _MAX_DLQ:
            _DLQ.popitem(last=False)
    return entry


def list_entries(limit: int = 50) -> list[dict[str, Any]]:
    with _lock:
        items = list(_DLQ.values())[-max(1, min(500, limit)) :]
        return list(reversed(items))


def get(job_id: str) -> dict[str, Any] | None:
    with _lock:
        return _DLQ.get(job_id)


def pop(job_id: str) -> dict[str, Any] | None:
    with _lock:
        return _DLQ.pop(job_id, None)


def depth() -> int:
    with _lock:
        return len(_DLQ)


def clear() -> None:
    with _lock:
        _DLQ.clear()


def statistics() -> dict[str, Any]:
    with _lock:
        return {
            "depth": len(_DLQ),
            "maxDepth": _MAX_DLQ,
            "recoveredCount": sum(1 for e in _DLQ.values() if e.get("recovered")),
        }
