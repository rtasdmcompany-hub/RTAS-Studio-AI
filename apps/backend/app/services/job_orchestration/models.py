"""Job orchestration domain models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

JobPriority = Literal["critical", "high", "normal", "low"]

JobState = Literal[
    "queued",
    "preparing",
    "running",
    "waiting",
    "completed",
    "failed",
    "cancelled",
    "retrying",
]

PRIORITY_ORDER: dict[JobPriority, int] = {
    "critical": 0,
    "high": 1,
    "normal": 2,
    "low": 3,
}

TERMINAL_STATES = frozenset({"completed", "failed", "cancelled"})


@dataclass
class JobMetrics:
    queue_time_ms: float = 0.0
    processing_time_ms: float = 0.0
    total_time_ms: float = 0.0
    provider_used: str | None = None
    retry_count: int = 0
    success: bool = False

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class OrchestratedJob:
    job_id: str
    prompt: str
    state: JobState
    priority: JobPriority = "normal"
    provider: str | None = None
    model: str | None = None
    request_type: str | None = None
    progress: float = 0.0
    depends_on: list[str] = field(default_factory=list)
    retry_count: int = 0
    max_retries: int = 3
    timeout_sec: float = 120.0
    error: str | None = None
    result: dict[str, Any] = field(default_factory=dict)
    metrics: JobMetrics = field(default_factory=JobMetrics)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: float = 0.0
    started_at: float | None = None
    finished_at: float | None = None
    enqueued_at: float | None = None
    version: int = 1

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "prompt": self.prompt,
            "state": self.state,
            "priority": self.priority,
            "provider": self.provider,
            "model": self.model,
            "request_type": self.request_type,
            "progress": self.progress,
            "depends_on": list(self.depends_on),
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "timeout_sec": self.timeout_sec,
            "error": self.error,
            "result": dict(self.result),
            "metrics": self.metrics.to_dict(),
            "metadata": dict(self.metadata),
            "created_at": self.created_at,
            "started_at": self.started_at,
            "finished_at": self.finished_at,
            "version": self.version,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "state": self.state,
            "priority": self.priority,
            "provider": self.provider,
            "model": self.model,
            "request_type": self.request_type,
            "progress": self.progress,
            "retry_count": self.retry_count,
            "error": self.error,
            "queue_time_ms": self.metrics.queue_time_ms,
            "processing_time_ms": self.metrics.processing_time_ms,
            "total_time_ms": self.metrics.total_time_ms,
            "success": self.metrics.success,
        }
