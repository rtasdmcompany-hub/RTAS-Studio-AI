"""Multi AI Video Generation Engine models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

QueueState = Literal["queued", "running", "completed", "failed", "cancelled"]


@dataclass
class QueueJob:
    job_id: str
    provider: str
    state: QueueState
    progress_percent: int = 0
    attempts: int = 0
    error: str | None = None
    result_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GenerationFlowResult:
    success: bool
    provider: str
    attempted_providers: list[str]
    queue_job: QueueJob
    remote_url: str | None = None
    local_mp4_path: str | None = None
    external_job_id: str | None = None
    error: str | None = None
    cost_estimate: dict[str, Any] = field(default_factory=dict)
    eta: dict[str, Any] = field(default_factory=dict)
    failover_log: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "success": self.success,
            "provider": self.provider,
            "attempted_providers": self.attempted_providers,
            "queue_job": self.queue_job.to_dict(),
            "remote_url": self.remote_url,
            "local_mp4_path": self.local_mp4_path,
            "external_job_id": self.external_job_id,
            "error": self.error,
            "cost_estimate": self.cost_estimate,
            "eta": self.eta,
            "failover_log": self.failover_log,
            "metadata": self.metadata,
        }
