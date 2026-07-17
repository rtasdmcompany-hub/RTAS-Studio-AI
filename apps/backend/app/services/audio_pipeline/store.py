"""Pipeline job store and metrics aggregation."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from app.services.audio_pipeline.models import PipelineJob

_lock = threading.Lock()
_jobs: OrderedDict[str, "PipelineJob"] = OrderedDict()
_history: list[dict[str, Any]] = []
_metrics: dict[str, Any] = {
    "jobs_total": 0,
    "jobs_completed": 0,
    "jobs_failed": 0,
    "retries_total": 0,
    "exports_total": 0,
    "quality_scores": [],
    "processing_times_ms": [],
}
_MAX = 2000
_HISTORY_MAX = 5000


def save(job: "PipelineJob") -> "PipelineJob":
    with _lock:
        _jobs[job.job_id] = job
        while len(_jobs) > _MAX:
            _jobs.popitem(last=False)
        return job


def get(job_id: str) -> "PipelineJob | None":
    with _lock:
        return _jobs.get(job_id)


def append_history(entry: dict[str, Any]) -> None:
    with _lock:
        _history.append({**entry, "ts": entry.get("ts") or time.time()})
        while len(_history) > _HISTORY_MAX:
            _history.pop(0)


def record_job_metrics(job: "PipelineJob") -> None:
    with _lock:
        _metrics["jobs_total"] += 1
        if job.state == "completed":
            _metrics["jobs_completed"] += 1
        if job.state == "failed":
            _metrics["jobs_failed"] += 1
        _metrics["retries_total"] += job.retry_count
        if job.export_job_id:
            _metrics["exports_total"] += 1
        _metrics["quality_scores"].append(job.quality.overall_score)
        _metrics["processing_times_ms"].append(job.performance.total_processing_time_ms)
        _metrics["quality_scores"] = _metrics["quality_scores"][-500:]
        _metrics["processing_times_ms"] = _metrics["processing_times_ms"][-500:]


def metrics_snapshot() -> dict[str, Any]:
    with _lock:
        scores = list(_metrics["quality_scores"])
        times = list(_metrics["processing_times_ms"])
        total = max(1, _metrics["jobs_total"])
        return {
            "jobs_total": _metrics["jobs_total"],
            "jobs_completed": _metrics["jobs_completed"],
            "jobs_failed": _metrics["jobs_failed"],
            "retries_total": _metrics["retries_total"],
            "exports_total": _metrics["exports_total"],
            "success_rate": round(_metrics["jobs_completed"] / total, 4),
            "failure_rate": round(_metrics["jobs_failed"] / total, 4),
            "retry_rate": round(_metrics["retries_total"] / total, 4),
            "avg_quality_score": round(sum(scores) / len(scores), 2) if scores else 0.0,
            "avg_processing_time_ms": round(sum(times) / len(times), 2) if times else 0.0,
            "tracked_jobs": len(_jobs),
            "system_health": "healthy"
            if _metrics["jobs_failed"] == 0 or (_metrics["jobs_completed"] / total) >= 0.9
            else "degraded",
        }


def history(limit: int = 50) -> list[dict[str, Any]]:
    with _lock:
        items = list(_history)
    return list(reversed(items[-max(1, min(500, limit)) :]))


def clear() -> None:
    with _lock:
        _jobs.clear()
        _history.clear()
        _metrics["jobs_total"] = 0
        _metrics["jobs_completed"] = 0
        _metrics["jobs_failed"] = 0
        _metrics["retries_total"] = 0
        _metrics["exports_total"] = 0
        _metrics["quality_scores"] = []
        _metrics["processing_times_ms"] = []
