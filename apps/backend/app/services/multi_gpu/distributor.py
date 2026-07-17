"""Worker distribution — assign Multi GPU jobs to fleet workers."""

from __future__ import annotations

from typing import Any

from app.services.multi_gpu.balancer import pick_worker
from app.services.multi_gpu.models import BalanceStrategy, GpuWorker, MultiGpuJob
from app.services.multi_gpu.queue import (
    dequeue_candidate,
    get_job,
    next_rr,
    requeue,
    update_job,
)
from app.services.multi_gpu.workers import (
    bump_queue,
    list_workers,
    mark_assignment,
    mark_release,
)


def distribute_job(
    job: MultiGpuJob,
    workers: list[GpuWorker],
    *,
    strategy: BalanceStrategy,
) -> dict[str, Any]:
    rr = next_rr()
    worker = pick_worker(workers, job, strategy=strategy, rr_counter=rr)
    if not worker:
        job.state = "queued"
        job.history.append({"event": "no_worker", "strategy": strategy})
        requeue(job)
        return {
            "job_id": job.job_id,
            "assigned": False,
            "reason": "no_eligible_worker",
        }

    job.state = "assigned"
    job.assigned_worker_id = worker.worker_id
    job.assigned_sku = worker.sku
    job.history.append(
        {
            "event": "assigned",
            "worker_id": worker.worker_id,
            "sku": worker.sku,
            "strategy": strategy,
        }
    )
    update_job(job)
    bump_queue(worker.worker_id, 1)
    mark_assignment(worker.worker_id, vram_mb=job.required_vram_mb)

    return {
        "job_id": job.job_id,
        "assigned": True,
        "worker_id": worker.worker_id,
        "sku": worker.sku,
        "region": worker.region,
        "strategy": strategy,
        "estimated_ms": job.estimated_ms,
    }


def distribute_pending(
    *,
    strategy: BalanceStrategy | str = "capability_match",
    max_jobs: int = 32,
) -> list[dict[str, Any]]:
    from app.services.multi_gpu.bridge import resolve_strategy

    bal: BalanceStrategy = (
        strategy
        if strategy
        in ("least_load", "least_queue", "round_robin", "capability_match")
        else resolve_strategy(str(strategy))
    )
    assignments: list[dict[str, Any]] = []
    for _ in range(max_jobs):
        job = dequeue_candidate()
        if not job:
            break
        # Refresh workers each assign for load awareness
        fleet = list_workers(online_only=True)
        result = distribute_job(job, fleet, strategy=bal)
        assignments.append(result)
        if not result.get("assigned"):
            break
    return assignments


def distribution_summary(
    assignments: list[dict[str, Any]],
    workers: list[GpuWorker],
) -> dict[str, Any]:
    by_worker: dict[str, int] = {}
    by_sku: dict[str, int] = {}
    for a in assignments:
        if not a.get("assigned"):
            continue
        wid = str(a.get("worker_id"))
        sku = str(a.get("sku"))
        by_worker[wid] = by_worker.get(wid, 0) + 1
        by_sku[sku] = by_sku.get(sku, 0) + 1
    return {
        "assigned_count": sum(1 for a in assignments if a.get("assigned")),
        "unassigned_count": sum(1 for a in assignments if not a.get("assigned")),
        "by_worker": by_worker,
        "by_sku": by_sku,
        "fleet_online": sum(1 for w in workers if w.state in ("online", "busy")),
    }


def complete_job(
    job_id: str,
    *,
    success: bool = True,
    error: str | None = None,
) -> MultiGpuJob | None:
    job = get_job(job_id)
    if not job:
        return None
    wid = job.assigned_worker_id
    if wid:
        mark_release(wid, vram_mb=job.required_vram_mb, success=success)
    if success:
        job.state = "completed"
        job.error = None
        job.history.append({"event": "completed"})
    else:
        from app.services.multi_gpu.retry import apply_retry, default_retry_policy

        job = apply_retry(job, default_retry_policy(), error)
        if job.state == "retrying":
            requeue(job)
    update_job(job)
    return job
