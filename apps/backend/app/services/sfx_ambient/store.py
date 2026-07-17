"""In-memory store for SFX/ambient jobs, library, history."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.sfx_ambient.models import SfxJob

_lock = threading.Lock()
_JOBS: OrderedDict[str, "SfxJob"] = OrderedDict()
_HISTORY: OrderedDict[str, list[dict]] = OrderedDict()
_LIBRARY: OrderedDict[str, dict[str, Any]] = OrderedDict()
_MAX = 2000


def put_job(job: "SfxJob") -> "SfxJob":
    with _lock:
        _JOBS[job.job_id] = job
        hist = _HISTORY.setdefault(job.job_id, [])
        hist.append({"version": len(hist) + 1, "state": job.state, "summary": job.summary()})
        job.history = list(hist)
        job.metadata["version"] = len(hist)
        while len(_JOBS) > _MAX:
            old_id, _ = _JOBS.popitem(last=False)
            _HISTORY.pop(old_id, None)
        return job


def get_job(job_id: str) -> "SfxJob | None":
    with _lock:
        return _JOBS.get(job_id)


def list_history(limit: int = 50, *, kind: str | None = None) -> list[dict]:
    with _lock:
        items = list(_JOBS.values())
        if kind:
            items = [j for j in items if j.kind == kind]
        return [j.summary() for j in reversed(items[-limit:])]


def get_job_history(job_id: str) -> list[dict]:
    with _lock:
        return list(_HISTORY.get(job_id, []))


def put_library_entry(entry_id: str, payload: dict[str, Any]) -> None:
    with _lock:
        _LIBRARY[entry_id] = payload
        while len(_LIBRARY) > _MAX:
            _LIBRARY.popitem(last=False)


def list_library(*, kind: str | None = None, category: str | None = None, limit: int = 100) -> list[dict]:
    with _lock:
        items = list(_LIBRARY.values())
        if kind:
            items = [i for i in items if i.get("kind") == kind]
        if category:
            items = [i for i in items if category in (i.get("categories") or []) or i.get("category") == category]
        return items[-limit:]


def clear() -> None:
    with _lock:
        _JOBS.clear()
        _HISTORY.clear()
        _LIBRARY.clear()
