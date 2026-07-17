"""Clone queue — Audio Queue lifecycle with training/processing states."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict, deque
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.voice_cloning.models import CloneJobState, VoiceCloneJob

_lock = threading.Lock()
_queue: deque[str] = deque()
_jobs: OrderedDict[str, "VoiceCloneJob"] = OrderedDict()
_enqueued_at: dict[str, float] = {}
_MAX = 2000


class CloneQueue:
    def enqueue(self, job: "VoiceCloneJob") -> "VoiceCloneJob":
        with _lock:
            job.state = "queued"
            job.queue_position = len(_queue) + 1
            _jobs[job.clone_id] = job
            if job.clone_id not in _queue:
                _queue.append(job.clone_id)
            _enqueued_at[job.clone_id] = time.perf_counter()
            while len(_jobs) > _MAX:
                old_id, _ = _jobs.popitem(last=False)
                try:
                    _queue.remove(old_id)
                except ValueError:
                    pass
                _enqueued_at.pop(old_id, None)
            self._reindex()
            return job

    def dequeue(self) -> "VoiceCloneJob | None":
        with _lock:
            while _queue:
                cid = _queue.popleft()
                job = _jobs.get(cid)
                if job and job.state in ("queued", "retrying"):
                    job.state = "preparing"
                    job.queue_position = None
                    return job
            return None

    def update_state(
        self,
        clone_id: str,
        state: "CloneJobState",
        *,
        error: str | None = None,
    ) -> "VoiceCloneJob | None":
        with _lock:
            job = _jobs.get(clone_id)
            if not job:
                return None
            job.state = state
            if error:
                job.observability.errors.append(error)
            if state in ("completed", "failed", "cancelled"):
                job.queue_position = None
            self._reindex()
            return job

    def retry(self, clone_id: str) -> "VoiceCloneJob | None":
        with _lock:
            job = _jobs.get(clone_id)
            if not job:
                return None
            if job.state not in ("failed", "cancelled", "completed"):
                return job
            job.retry_count += 1
            job.observability.retry_count = job.retry_count
            job.state = "retrying"
            if clone_id not in _queue:
                _queue.append(clone_id)
            _enqueued_at[clone_id] = time.perf_counter()
            self._reindex()
            return job

    def cancel(self, clone_id: str) -> "VoiceCloneJob | None":
        with _lock:
            job = _jobs.get(clone_id)
            if not job:
                return None
            if job.state in ("completed", "cancelled"):
                return job
            job.state = "cancelled"
            try:
                _queue.remove(clone_id)
            except ValueError:
                pass
            job.queue_position = None
            self._reindex()
            return job

    def get(self, clone_id: str) -> "VoiceCloneJob | None":
        with _lock:
            return _jobs.get(clone_id)

    def queue_wait_ms(self, clone_id: str) -> float:
        with _lock:
            started = _enqueued_at.get(clone_id)
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
        for idx, cid in enumerate(_queue, start=1):
            job = _jobs.get(cid)
            if job and job.state in ("queued", "retrying"):
                job.queue_position = idx


clone_queue = CloneQueue()
