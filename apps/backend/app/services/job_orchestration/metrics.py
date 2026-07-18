"""Aggregate performance metrics for the job orchestrator."""

from __future__ import annotations

from typing import Any

from app.services.job_orchestration import store
from app.services.job_orchestration.models import TERMINAL_STATES
from app.services.job_orchestration.queue_manager import queue_manager


def compute_metrics() -> dict[str, Any]:
    jobs = store.all_jobs()
    completed = [j for j in jobs if j.state == "completed"]
    failed = [j for j in jobs if j.state == "failed"]
    terminal = [j for j in jobs if j.state in TERMINAL_STATES]
    running = [j for j in jobs if j.state in ("running", "preparing", "waiting", "retrying")]

    queue_times = [j.metrics.queue_time_ms for j in terminal if j.metrics.queue_time_ms]
    proc_times = [j.metrics.processing_time_ms for j in completed if j.metrics.processing_time_ms]
    total_times = [j.metrics.total_time_ms for j in terminal if j.metrics.total_time_ms]
    retries = sum(j.retry_count for j in jobs)
    success_rate = round(100.0 * len(completed) / len(terminal), 2) if terminal else 100.0

    providers: dict[str, int] = {}
    for j in completed:
        p = j.provider or "unknown"
        providers[p] = providers.get(p, 0) + 1

    return {
        "total_jobs": len(jobs),
        "completed": len(completed),
        "failed": len(failed),
        "running": len(running),
        "queued": queue_manager.queued_count(),
        "success_rate": success_rate,
        "avg_queue_time_ms": round(sum(queue_times) / len(queue_times), 3) if queue_times else 0.0,
        "avg_processing_time_ms": round(sum(proc_times) / len(proc_times), 3) if proc_times else 0.0,
        "avg_total_time_ms": round(sum(total_times) / len(total_times), 3) if total_times else 0.0,
        "retry_count_total": retries,
        "providers_used": providers,
        "queue": queue_manager.statistics(),
    }
