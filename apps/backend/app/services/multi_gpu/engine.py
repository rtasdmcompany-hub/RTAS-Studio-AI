"""
Multi GPU Engine.

H100 / A100 / L40S / RTX / Cloud GPU fleet with worker distribution,
queue balancing, load balancing, retry, and monitoring.
"""

from __future__ import annotations

import hashlib
import logging
from typing import Any
from uuid import uuid4

from app.services.multi_gpu.balancer import load_balance_report, queue_balance_report
from app.services.multi_gpu.bridge import (
    jobs_from_scene_render,
    resolve_strategy,
    scene_render_integration,
)
from app.services.multi_gpu.catalog import CAPABILITIES, GPU_SKUS
from app.services.multi_gpu.distributor import (
    distribute_pending,
    distribution_summary,
)
from app.services.multi_gpu.models import BalanceStrategy, MultiGpuPlan
from app.services.multi_gpu.monitor import build_monitor_snapshot
from app.services.multi_gpu.queue import enqueue_many, list_jobs, make_job, queue_status
from app.services.multi_gpu.retry import default_retry_policy, retry_plan_summary
from app.services.multi_gpu.store import get_plan as store_get
from app.services.multi_gpu.store import put_plan
from app.services.multi_gpu.workers import ensure_default_fleet, list_workers

logger = logging.getLogger(__name__)


def _plan_id(seed: str) -> str:
    raw = f"{seed}|{uuid4().hex[:8]}"
    return f"multigpu_{hashlib.sha1(raw.encode('utf-8')).hexdigest()[:10]}"


def build_multi_gpu_plan(
    *,
    scene_render: dict[str, Any] | None = None,
    jobs: list[dict[str, Any]] | None = None,
    strategy: str | None = None,
    quality: str = "production",
    seed_fleet: bool = True,
    distribute: bool = True,
    parent_generation_id: str | None = None,
    prompt: str | None = None,
) -> MultiGpuPlan:
    bal_strategy: BalanceStrategy = resolve_strategy(strategy)
    if seed_fleet:
        ensure_default_fleet()
    workers = list_workers()

    mg_jobs = []
    if scene_render:
        mg_jobs.extend(jobs_from_scene_render(scene_render, quality=quality))
    for raw in jobs or []:
        if not isinstance(raw, dict):
            continue
        mg_jobs.append(
            make_job(
                kind=str(raw.get("kind") or "generic"),
                priority=int(raw.get("priority") or 100),
                required_vram_mb=int(raw.get("required_vram_mb") or 4096),
                preferred_skus=raw.get("preferred_skus"),
                require_rt=bool(raw.get("require_rt")),
                estimated_ms=int(raw.get("estimated_ms") or 5000),
                parent_plan_id=raw.get("parent_plan_id"),
                scene_index=raw.get("scene_index"),
            )
        )

    if not mg_jobs:
        # Default: one production job across preferred fleet
        from app.services.multi_gpu.catalog import preferred_skus

        mg_jobs = [
            make_job(
                kind="generic",
                priority=50,
                required_vram_mb=4096,
                preferred_skus=preferred_skus(quality=quality),
                require_rt=False,
                estimated_ms=6000,
            )
        ]

    enqueue_many(mg_jobs)

    assignments: list[dict[str, Any]] = []
    if distribute:
        assignments = distribute_pending(strategy=bal_strategy, max_jobs=len(mg_jobs) + 4)

    # Refresh workers after assignment side-effects
    workers = list_workers()
    tracked = list_jobs(limit=500)
    # Prefer jobs from this plan batch
    batch_ids = {j.job_id for j in mg_jobs}
    plan_jobs = [j for j in tracked if j.job_id in batch_ids] or mg_jobs

    retry = default_retry_policy()
    monitoring = build_monitor_snapshot(workers, plan_jobs)
    qbal = queue_balance_report(workers)
    lbal = load_balance_report(workers)
    dist = distribution_summary(assignments, workers)

    directives = [
        "MULTI GPU ENGINE — distribute work across H100/A100/L40S/RTX/Cloud.",
        f"Balance strategy: {bal_strategy}.",
        "Retry transient/OOM/timeout with SKU escalation; monitor heartbeats.",
        f"Fleet SKUs online: {sorted({w.sku for w in workers if w.state in ('online', 'busy')})}.",
        f"Queue balanced={qbal.get('balanced')} load_balanced={lbal.get('balanced')}.",
    ]
    for a in assignments[:8]:
        if a.get("assigned"):
            directives.append(
                f"Assign {a['job_id']} → {a['worker_id']} ({a['sku']})"
            )

    plan = MultiGpuPlan(
        job_id=_plan_id(prompt or parent_generation_id or "fleet"),
        strategy=bal_strategy,
        workers=workers,
        jobs=plan_jobs,
        assignments=assignments,
        retry_policy=retry,
        monitoring=monitoring,
        queue_balance=qbal,
        load_balance=lbal,
        distribution=dist,
        scene_render_integration=scene_render_integration(scene_render, assignments),
        provider_directives=directives,
    )
    if parent_generation_id:
        plan.distribution["parent_generation_id"] = parent_generation_id
    plan.distribution["supported_skus"] = list(GPU_SKUS)
    plan.distribution["capabilities"] = {k: v.to_dict() for k, v in CAPABILITIES.items()}
    plan.distribution["retry"] = retry_plan_summary(retry)
    plan.distribution["queue_status"] = queue_status()

    put_plan(plan)
    logger.info(
        "multi_gpu_ready plan=%s workers=%s jobs=%s assigned=%s strategy=%s",
        plan.job_id,
        len(workers),
        len(plan_jobs),
        dist.get("assigned_count"),
        bal_strategy,
    )
    return plan


def build_multi_gpu_dict(**kwargs: Any) -> dict[str, Any]:
    plan = build_multi_gpu_plan(**kwargs)
    return {"plan": plan.to_dict(), "summary": plan.summary()}


def get_plan(job_id: str) -> MultiGpuPlan | None:
    return store_get(job_id)
