"""Multi-GPU job queue — thread-safe, no nested lock calls."""

from __future__ import annotations

import hashlib
import threading
from collections import OrderedDict, deque
from typing import Any
from uuid import uuid4

from app.services.multi_gpu.models import GpuSku, JobState, MultiGpuJob

_lock = threading.Lock()
_queue: deque[str] = deque()
_jobs: OrderedDict[str, MultiGpuJob] = OrderedDict()
_MAX = 2000
_rr = 0


def new_job_id(kind: str) -> str:
    seed = f"{kind}|{uuid4().hex[:8]}"
    return f"mgpu_{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:10]}"


def make_job(
    *,
    kind: str,
    priority: int = 100,
    required_vram_mb: int = 4096,
    preferred_skus: list[GpuSku] | None = None,
    require_rt: bool = False,
    estimated_ms: int = 5000,
    max_attempts: int = 3,
    parent_plan_id: str | None = None,
    scene_index: int | None = None,
) -> MultiGpuJob:
    return MultiGpuJob(
        job_id=new_job_id(kind),
        kind=kind,
        priority=priority,
        state="queued",
        required_vram_mb=required_vram_mb,
        preferred_skus=list(preferred_skus or ["A100", "L40S", "CLOUD"]),
        require_rt=require_rt,
        estimated_ms=estimated_ms,
        attempts=0,
        max_attempts=max_attempts,
        parent_plan_id=parent_plan_id,
        scene_index=scene_index,
    )


def enqueue(job: MultiGpuJob) -> MultiGpuJob:
    with _lock:
        job.state = "queued" if job.state != "retrying" else "retrying"
        _jobs[job.job_id] = job
        if job.job_id not in _queue:
            _queue.append(job.job_id)
        _resort_unlocked()
        while len(_jobs) > _MAX:
            old_id, _ = _jobs.popitem(last=False)
            try:
                _queue.remove(old_id)
            except ValueError:
                pass
        return job


def enqueue_many(jobs: list[MultiGpuJob]) -> list[MultiGpuJob]:
    return [enqueue(j) for j in jobs]


def _resort_unlocked() -> None:
    items: list[MultiGpuJob] = []
    for jid in list(_queue):
        job = _jobs.get(jid)
        if job and job.state in ("queued", "retrying"):
            items.append(job)
    items.sort(key=lambda j: (j.priority, j.scene_index if j.scene_index is not None else 999))
    _queue.clear()
    _queue.extend(j.job_id for j in items)


def dequeue_candidate() -> MultiGpuJob | None:
    """Pop next job without assigning a worker (distributor assigns)."""
    with _lock:
        if not _queue:
            return None
        n = len(_queue)
        for _ in range(n):
            jid = _queue.popleft()
            job = _jobs.get(jid)
            if job and job.state in ("queued", "retrying"):
                return job
        return None


def requeue(job: MultiGpuJob) -> None:
    with _lock:
        _jobs[job.job_id] = job
        if job.job_id not in _queue:
            _queue.append(job.job_id)
        _resort_unlocked()


def update_job(job: MultiGpuJob) -> MultiGpuJob:
    with _lock:
        _jobs[job.job_id] = job
        return job


def get_job(job_id: str) -> MultiGpuJob | None:
    with _lock:
        return _jobs.get(job_id)


def list_jobs(limit: int = 100) -> list[MultiGpuJob]:
    with _lock:
        return list(_jobs.values())[:limit]


def queue_depth() -> int:
    with _lock:
        return sum(
            1
            for jid in _queue
            if (_jobs.get(jid) and _jobs[jid].state in ("queued", "retrying"))
        )


def next_rr() -> int:
    global _rr
    with _lock:
        _rr = (_rr + 1) % 10_000
        return _rr


def queue_status() -> dict[str, Any]:
    with _lock:
        states: dict[str, int] = {}
        for job in _jobs.values():
            states[job.state] = states.get(job.state, 0) + 1
        head = []
        for jid in list(_queue)[:8]:
            job = _jobs.get(jid)
            if job:
                head.append(
                    {
                        "job_id": job.job_id,
                        "kind": job.kind,
                        "priority": job.priority,
                        "state": job.state,
                        "preferred_skus": job.preferred_skus,
                    }
                )
        return {
            "depth": len(_queue),
            "total_jobs": len(_jobs),
            "states": states,
            "head": head,
        }


def clear_queue() -> None:
    with _lock:
        _queue.clear()
        _jobs.clear()


def set_job_state(job_id: str, state: JobState, **fields: Any) -> MultiGpuJob | None:
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return None
        job.state = state
        for k, v in fields.items():
            if hasattr(job, k):
                setattr(job, k, v)
        return job
