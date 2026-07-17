"""GPU worker registry and heartbeat management."""

from __future__ import annotations

import threading
import time
from typing import Any

from app.services.multi_gpu.catalog import CAPABILITIES, GPU_SKUS
from app.services.multi_gpu.models import GpuSku, GpuWorker, WorkerState

_lock = threading.Lock()
_WORKERS: dict[str, GpuWorker] = {}


def _default_fleet() -> list[GpuWorker]:
    """Seed a realistic multi-SKU fleet for planning / local orchestration."""
    seeds: list[tuple[str, GpuSku, str, str | None, list[str]]] = [
        ("w_h100_01", "H100", "us-east-1", "aws", ["cinema", "nvlink"]),
        ("w_h100_02", "H100", "us-east-1", "aws", ["cinema"]),
        ("w_a100_01", "A100", "us-central-1", "gcp", ["production", "nvlink"]),
        ("w_a100_02", "A100", "eu-west-1", "gcp", ["production"]),
        ("w_l40s_01", "L40S", "us-west-2", "azure", ["rt", "production"]),
        ("w_l40s_02", "L40S", "us-west-2", "azure", ["rt"]),
        ("w_rtx_01", "RTX", "local", None, ["edge", "rt", "draft"]),
        ("w_rtx_02", "RTX", "local", None, ["edge", "rt"]),
        ("w_cloud_01", "CLOUD", "auto", "runpod", ["burst", "cloud"]),
        ("w_cloud_02", "CLOUD", "auto", "lambda", ["burst", "cloud"]),
    ]
    workers: list[GpuWorker] = []
    for wid, sku, region, provider, labels in seeds:
        c = CAPABILITIES[sku]
        workers.append(
            GpuWorker(
                worker_id=wid,
                sku=sku,
                region=region,
                state="online",
                capacity_slots=2 if sku in ("H100", "A100") else 1,
                active_jobs=0,
                queued_jobs=0,
                vram_free_mb=c.vram_mb,
                vram_total_mb=c.vram_mb,
                load=0.0,
                success_rate=0.98 if sku != "CLOUD" else 0.94,
                last_heartbeat_sec=time.time(),
                labels=labels,
                cloud_provider=provider,
            )
        )
    return workers


def ensure_default_fleet() -> list[GpuWorker]:
    with _lock:
        if not _WORKERS:
            for w in _default_fleet():
                _WORKERS[w.worker_id] = w
        return list(_WORKERS.values())


def register_worker(worker: GpuWorker) -> GpuWorker:
    with _lock:
        worker.last_heartbeat_sec = time.time()
        _WORKERS[worker.worker_id] = worker
        return worker


def heartbeat(
    worker_id: str,
    *,
    state: WorkerState | None = None,
    active_jobs: int | None = None,
    queued_jobs: int | None = None,
    vram_free_mb: int | None = None,
    load: float | None = None,
) -> GpuWorker | None:
    with _lock:
        w = _WORKERS.get(worker_id)
        if not w:
            return None
        w.last_heartbeat_sec = time.time()
        if state is not None:
            w.state = state
        if active_jobs is not None:
            w.active_jobs = max(0, active_jobs)
        if queued_jobs is not None:
            w.queued_jobs = max(0, queued_jobs)
        if vram_free_mb is not None:
            w.vram_free_mb = max(0, vram_free_mb)
        if load is not None:
            w.load = max(0.0, min(1.0, load))
        # Auto busy/online from occupancy
        if w.state not in ("offline", "error", "draining"):
            if w.active_jobs >= w.capacity_slots:
                w.state = "busy"
            elif w.active_jobs == 0 and w.load < 0.15:
                w.state = "online"
        return w


def list_workers(*, online_only: bool = False) -> list[GpuWorker]:
    with _lock:
        workers = list(_WORKERS.values())
    if online_only:
        return [w for w in workers if w.state in ("online", "busy")]
    return workers


def get_worker(worker_id: str) -> GpuWorker | None:
    with _lock:
        return _WORKERS.get(worker_id)


def mark_assignment(worker_id: str, *, vram_mb: int) -> GpuWorker | None:
    with _lock:
        w = _WORKERS.get(worker_id)
        if not w:
            return None
        w.active_jobs += 1
        w.queued_jobs = max(0, w.queued_jobs - 1)
        w.vram_free_mb = max(0, w.vram_free_mb - vram_mb)
        w.load = min(1.0, w.active_jobs / max(1, w.capacity_slots))
        w.state = "busy" if w.active_jobs >= w.capacity_slots else "online"
        w.last_heartbeat_sec = time.time()
        return w


def mark_release(worker_id: str, *, vram_mb: int, success: bool = True) -> GpuWorker | None:
    with _lock:
        w = _WORKERS.get(worker_id)
        if not w:
            return None
        w.active_jobs = max(0, w.active_jobs - 1)
        w.vram_free_mb = min(w.vram_total_mb, w.vram_free_mb + vram_mb)
        w.load = min(1.0, w.active_jobs / max(1, w.capacity_slots))
        # EMA success rate
        w.success_rate = round(w.success_rate * 0.9 + (1.0 if success else 0.0) * 0.1, 4)
        if w.state not in ("offline", "error", "draining"):
            w.state = "online" if w.active_jobs < w.capacity_slots else "busy"
        w.last_heartbeat_sec = time.time()
        return w


def bump_queue(worker_id: str, delta: int = 1) -> None:
    with _lock:
        w = _WORKERS.get(worker_id)
        if w:
            w.queued_jobs = max(0, w.queued_jobs + delta)


def clear_workers() -> None:
    with _lock:
        _WORKERS.clear()


def fleet_by_sku() -> dict[str, int]:
    with _lock:
        counts: dict[str, int] = {s: 0 for s in GPU_SKUS}
        for w in _WORKERS.values():
            if w.state in ("online", "busy"):
                counts[w.sku] = counts.get(w.sku, 0) + 1
        return counts


def worker_snapshot() -> list[dict[str, Any]]:
    return [w.to_dict() for w in list_workers()]
