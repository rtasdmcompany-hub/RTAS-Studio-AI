"""Mix/Master queue — mixing / mastering / quality_check states."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict, deque
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.mixing_mastering.models import MixJobState, MixMasterJob

_lock = threading.Lock()
_queue: deque[str] = deque()
_jobs: OrderedDict[str, "MixMasterJob"] = OrderedDict()
_enqueued_at: dict[str, float] = {}
_MAX = 2000


class MixQueue:
    def enqueue(self, job: "MixMasterJob") -> "MixMasterJob":
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

    def dequeue(self) -> "MixMasterJob | None":
        with _lock:
            while _queue:
                jid = _queue.popleft()
                job = _jobs.get(jid)
                if job and job.state in ("queued", "retrying"):
                    job.state = "preparing"
                    job.queue_position = None
                    return job
            return None

    def update_state(
        self,
        job_id: str,
        state: "MixJobState",
        *,
        error: str | None = None,
    ) -> "MixMasterJob | None":
        with _lock:
            job = _jobs.get(job_id)
            if not job:
                return None
            job.state = state
            if error:
                job.observability.errors.append(error)
            if state in ("completed", "failed", "cancelled"):
                job.queue_position = None
            self._reindex()
            return job

    def retry(self, job_id: str) -> "MixMasterJob | None":
        with _lock:
            job = _jobs.get(job_id)
            if not job:
                return None
            if job.state not in ("failed", "cancelled", "completed"):
                return job
            job.retry_count += 1
            job.observability.retry_count = job.retry_count
            job.state = "retrying"
            if job_id not in _queue:
                _queue.append(job_id)
            _enqueued_at[job_id] = time.perf_counter()
            self._reindex()
            return job

    def cancel(self, job_id: str) -> "MixMasterJob | None":
        with _lock:
            job = _jobs.get(job_id)
            if not job:
                return None
            if job.state in ("completed", "cancelled"):
                return job
            job.state = "cancelled"
            try:
                _queue.remove(job_id)
            except ValueError:
                pass
            job.queue_position = None
            self._reindex()
            return job

    def get(self, job_id: str) -> "MixMasterJob | None":
        with _lock:
            return _jobs.get(job_id)

    def queue_wait_ms(self, job_id: str) -> float:
        with _lock:
            started = _enqueued_at.get(job_id)
            if started is None:
                return 0.0
            return max(0.0, (time.perf_counter() - started) * 1000.0)

    def status(self) -> dict[str, Any]:
        with _lock:
            by_state: dict[str, int] = {}
            for job in _jobs.values():
                by_state[job.state] = by_state.get(job.state, 0) + 1
            return {"queued": len(_queue), "tracked": len(_jobs), "by_state": by_state}

    def clear(self) -> None:
        with _lock:
            _queue.clear()
            _jobs.clear()
            _enqueued_at.clear()

    def _reindex(self) -> None:
        for idx, jid in enumerate(_queue, start=1):
            job = _jobs.get(jid)
            if job and job.state in ("queued", "retrying"):
                job.queue_position = idx


mix_queue = MixQueue()
