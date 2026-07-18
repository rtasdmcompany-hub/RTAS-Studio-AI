"""Priority job queue manager."""

from __future__ import annotations

import threading
import time
from collections import deque
from typing import TYPE_CHECKING, Any

from app.services.job_orchestration.models import PRIORITY_ORDER, JobPriority

if TYPE_CHECKING:
    from app.services.job_orchestration.models import OrchestratedJob

_lock = threading.Lock()


class JobQueueManager:
    def __init__(self) -> None:
        self._queues: dict[JobPriority, deque[str]] = {
            "critical": deque(),
            "high": deque(),
            "normal": deque(),
            "low": deque(),
        }
        self._jobs: dict[str, "OrchestratedJob"] = {}

    def enqueue(self, job: "OrchestratedJob") -> "OrchestratedJob":
        with _lock:
            job.state = "queued"
            job.enqueued_at = time.perf_counter()
            self._jobs[job.job_id] = job
            q = self._queues[job.priority]
            if job.job_id not in q:
                q.append(job.job_id)
            return job

    def dequeue(self) -> "OrchestratedJob | None":
        with _lock:
            for priority in sorted(self._queues.keys(), key=lambda p: PRIORITY_ORDER[p]):
                q = self._queues[priority]
                while q:
                    jid = q.popleft()
                    job = self._jobs.get(jid)
                    if not job:
                        continue
                    if job.state in ("queued", "retrying"):
                        return job
            return None

    def remove(self, job_id: str) -> None:
        with _lock:
            for q in self._queues.values():
                try:
                    q.remove(job_id)
                except ValueError:
                    pass

    def peek_depth(self) -> dict[str, int]:
        with _lock:
            return {p: len(q) for p, q in self._queues.items()}

    def queued_count(self) -> int:
        with _lock:
            return sum(len(q) for q in self._queues.values())

    def statistics(self) -> dict[str, Any]:
        with _lock:
            depths = {p: len(q) for p, q in self._queues.items()}
            return {
                "queued_total": sum(depths.values()),
                "by_priority": depths,
                "jobs_tracked": len(self._jobs),
            }

    def clear(self) -> None:
        with _lock:
            for q in self._queues.values():
                q.clear()
            self._jobs.clear()


queue_manager = JobQueueManager()
