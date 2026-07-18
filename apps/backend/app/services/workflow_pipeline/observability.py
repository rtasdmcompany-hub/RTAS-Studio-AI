"""Observability metrics for workflows and pipelines."""

from __future__ import annotations

from typing import Any

from app.services.workflow_pipeline import store
from app.services.workflow_pipeline.models import TERMINAL_WORKFLOW


def metrics() -> dict[str, Any]:
    jobs = store.all_jobs()
    total = len(jobs)
    completed = sum(1 for j in jobs if j.status == "completed")
    failed = sum(1 for j in jobs if j.status == "failed")
    cancelled = sum(1 for j in jobs if j.status == "cancelled")
    running = sum(1 for j in jobs if j.status in ("running", "queued", "waiting", "recovering"))
    terminal = [j for j in jobs if j.status in TERMINAL_WORKFLOW]
    success_rate = (completed / len(terminal) * 100.0) if terminal else 100.0
    runtimes = [j.processing_time_ms for j in jobs if j.processing_time_ms > 0]
    avg_runtime = sum(runtimes) / len(runtimes) if runtimes else 0.0

    failed_steps: dict[str, int] = {}
    retries = 0
    stage_completed = 0
    stage_failed = 0
    for j in jobs:
        retries += j.retry_count
        for s in j.stages:
            retries += s.retry_count
            if s.status == "completed":
                stage_completed += 1
            elif s.status == "failed":
                stage_failed += 1
                failed_steps[s.name] = failed_steps.get(s.name, 0) + 1

    stage_total = stage_completed + stage_failed
    pipeline_success = (
        (stage_completed / stage_total * 100.0) if stage_total else 100.0
    )
    # Queue efficiency: completed vs (completed+failed+cancelled) with running penalty
    denom = completed + failed + cancelled + max(0, running)
    queue_eff = (completed / denom * 100.0) if denom else 100.0

    return {
        "workflow_success_rate": round(success_rate, 2),
        "pipeline_success_rate": round(pipeline_success, 2),
        "average_runtime_ms": round(avg_runtime, 2),
        "failed_steps": failed_steps,
        "retry_statistics": {
            "total_retries": retries,
            "workflows_with_retries": sum(1 for j in jobs if j.retry_count > 0),
        },
        "queue_efficiency": round(queue_eff, 2),
        "counts": {
            "total": total,
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "running": running,
        },
    }


def pipeline_status_snapshot() -> dict[str, Any]:
    jobs = store.all_jobs()
    active = [j for j in jobs if j.status in ("running", "queued", "waiting", "recovering", "paused")]
    return {
        "active_pipelines": len(active),
        "pipelines": [
            {
                "workflow_id": j.workflow_id,
                "status": j.status,
                "active_stage": j.active_stage,
                "completed_stages": [s.name for s in j.stages if s.status == "completed"],
                "failed_stages": [s.name for s in j.stages if s.status == "failed"],
                "retry_count": j.retry_count,
                "processing_time_ms": j.processing_time_ms,
                "logs": j.logs[-20:],
            }
            for j in active[:50]
        ],
        "observability": metrics(),
    }
