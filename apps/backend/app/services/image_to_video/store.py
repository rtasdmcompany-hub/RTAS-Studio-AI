"""Job metadata + generation history for Image-to-Video."""

from __future__ import annotations

import threading
from collections import OrderedDict
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

from app.services.image_to_video.models import HistoryRecord, ImageToVideoJob

_lock = threading.Lock()
_jobs: OrderedDict[str, ImageToVideoJob] = OrderedDict()
_history: list[HistoryRecord] = []
_MAX_JOBS = 500
_MAX_HISTORY = 5000


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


class MetadataStore:
    def save_job(self, job: ImageToVideoJob) -> ImageToVideoJob:
        with _lock:
            job.updated_at = _now()
            _jobs[job.job_id] = job
            while len(_jobs) > _MAX_JOBS:
                _jobs.popitem(last=False)
            return job

    def get_job(self, job_id: str) -> ImageToVideoJob | None:
        with _lock:
            return _jobs.get(job_id)

    def list_jobs(self, limit: int = 50) -> list[ImageToVideoJob]:
        with _lock:
            return list(_jobs.values())[-limit:]

    def update_job_state(
        self, job_id: str, state: str, **metadata: Any
    ) -> ImageToVideoJob | None:
        with _lock:
            job = _jobs.get(job_id)
            if not job:
                return None
            job.state = state  # type: ignore[assignment]
            job.updated_at = _now()
            if metadata:
                job.metadata.update(metadata)
            return job


class HistoryStore:
    def append(
        self,
        *,
        job_id: str,
        event: str,
        request_id: str | None = None,
        detail: dict[str, Any] | None = None,
    ) -> HistoryRecord:
        with _lock:
            record = HistoryRecord(
                history_id=f"ihist_{uuid4().hex[:12]}",
                job_id=job_id,
                request_id=request_id,
                event=event,
                timestamp=_now(),
                detail=detail or {},
            )
            _history.append(record)
            while len(_history) > _MAX_HISTORY:
                _history.pop(0)
            return record

    def for_job(self, job_id: str, limit: int = 200) -> list[HistoryRecord]:
        with _lock:
            return [h for h in _history if h.job_id == job_id][-limit:]

    def recent(self, limit: int = 100) -> list[HistoryRecord]:
        with _lock:
            return list(_history[-limit:])


metadata_store = MetadataStore()
history_store = HistoryStore()


def clear_all_stores() -> None:
    with _lock:
        _jobs.clear()
        _history.clear()
