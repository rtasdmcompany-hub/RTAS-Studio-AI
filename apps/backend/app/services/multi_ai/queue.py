"""In-process generation job queue with progress tracking."""

from __future__ import annotations

import threading
from collections import OrderedDict

from app.services.multi_ai.models import QueueJob, QueueState

_lock = threading.Lock()
_jobs: OrderedDict[str, QueueJob] = OrderedDict()
_MAX_JOBS = 500


class GenerationQueue:
    """Thread-safe in-memory queue for Multi-AI generation jobs."""

    def enqueue(self, job_id: str, provider: str) -> QueueJob:
        with _lock:
            job = QueueJob(job_id=job_id, provider=provider, state="queued")
            _jobs[job_id] = job
            while len(_jobs) > _MAX_JOBS:
                _jobs.popitem(last=False)
            return job

    def update(
        self,
        job_id: str,
        *,
        state: QueueState | None = None,
        progress_percent: int | None = None,
        provider: str | None = None,
        error: str | None = None,
        result_url: str | None = None,
        attempts: int | None = None,
        **metadata,
    ) -> QueueJob | None:
        with _lock:
            job = _jobs.get(job_id)
            if not job:
                return None
            if state is not None:
                job.state = state
            if progress_percent is not None:
                job.progress_percent = max(0, min(100, progress_percent))
            if provider is not None:
                job.provider = provider
            if error is not None:
                job.error = error
            if result_url is not None:
                job.result_url = result_url
            if attempts is not None:
                job.attempts = attempts
            if metadata:
                job.metadata.update(metadata)
            return job

    def get(self, job_id: str) -> QueueJob | None:
        with _lock:
            job = _jobs.get(job_id)
            return QueueJob(**job.to_dict()) if job else None

    def list_recent(self, limit: int = 50) -> list[QueueJob]:
        with _lock:
            items = list(_jobs.values())[-limit:]
            return [QueueJob(**j.to_dict()) for j in items]


generation_queue = GenerationQueue()
