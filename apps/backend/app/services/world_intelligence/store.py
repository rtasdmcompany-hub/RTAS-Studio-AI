"""In-memory world intelligence job store."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.world_intelligence.models import WorldIntelligenceJob

_lock = threading.Lock()
_jobs: OrderedDict[str, "WorldIntelligenceJob"] = OrderedDict()
_history: list[str] = []
_MAX = 2000


def save(job: "WorldIntelligenceJob") -> "WorldIntelligenceJob":
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


def get(job_id: str) -> "WorldIntelligenceJob | None":
    with _lock:
        return _jobs.get(job_id)


def history(limit: int = 50) -> list["WorldIntelligenceJob"]:
    with _lock:
        ids = list(_history[-max(1, min(500, limit)) :])
        return [j for jid in reversed(ids) if (j := _jobs.get(jid))]


def clear() -> None:
    with _lock:
        _jobs.clear()
        _history.clear()
