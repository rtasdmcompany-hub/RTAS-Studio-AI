"""Production queue for emotion intelligence jobs."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict, deque
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.emotion_intelligence.models import EmotionIntelligenceJob, EmotionJobState

_lock = threading.Lock()
_queue: deque[str] = deque()
_jobs: OrderedDict[str, "EmotionIntelligenceJob"] = OrderedDict()
_enqueued_at: dict[str, float] = {}
_MAX = 2000


class EmotionQueue:
    def enqueue(self, job: "EmotionIntelligenceJob") -> "EmotionIntelligenceJob":
        with _lock:
            job.state = "queued"
            job.queue_position = len(_queue) + 1
            _jobs[job.job_id] = job
            if job.job_id not in _queue:
                _queue.append(job.job_id)
            _enqueued_at[job.job_id] = time.perf_counter()
            while len(_jobs) > _MAX:
                old_id, _ = _jobs.popitem(last=False)
                try:
                    _queue.remove(old_id)
                except ValueError:
                    pass
                _enqueued_at.pop(old_id, None)
            self._reindex()
            return job

    def update_state(
        self,
        job_id: str,
        state: "EmotionJobState",
        *,
        error: str | None = None,
    ) -> "EmotionIntelligenceJob | None":
        with _lock:
            job = _jobs.get(job_id)
            if not job:
                return None
            job.state = state
            if error:
                job.error = error
                if job.observability:
                    job.observability.errors.append(error)
            if state in ("completed", "failed", "cancelled"):
                job.queue_position = None
            self._reindex()
            return job

    def retry(self, job_id: str) -> "EmotionIntelligenceJob | None":
        with _lock:
            job = _jobs.get(job_id)
            if not job:
                return None
            if job.state not in ("failed", "cancelled", "completed"):
                return job
            job.retry_count += 1
            if job.observability:
                job.observability.retry_count = job.retry_count
            job.state = "retrying"
            job.error = None
            if job_id not in _queue:
                _queue.append(job_id)
            job.queue_position = len(_queue)
            _enqueued_at[job_id] = time.perf_counter()
            self._reindex()
            return job

    def cancel(self, job_id: str) -> "EmotionIntelligenceJob | None":
        with _lock:
            job = _jobs.get(job_id)
            if not job:
                return None
            try:
                _queue.remove(job_id)
            except ValueError:
                pass
            job.state = "cancelled"
            job.queue_position = None
            self._reindex()
            return job

    def get(self, job_id: str) -> "EmotionIntelligenceJob | None":
        with _lock:
            return _jobs.get(job_id)

    def queue_wait_ms(self, job_id: str) -> float:
        with _lock:
            started = _enqueued_at.get(job_id)
            if not started:
                return 0.0
            return round((time.perf_counter() - started) * 1000.0, 3)

    def status(self) -> dict[str, Any]:
        with _lock:
            return {
                "queued": len(_queue),
                "jobs": len(_jobs),
                "states": {
                    s: sum(1 for j in _jobs.values() if j.state == s)
                    for s in (
                        "queued",
                        "preparing",
                        "emotion_analysis",
                        "expression_generation",
                        "performance_optimization",
                        "completed",
                        "failed",
                        "cancelled",
                        "retrying",
                    )
                },
            }

    def clear(self) -> None:
        with _lock:
            _queue.clear()
            _jobs.clear()
            _enqueued_at.clear()

    def _reindex(self) -> None:
        for i, jid in enumerate(_queue, start=1):
            job = _jobs.get(jid)
            if job and job.state in ("queued", "retrying"):
                job.queue_position = i


emotion_queue = EmotionQueue()
