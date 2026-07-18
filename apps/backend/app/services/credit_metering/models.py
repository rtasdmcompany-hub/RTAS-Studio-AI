"""Domain models for credit consumption, metering, quotas, and costs."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid4()}"


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


@dataclass
class CreditUsageEvent:
    id: str
    organization_id: str
    workspace_id: str | None
    user_id: str | None
    team_id: str | None
    service_type: str
    provider: str
    credits: int
    quantity: float = 1.0
    resource_type: str | None = None
    resource_id: str | None = None
    status: str = "completed"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "userId": self.user_id,
            "teamId": self.team_id,
            "serviceType": self.service_type,
            "provider": self.provider,
            "credits": self.credits,
            "quantity": self.quantity,
            "resourceType": self.resource_type,
            "resourceId": self.resource_id,
            "status": self.status,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class UsageMetricBucket:
    id: str
    organization_id: str
    workspace_id: str | None
    user_id: str | None
    provider: str | None
    period: str  # day|week|month
    period_key: str  # e.g. 2026-07-19
    credits_used: int = 0
    request_count: int = 0
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "userId": self.user_id,
            "provider": self.provider,
            "period": self.period,
            "periodKey": self.period_key,
            "creditsUsed": self.credits_used,
            "requestCount": self.request_count,
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class UsageQuota:
    id: str
    organization_id: str
    workspace_id: str | None = None
    team_id: str | None = None
    plan_key: str = "free_trial"
    daily_limit: int = 50
    monthly_limit: int = 100
    trial_limit: int = 100
    unlimited: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "teamId": self.team_id,
            "planKey": self.plan_key,
            "dailyLimit": self.daily_limit,
            "monthlyLimit": self.monthly_limit,
            "trialLimit": self.trial_limit,
            "unlimited": self.unlimited,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class AIUsageHistoryEntry:
    id: str
    organization_id: str
    workspace_id: str | None
    user_id: str | None
    service_type: str
    provider: str
    credits: int
    cost_usd: float
    detail: str = ""
    usage_event_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "userId": self.user_id,
            "serviceType": self.service_type,
            "provider": self.provider,
            "credits": self.credits,
            "costUsd": self.cost_usd,
            "detail": self.detail,
            "usageEventId": self.usage_event_id,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class CostCalculation:
    id: str
    organization_id: str
    service_type: str
    provider: str
    credits: int
    provider_cost_usd: float
    gpu_cost_usd: float
    model_cost_usd: float
    retail_value_usd: float
    estimated_margin_usd: float
    margin_pct: float
    quantity: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "serviceType": self.service_type,
            "provider": self.provider,
            "credits": self.credits,
            "quantity": self.quantity,
            "providerCostUsd": round(self.provider_cost_usd, 6),
            "gpuCostUsd": round(self.gpu_cost_usd, 6),
            "modelCostUsd": round(self.model_cost_usd, 6),
            "retailValueUsd": round(self.retail_value_usd, 6),
            "estimatedMarginUsd": round(self.estimated_margin_usd, 6),
            "marginPct": round(self.margin_pct, 2),
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class ProviderCostRate:
    id: str
    provider: str
    cost_per_credit_usd: float
    currency: str = "USD"
    active: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "provider": self.provider,
            "costPerCreditUsd": self.cost_per_credit_usd,
            "currency": self.currency,
            "active": self.active,
            "metadata": dict(self.metadata),
            "updatedAt": _iso(self.updated_at),
        }
