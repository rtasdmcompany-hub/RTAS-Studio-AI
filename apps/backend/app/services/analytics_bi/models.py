"""Domain models for analytics, reporting & BI."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid4()}" if prefix else str(uuid4())


@dataclass
class AnalyticsRecord:
    id: str
    organization_id: str
    category: str
    metric_key: str
    metric_value: float = 0.0
    workspace_id: str | None = None
    dimensions: dict[str, Any] = field(default_factory=dict)
    recorded_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "category": self.category,
            "metricKey": self.metric_key,
            "metricValue": self.metric_value,
            "dimensions": dict(self.dimensions),
            "recordedAt": _iso(self.recorded_at),
        }


@dataclass
class BusinessMetric:
    id: str
    organization_id: str
    name: str
    value: float = 0.0
    workspace_id: str | None = None
    unit: str | None = None
    period: str = "daily"
    metadata: dict[str, Any] = field(default_factory=dict)
    recorded_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "period": self.period,
            "metadata": dict(self.metadata),
            "recordedAt": _iso(self.recorded_at),
        }


@dataclass
class KpiRecord:
    id: str
    organization_id: str
    kpi_key: str
    label: str
    value: float = 0.0
    workspace_id: str | None = None
    target: float | None = None
    unit: str | None = None
    trend: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    recorded_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "kpiKey": self.kpi_key,
            "label": self.label,
            "value": self.value,
            "target": self.target,
            "unit": self.unit,
            "trend": self.trend,
            "metadata": dict(self.metadata),
            "recordedAt": _iso(self.recorded_at),
        }


@dataclass
class ReportHistory:
    id: str
    organization_id: str
    report_type: str
    title: str
    workspace_id: str | None = None
    generated_by_id: str | None = None
    scope: str = "organization"
    period_start: datetime | None = None
    period_end: datetime | None = None
    status: str = "ready"
    payload: dict[str, Any] = field(default_factory=dict)
    duration_ms: float = 0.0
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "generatedById": self.generated_by_id,
            "reportType": self.report_type,
            "scope": self.scope,
            "title": self.title,
            "periodStart": _iso(self.period_start),
            "periodEnd": _iso(self.period_end),
            "status": self.status,
            "payload": dict(self.payload),
            "durationMs": self.duration_ms,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class UsageStatistic:
    id: str
    organization_id: str
    usage_type: str
    count: int = 0
    bytes: int = 0
    workspace_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    recorded_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "usageType": self.usage_type,
            "count": self.count,
            "bytes": self.bytes,
            "metadata": dict(self.metadata),
            "recordedAt": _iso(self.recorded_at),
        }


@dataclass
class PerformanceStatistic:
    id: str
    organization_id: str
    metric_key: str
    avg_ms: float = 0.0
    p95_ms: float = 0.0
    success_rate: float = 1.0
    sample_count: int = 0
    workspace_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    recorded_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "metricKey": self.metric_key,
            "avgMs": self.avg_ms,
            "p95Ms": self.p95_ms,
            "successRate": self.success_rate,
            "sampleCount": self.sample_count,
            "metadata": dict(self.metadata),
            "recordedAt": _iso(self.recorded_at),
        }


@dataclass
class ForecastRecord:
    id: str
    organization_id: str
    metric_key: str
    predicted_value: float = 0.0
    workspace_id: str | None = None
    horizon_days: int = 30
    confidence: float = 0.7
    method: str = "linear"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "metricKey": self.metric_key,
            "horizonDays": self.horizon_days,
            "predictedValue": self.predicted_value,
            "confidence": self.confidence,
            "method": self.method,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }
