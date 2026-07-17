"""GPU render queue — priority scheduling for scene passes."""

from __future__ import annotations

import hashlib
import threading
from collections import OrderedDict, deque
from typing import Any
from uuid import uuid4

from app.services.scene_render.models import GpuJobState, GpuRenderJob, RenderQuality

_lock = threading.Lock()
_queue: deque[str] = deque()
_jobs: OrderedDict[str, GpuRenderJob] = OrderedDict()
_MAX = 500

_EST_MS = {"draft": 800, "preview": 2500, "production": 8000, "cinema": 20000}
_EST_VRAM = {"draft": 1024, "preview": 2048, "production": 4096, "cinema": 6144}


def _job_id(scene_index: int) -> str:
    seed = f"{scene_index}|{uuid4().hex[:8]}"
    return f"gpu_{hashlib.sha1(seed.encode('utf-8')).hexdigest()[:10]}"


def estimate_job(
    scene_index: int,
    *,
    quality: RenderQuality,
    priority: int = 100,
    particle_heavy: bool = False,
    dependencies: list[str] | None = None,
) -> GpuRenderJob:
    ms = _EST_MS[quality]
    vram = _EST_VRAM[quality]
    if particle_heavy:
        ms = int(ms * 1.35)
        vram = int(vram * 1.2)
    return GpuRenderJob(
        job_id=_job_id(scene_index),
        scene_index=scene_index,
        priority=priority,
        state="queued",
        quality=quality,
        estimated_vram_mb=vram,
        estimated_ms=ms,
        dependencies=list(dependencies or []),
        notes="GPU scene render pass",
    )


def enqueue(job: GpuRenderJob) -> GpuRenderJob:
    with _lock:
        job.state = "queued"
        _jobs[job.job_id] = job
        # Higher priority first: store as sorted insert via re-sort of deque
        _queue.append(job.job_id)
        _resort_locked()
        while len(_jobs) > _MAX:
            old_id, _ = _jobs.popitem(last=False)
            try:
                _queue.remove(old_id)
            except ValueError:
                pass
        return job


def enqueue_many(jobs: list[GpuRenderJob]) -> list[GpuRenderJob]:
    return [enqueue(j) for j in jobs]


def _resort_locked() -> None:
    items = []
    for jid in list(_queue):
        job = _jobs.get(jid)
        if job and job.state == "queued":
            items.append(job)
    items.sort(key=lambda j: (j.priority, j.scene_index))
    _queue.clear()
    _queue.extend(j.job_id for j in items)


def dequeue() -> GpuRenderJob | None:
    with _lock:
        if not _queue:
            return None
        # Single pass — avoid infinite re-queue loops on unmet deps
        n = len(_queue)
        for _ in range(n):
            jid = _queue.popleft()
            job = _jobs.get(jid)
            if not job or job.state != "queued":
                continue
            blocked = any(
                (_jobs.get(d) is not None and _jobs[d].state not in ("completed",))
                for d in job.dependencies
            )
            if blocked:
                _queue.append(jid)
                continue
            job.state = "running"
            return job
        return None


def complete(job_id: str, *, failed: bool = False, error: str | None = None) -> GpuRenderJob | None:
    with _lock:
        job = _jobs.get(job_id)
        if not job:
            return None
        job.state = "failed" if failed else "completed"
        if error:
            job.notes = f"{job.notes}; error={error}"[:240]
        return job


def get_job(job_id: str) -> GpuRenderJob | None:
    with _lock:
        return _jobs.get(job_id)


def peek(limit: int = 32) -> list[GpuRenderJob]:
    with _lock:
        return _peek_unlocked(limit)


def _peek_unlocked(limit: int = 32) -> list[GpuRenderJob]:
    out = []
    for jid in list(_queue)[:limit]:
        job = _jobs.get(jid)
        if job:
            out.append(job)
    return out


def queue_status() -> dict[str, Any]:
    with _lock:
        states: dict[str, int] = {}
        for job in _jobs.values():
            states[job.state] = states.get(job.state, 0) + 1
        return {
            "queued": len(_queue),
            "total_jobs": len(_jobs),
            "states": states,
            "head": [j.to_dict() for j in _peek_unlocked(5)],
        }


def clear_queue() -> None:
    with _lock:
        _queue.clear()
        _jobs.clear()


def prioritize_scene_order(scene_indices: list[int]) -> list[tuple[int, int]]:
    """Return (scene_index, priority) — earlier narrative scenes render first."""
    out = []
    for i, idx in enumerate(scene_indices):
        # Lower number = higher priority
        out.append((idx, 10 + i * 10))
    return out
