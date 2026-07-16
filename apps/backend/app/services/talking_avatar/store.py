"""In-memory job store + history for Talking Avatar Engine."""

from __future__ import annotations

import threading
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.services.talking_avatar.models import TalkingAvatarJob

_lock = threading.Lock()
_jobs: OrderedDict[str, TalkingAvatarJob] = OrderedDict()
_history: list[dict[str, Any]] = []
_MAX_JOBS = 500
_MAX_HISTORY = 5000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def save_job(job: TalkingAvatarJob) -> TalkingAvatarJob:
    with _lock:
        _jobs[job.job_id] = job
        while len(_jobs) > _MAX_JOBS:
            _jobs.popitem(last=False)
        return job


def get_job(job_id: str) -> TalkingAvatarJob | None:
    with _lock:
        return _jobs.get(job_id)


def append_history(
    job_id: str,
    event: str,
    *,
    detail: dict[str, Any] | None = None,
) -> dict[str, Any]:
    with _lock:
        record = {
            "history_id": f"ahist_{uuid4().hex[:12]}",
            "job_id": job_id,
            "event": event,
            "timestamp": _now(),
            "detail": detail or {},
        }
        _history.append(record)
        while len(_history) > _MAX_HISTORY:
            _history.pop(0)
        return record


def history_for_job(job_id: str, limit: int = 200) -> list[dict[str, Any]]:
    with _lock:
        return [h for h in _history if h["job_id"] == job_id][-limit:]


def clear_all() -> None:
    with _lock:
        _jobs.clear()
        _history.clear()
