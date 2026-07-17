"""In-memory store + version history for voice jobs."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.voice_generation.models import VoiceGenerationJob

_lock = threading.Lock()
_JOBS: OrderedDict[str, "VoiceGenerationJob"] = OrderedDict()
_HISTORY: OrderedDict[str, list[dict]] = OrderedDict()
_MAX = 2000


def put_job(job: "VoiceGenerationJob") -> "VoiceGenerationJob":
    with _lock:
        _JOBS[job.job_id] = job
        hist = _HISTORY.setdefault(job.job_id, [])
        hist.append(
            {
                "version": len(hist) + 1,
                "state": job.state,
                "summary": job.summary(),
            }
        )
        job.history = list(hist)
        job.metadata["version"] = len(hist)
        while len(_JOBS) > _MAX:
            old_id, _ = _JOBS.popitem(last=False)
            _HISTORY.pop(old_id, None)
        return job


def get_job(job_id: str) -> "VoiceGenerationJob | None":
    with _lock:
        return _JOBS.get(job_id)


def list_history(limit: int = 50) -> list[dict]:
    with _lock:
        items = list(_JOBS.values())[-limit:]
        return [j.summary() for j in reversed(items)]


def get_job_history(job_id: str) -> list[dict]:
    with _lock:
        return list(_HISTORY.get(job_id, []))


def clear() -> None:
    with _lock:
        _JOBS.clear()
        _HISTORY.clear()
