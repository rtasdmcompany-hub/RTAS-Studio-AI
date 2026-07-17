"""In-memory voice intelligence job store — keyed by project_id."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.voice_intelligence.models import VoiceIntelligenceJob

_lock = threading.Lock()
_by_project: OrderedDict[str, "VoiceIntelligenceJob"] = OrderedDict()
_by_job: OrderedDict[str, "VoiceIntelligenceJob"] = OrderedDict()
_MAX = 2000


def save(job: "VoiceIntelligenceJob") -> "VoiceIntelligenceJob":
    with _lock:
        _by_project[job.project_id] = job
        _by_job[job.job_id] = job
        while len(_by_project) > _MAX:
            _pid, old = _by_project.popitem(last=False)
            _by_job.pop(old.job_id, None)
        return job


def get_by_project(project_id: str) -> "VoiceIntelligenceJob | None":
    with _lock:
        return _by_project.get(project_id)


def get_by_job(job_id: str) -> "VoiceIntelligenceJob | None":
    with _lock:
        return _by_job.get(job_id)


def list_jobs(limit: int = 50) -> list["VoiceIntelligenceJob"]:
    with _lock:
        items = list(_by_project.values())
    return list(reversed(items[-max(1, min(500, limit)) :]))


def clear() -> None:
    with _lock:
        _by_project.clear()
        _by_job.clear()
