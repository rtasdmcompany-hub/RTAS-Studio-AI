"""Queue balancing and load balancing across GPU workers."""

from __future__ import annotations

from typing import Any

from app.services.multi_gpu.catalog import caps
from app.services.multi_gpu.models import BalanceStrategy, GpuWorker, MultiGpuJob


def worker_score(
    worker: GpuWorker,
    job: MultiGpuJob,
    *,
    strategy: BalanceStrategy,
    rr_index: int = 0,
) -> float:
    """Lower score = better candidate."""
    if worker.state in ("offline", "error", "draining"):
        return 1e9
    if worker.vram_free_mb < job.required_vram_mb:
        return 1e8
    if worker.active_jobs >= worker.capacity_slots and strategy != "capability_match":
        # Still allow queueing but penalize heavily
        pass

    c = caps(worker.sku)
    sku_rank = 0
    if job.preferred_skus:
        try:
            sku_rank = job.preferred_skus.index(worker.sku)
        except ValueError:
            sku_rank = len(job.preferred_skus) + 2
    if job.require_rt and not c.supports_rt:
        return 1e7

    load_term = worker.load * 100
    queue_term = worker.queued_jobs * 25 + worker.active_jobs * 40
    vram_pressure = 1.0 - (worker.vram_free_mb / max(1, worker.vram_total_mb))
    reliability = (1.0 - worker.success_rate) * 50

    if strategy == "least_load":
        return load_term + queue_term * 0.3 + sku_rank * 5 + reliability
    if strategy == "least_queue":
        return queue_term + load_term * 0.3 + sku_rank * 5 + reliability
    if strategy == "round_robin":
        return float((rr_index % 1000)) + sku_rank * 0.01 + load_term * 0.1
    # capability_match
    return (
        sku_rank * 20
        + load_term * 0.5
        + queue_term * 0.4
        + vram_pressure * 15
        + reliability
    )


def pick_worker(
    workers: list[GpuWorker],
    job: MultiGpuJob,
    *,
    strategy: BalanceStrategy,
    rr_counter: int = 0,
) -> GpuWorker | None:
    eligible = [
        w
        for w in workers
        if w.state in ("online", "busy")
        and w.vram_free_mb >= min(job.required_vram_mb, int(w.vram_total_mb * 0.5))
    ]
    if not eligible:
        eligible = [w for w in workers if w.state in ("online", "busy")]
    if not eligible:
        return None

    ranked = sorted(
        eligible,
        key=lambda w: worker_score(w, job, strategy=strategy, rr_index=rr_counter),
    )
    return ranked[0]


def queue_balance_report(workers: list[GpuWorker]) -> dict[str, Any]:
    by_sku: dict[str, dict[str, int]] = {}
    total_q = 0
    for w in workers:
        bucket = by_sku.setdefault(w.sku, {"workers": 0, "queued": 0, "active": 0})
        bucket["workers"] += 1
        bucket["queued"] += w.queued_jobs
        bucket["active"] += w.active_jobs
        total_q += w.queued_jobs
    # Imbalance: max queue vs mean
    queues = [w.queued_jobs + w.active_jobs for w in workers if w.state in ("online", "busy")]
    imbalance = 0.0
    if queues:
        mean = sum(queues) / len(queues)
        imbalance = max(queues) - mean
    return {
        "total_queued": total_q,
        "by_sku": by_sku,
        "imbalance": round(imbalance, 3),
        "balanced": imbalance <= 1.5,
        "recommendation": (
            "redistribute burst jobs to CLOUD/L40S"
            if imbalance > 2
            else "queues within tolerance"
        ),
    }


def load_balance_report(workers: list[GpuWorker]) -> dict[str, Any]:
    online = [w for w in workers if w.state in ("online", "busy")]
    if not online:
        return {"avg_load": 0.0, "max_load": 0.0, "hot_workers": [], "balanced": True}
    loads = [w.load for w in online]
    avg = sum(loads) / len(loads)
    hot = [w.worker_id for w in online if w.load >= avg + 0.35 and w.load >= 0.7]
    return {
        "avg_load": round(avg, 3),
        "max_load": round(max(loads), 3),
        "min_load": round(min(loads), 3),
        "hot_workers": hot,
        "balanced": len(hot) == 0,
        "strategy_hint": "least_load" if hot else "capability_match",
    }
