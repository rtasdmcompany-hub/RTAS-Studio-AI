"""Domain models for provider usage, cost analytics, budgets, and profit reports."""

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


def _now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass
class ProviderUsageEvent:
    id: str
    organization_id: str
    provider: str
    model: str = ""
    user_id: str | None = None
    workspace_id: str | None = None
    status: str = "success"  # success|failed
    latency_ms: float = 0.0
    credits_charged: float = 0.0
    cost_breakdown_usd: dict[str, float] = field(default_factory=dict)
    total_cost_usd: float = 0.0
    revenue_usd: float = 0.0
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "provider": self.provider,
            "model": self.model,
            "userId": self.user_id,
            "workspaceId": self.workspace_id,
            "status": self.status,
            "latencyMs": round(self.latency_ms, 3),
            "creditsCharged": round(self.credits_charged, 4),
            "costBreakdownUsd": {k: round(v, 6) for k, v in self.cost_breakdown_usd.items()},
            "totalCostUsd": round(self.total_cost_usd, 6),
            "revenueUsd": round(self.revenue_usd, 6),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class BudgetPolicy:
    id: str
    organization_id: str
    scope: str = "organization"  # organization|workspace
    scope_id: str = ""
    daily_limit_usd: float = 0.0  # 0 = no limit
    monthly_limit_usd: float = 0.0
    alerts_enabled: bool = True
    hard_stop: bool = False  # block spending once limit reached
    updated_by: str | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "scope": self.scope,
            "scopeId": self.scope_id,
            "dailyLimitUsd": round(self.daily_limit_usd, 2),
            "monthlyLimitUsd": round(self.monthly_limit_usd, 2),
            "alertsEnabled": self.alerts_enabled,
            "hardStop": self.hard_stop,
            "updatedBy": self.updated_by,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class BudgetEvent:
    id: str
    organization_id: str
    policy_id: str
    event_type: str  # threshold_alert|limit_reached|budget_updated|spend_recorded
    period: str = "daily"
    threshold_pct: float = 0.0
    spent_usd: float = 0.0
    limit_usd: float = 0.0
    detail: str = ""
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "policyId": self.policy_id,
            "eventType": self.event_type,
            "period": self.period,
            "thresholdPct": round(self.threshold_pct, 2),
            "spentUsd": round(self.spent_usd, 6),
            "limitUsd": round(self.limit_usd, 2),
            "detail": self.detail,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class ProfitReport:
    id: str
    organization_id: str
    period: str  # e.g. 2026-07
    revenue_usd: float = 0.0
    provider_cost_usd: float = 0.0
    infrastructure_cost_usd: float = 0.0
    fixed_overhead_usd: float = 0.0
    gross_profit_usd: float = 0.0
    net_profit_usd: float = 0.0
    margin_pct: float = 0.0
    generated_by: str | None = None
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "period": self.period,
            "revenueUsd": round(self.revenue_usd, 6),
            "providerCostUsd": round(self.provider_cost_usd, 6),
            "infrastructureCostUsd": round(self.infrastructure_cost_usd, 6),
            "fixedOverheadUsd": round(self.fixed_overhead_usd, 2),
            "grossProfitUsd": round(self.gross_profit_usd, 6),
            "netProfitUsd": round(self.net_profit_usd, 6),
            "marginPct": round(self.margin_pct, 2),
            "generatedBy": self.generated_by,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class OptimizationRecord:
    id: str
    organization_id: str
    mode: str
    capability: str = ""
    selected_provider: str = ""
    estimated_cost_usd: float = 0.0
    estimated_latency_ms: float = 0.0
    quality_score: float = 0.0
    savings_usd: float = 0.0
    reason: str = ""
    ranking: list[dict[str, Any]] = field(default_factory=list)
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "mode": self.mode,
            "capability": self.capability,
            "selectedProvider": self.selected_provider,
            "estimatedCostUsd": round(self.estimated_cost_usd, 6),
            "estimatedLatencyMs": round(self.estimated_latency_ms, 3),
            "qualityScore": round(self.quality_score, 2),
            "savingsUsd": round(self.savings_usd, 6),
            "reason": self.reason,
            "ranking": [dict(r) for r in self.ranking],
            "createdAt": _iso(self.created_at),
        }
