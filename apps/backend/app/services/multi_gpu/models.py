"""Multi GPU Engine — dataclasses."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

GpuSku = Literal["H100", "A100", "L40S", "RTX", "CLOUD"]
WorkerState = Literal["online", "busy", "draining", "offline", "error"]
JobState = Literal["queued", "assigned", "running", "completed", "failed", "retrying", "cancelled"]
BalanceStrategy = Literal["least_load", "least_queue", "round_robin", "capability_match"]


@dataclass
class GpuCapabilities:
    sku: GpuSku
    vram_mb: int
    fp16_tflops: float
    supports_rt: bool
    supports_nvlink: bool
    cloud: bool
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class GpuWorker:
    worker_id: str
    sku: GpuSku
    region: str
    state: WorkerState
    capacity_slots: int
    active_jobs: int
    queued_jobs: int
    vram_free_mb: int
    vram_total_mb: int
    load: float  # 0–1
    success_rate: float
    last_heartbeat_sec: float
    labels: list[str] = field(default_factory=list)
    cloud_provider: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MultiGpuJob:
    job_id: str
    kind: str  # scene_render / text_to_video / physics / generic
    priority: int
    state: JobState
    required_vram_mb: int
    preferred_skus: list[GpuSku]
    require_rt: bool
    estimated_ms: int
    attempts: int
    max_attempts: int
    assigned_worker_id: str | None = None
    assigned_sku: GpuSku | None = None
    parent_plan_id: str | None = None
    scene_index: int | None = None
    error: str | None = None
    history: list[dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RetryPolicy:
    max_attempts: int = 3
    backoff_ms: list[int] = field(default_factory=lambda: [500, 2000, 5000])
    retry_on: list[str] = field(
        default_factory=lambda: ["timeout", "oom", "worker_lost", "transient"]
    )
    escalate_sku: bool = True

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MonitorSnapshot:
    ts_sec: float
    workers_online: int
    workers_busy: int
    queue_depth: int
    running_jobs: int
    failed_jobs: int
    retrying_jobs: int
    avg_load: float
    sku_utilization: dict[str, float]
    alerts: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class MultiGpuPlan:
    job_id: str
    strategy: BalanceStrategy
    workers: list[GpuWorker]
    jobs: list[MultiGpuJob]
    assignments: list[dict[str, Any]]
    retry_policy: RetryPolicy
    monitoring: MonitorSnapshot
    queue_balance: dict[str, Any]
    load_balance: dict[str, Any]
    distribution: dict[str, Any]
    scene_render_integration: dict[str, Any] = field(default_factory=dict)
    provider_directives: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "strategy": self.strategy,
            "workers": [w.to_dict() for w in self.workers],
            "jobs": [j.to_dict() for j in self.jobs],
            "assignments": self.assignments,
            "retry_policy": self.retry_policy.to_dict(),
            "monitoring": self.monitoring.to_dict(),
            "queue_balance": self.queue_balance,
            "load_balance": self.load_balance,
            "distribution": self.distribution,
            "scene_render_integration": self.scene_render_integration,
            "provider_directives": self.provider_directives,
        }

    def summary(self) -> dict[str, Any]:
        return {
            "job_id": self.job_id,
            "strategy": self.strategy,
            "workers": len(self.workers),
            "online": sum(1 for w in self.workers if w.state in ("online", "busy")),
            "jobs": len(self.jobs),
            "assigned": sum(1 for j in self.jobs if j.assigned_worker_id),
            "queue_depth": self.monitoring.queue_depth,
            "avg_load": self.monitoring.avg_load,
            "skus": sorted({w.sku for w in self.workers}),
            "alerts": self.monitoring.alerts[:8],
            "directives": self.provider_directives[:10],
        }
