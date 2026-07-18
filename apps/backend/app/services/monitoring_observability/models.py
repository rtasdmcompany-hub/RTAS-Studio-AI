"""Datamodels for monitoring, incidents, alerts, and recovery."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal
from uuid import uuid4

ComponentStatus = Literal["healthy", "degraded", "unhealthy", "unknown", "offline"]
IncidentSeverity = Literal["low", "medium", "high", "critical"]
IncidentStatus = Literal["open", "acknowledged", "mitigating", "resolved"]
AlertLevel = Literal["info", "warning", "error", "critical"]
RecoveryAction = Literal[
    "restart_worker",
    "retry_job",
    "reconnect_service",
    "refresh_token",
    "recover_queue",
    "detect_deadlock",
    "recover_stuck_job",
    "failover",
]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid4().hex[:12]}"


@dataclass
class ComponentHealth:
    name: str
    status: ComponentStatus
    latency_ms: float = 0.0
    detail: str = ""
    metrics: dict[str, Any] = field(default_factory=dict)
    checked_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class HealthReport:
    report_id: str
    overall: ComponentStatus
    components: list[ComponentHealth]
    uptime_sec: float
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return {
            "report_id": self.report_id,
            "overall": self.overall,
            "components": [c.to_dict() for c in self.components],
            "uptime_sec": round(self.uptime_sec, 2),
            "created_at": self.created_at,
        }


@dataclass
class MonitoringEvent:
    event_id: str
    category: str
    message: str
    severity: AlertLevel = "info"
    component: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Incident:
    incident_id: str
    title: str
    severity: IncidentSeverity
    status: IncidentStatus
    component: str
    description: str
    recovery_actions: list[str] = field(default_factory=list)
    created_at: str = field(default_factory=_now_iso)
    resolved_at: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Alert:
    alert_id: str
    level: AlertLevel
    alert_type: str
    message: str
    component: str
    acknowledged: bool = False
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class RecoveryRecord:
    recovery_id: str
    action: RecoveryAction
    target: str
    success: bool
    detail: str
    incident_id: str | None = None
    created_at: str = field(default_factory=_now_iso)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class PerformanceSnapshot:
    request_rate: float
    success_rate: float
    failure_rate: float
    avg_response_ms: float
    queue_latency_ms: float
    provider_latency_ms: float
    active_jobs: int
    workers_online: int
    workers_total: int
    uptime_sec: float
    error_categories: dict[str, int] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
