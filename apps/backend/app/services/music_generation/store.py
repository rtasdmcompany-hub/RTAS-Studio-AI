"""In-memory store for music jobs, library, versions, history."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.music_generation.models import MusicJob

_lock = threading.Lock()
_JOBS: OrderedDict[str, "MusicJob"] = OrderedDict()
_HISTORY: OrderedDict[str, list[dict]] = OrderedDict()
_LIBRARY: OrderedDict[str, dict[str, Any]] = OrderedDict()
_VERSIONS: OrderedDict[str, list[dict]] = OrderedDict()
_MAX = 2000


def put_job(job: "MusicJob") -> "MusicJob":
    with _lock:
        _JOBS[job.job_id] = job
        hist = _HISTORY.setdefault(job.job_id, [])
        hist.append({"version": len(hist) + 1, "state": job.state, "summary": job.summary()})
        job.history = list(hist)
        job.metadata["store_version"] = len(hist)
        while len(_JOBS) > _MAX:
            old_id, _ = _JOBS.popitem(last=False)
            _HISTORY.pop(old_id, None)
        return job


def get_job(job_id: str) -> "MusicJob | None":
    with _lock:
        return _JOBS.get(job_id)


def list_history(limit: int = 50) -> list[dict]:
    with _lock:
        items = list(_JOBS.values())[-limit:]
        return [j.summary() for j in reversed(items)]


def get_job_history(job_id: str) -> list[dict]:
    with _lock:
        return list(_HISTORY.get(job_id, []))


def put_library_entry(entry: dict[str, Any]) -> dict[str, Any]:
    with _lock:
        lid = entry["library_id"]
        _LIBRARY[lid] = entry
        while len(_LIBRARY) > _MAX:
            _LIBRARY.popitem(last=False)
        return entry


def get_library_entry(library_id: str) -> dict[str, Any] | None:
    with _lock:
        return _LIBRARY.get(library_id)


def list_library(
    *,
    genre: str | None = None,
    role: str | None = None,
    limit: int = 100,
) -> list[dict[str, Any]]:
    with _lock:
        items = list(_LIBRARY.values())
    if genre:
        items = [i for i in items if i.get("genre") == genre]
    if role:
        items = [i for i in items if i.get("role") == role]
    return list(reversed(items[-limit:]))


def put_version(job_id: str, snapshot: dict[str, Any]) -> list[dict]:
    with _lock:
        vers = _VERSIONS.setdefault(job_id, [])
        vers.append({"version": len(vers) + 1, **snapshot})
        return list(vers)


def get_versions(job_id: str | None = None) -> list[dict]:
    with _lock:
        if job_id:
            return list(_VERSIONS.get(job_id, []))
        # Flat recent versions across jobs
        out: list[dict] = []
        for jid, vers in _VERSIONS.items():
            for v in vers:
                out.append({"job_id": jid, **v})
        return out[-100:]


def clear() -> None:
    with _lock:
        _JOBS.clear()
        _HISTORY.clear()
        _LIBRARY.clear()
        _VERSIONS.clear()
