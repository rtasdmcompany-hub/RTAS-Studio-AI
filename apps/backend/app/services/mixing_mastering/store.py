"""In-memory store for mix/master jobs and quality reports."""

from __future__ import annotations

import threading
from collections import OrderedDict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.services.mixing_mastering.models import MixMasterJob

_lock = threading.Lock()
_JOBS: OrderedDict[str, "MixMasterJob"] = OrderedDict()
_HISTORY: OrderedDict[str, list[dict]] = OrderedDict()
_BY_MIX: dict[str, str] = {}
_BY_MASTER: dict[str, str] = {}
_MAX = 2000


def put_job(job: "MixMasterJob") -> "MixMasterJob":
    with _lock:
        _JOBS[job.job_id] = job
        mix_id = job.mix_job_id or job.job_id
        _BY_MIX[mix_id] = job.job_id
        if job.master_job_id:
            _BY_MASTER[job.master_job_id] = job.job_id
        hist = _HISTORY.setdefault(job.job_id, [])
        hist.append({"version": len(hist) + 1, "state": job.state, "summary": job.summary()})
        job.history = list(hist)
        job.metadata["version"] = len(hist)
        while len(_JOBS) > _MAX:
            old_id, _ = _JOBS.popitem(last=False)
            _HISTORY.pop(old_id, None)
        return job


def get_job(job_id: str) -> "MixMasterJob | None":
    with _lock:
        if job_id in _JOBS:
            return _JOBS[job_id]
        real = _BY_MIX.get(job_id) or _BY_MASTER.get(job_id)
        return _JOBS.get(real) if real else None


def get_job_history(job_id: str) -> list[dict]:
    with _lock:
        if job_id in _JOBS:
            jid = job_id
        else:
            jid = _BY_MIX.get(job_id) or _BY_MASTER.get(job_id)
        if not jid:
            return []
        return list(_HISTORY.get(jid, []))


def list_history(limit: int = 50) -> list[dict]:
    with _lock:
        items = list(_JOBS.values())[-limit:]
        return [j.summary() for j in reversed(items)]


def clear() -> None:
    with _lock:
        _JOBS.clear()
        _HISTORY.clear()
        _BY_MIX.clear()
        _BY_MASTER.clear()
