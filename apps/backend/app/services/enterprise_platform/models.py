"""Platform integration models."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


@dataclass
class PipelineStepResult:
    step: str
    ok: bool
    detail: str = ""
    latency_ms: float = 0.0
    data: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class QualityScore:
    overall: float
    routing_accuracy: float
    provider_failover: float
    retry_logic: float
    queue_performance: float
    memory_retrieval: float
    workflow_execution: float
    security_validation: float
    audit_logs: float
    monitoring: float
    recovery: float
    passed: bool
    breakdown: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class StressResult:
    job_count: int
    completed: int
    failed: int
    elapsed_sec: float
    jobs_per_sec: float
    avg_latency_ms: float
    failure_rate: float
    queue_time_ms: float
    recovery_time_ms: float
    provider_switches: int
    cpu_estimate: float
    memory_estimate: float

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PlatformRelease:
    release_id: str
    platform: str
    version: str
    phase: int
    sprint: int
    status: str
    quality_score: float
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
