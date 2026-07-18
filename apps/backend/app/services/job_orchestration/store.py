"""In-memory job store + history."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.job_orchestration.models import OrchestratedJob

_lock = threading.Lock()
_jobs: OrderedDict[str, "OrchestratedJob"] = OrderedDict()
_history: list[str] = []
_MAX = 5000


def save(job: "OrchestratedJob") -> "OrchestratedJob":
    with _lock:
        _jobs[job.job_id] = job
        if job.job_id not in _history:
            _history.append(job.job_id)
        while len(_jobs) > _MAX:
            old_id, _ = _jobs.popitem(last=False)
            try:
                _history.remove(old_id)
            except ValueError:
                pass
        return job


def get(job_id: str) -> "OrchestratedJob | None":
    with _lock:
        return _jobs.get(job_id)


def all_jobs() -> list["OrchestratedJob"]:
    with _lock:
        return list(_jobs.values())


def history(limit: int = 50) -> list["OrchestratedJob"]:
    with _lock:
        ids = list(_history[-max(1, min(1000, limit)) :])
        return [j for jid in reversed(ids) if (j := _jobs.get(jid))]


def clear() -> None:
    with _lock:
        _jobs.clear()
        _history.clear()
