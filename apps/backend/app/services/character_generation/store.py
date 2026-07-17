"""In-memory character job store."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.character_generation.models import CharacterJob

_lock = threading.Lock()
_jobs: OrderedDict[str, "CharacterJob"] = OrderedDict()
_MAX = 2000


def save(job: "CharacterJob") -> "CharacterJob":
    with _lock:
        _jobs[job.job_id] = job
        while len(_jobs) > _MAX:
            _jobs.popitem(last=False)
        return job


def get(job_id: str) -> "CharacterJob | None":
    with _lock:
        return _jobs.get(job_id)


def list_jobs(limit: int = 50) -> list["CharacterJob"]:
    with _lock:
        jobs = list(_jobs.values())
    return list(reversed(jobs[-max(1, min(500, limit)) :]))


def clear() -> None:
    with _lock:
        _jobs.clear()
