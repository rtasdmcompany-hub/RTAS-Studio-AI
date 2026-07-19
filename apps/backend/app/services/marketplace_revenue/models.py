"""Domain models for marketplace revenue intelligence & monetization."""

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
class RevenueLedgerRecord:
    """Atomic revenue / refund ledger entry."""

    id: str
    organization_id: str
    workspace_id: str | None
    stream: str
    amount: float
    currency: str = "USD"
    creator_id: str | None = None
    product_id: str | None = None
    customer_id: str | None = None
    period: str = ""  # YYYY-MM
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "stream": self.stream,
            "amount": self.amount,
            "currency": self.currency,
            "creatorId": self.creator_id,
            "productId": self.product_id,
            "customerId": self.customer_id,
            "period": self.period,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class SalesEventRecord:
    id: str
    organization_id: str
    workspace_id: str | None
    event_type: str
    amount: float
    product_id: str | None = None
    creator_id: str | None = None
    customer_id: str | None = None
    quantity: int = 1
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "eventType": self.event_type,
            "amount": self.amount,
            "productId": self.product_id,
            "creatorId": self.creator_id,
            "customerId": self.customer_id,
            "quantity": self.quantity,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class ProductMetricRecord:
    id: str
    organization_id: str
    product_id: str
    metric: str
    category: str = "other"
    featured: bool = False
    value: float = 1.0
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "productId": self.product_id,
            "metric": self.metric,
            "category": self.category,
            "featured": self.featured,
            "value": self.value,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class CreatorStatsRecord:
    id: str
    organization_id: str
    creator_id: str
    revenue: float = 0.0
    sales: int = 0
    downloads: int = 0
    views: int = 0
    rating_total: float = 0.0
    rating_count: int = 0
    review_count: int = 0
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        avg = (
            round(self.rating_total / self.rating_count, 2)
            if self.rating_count
            else 0.0
        )
        conversion = (
            round((self.sales / self.views) * 100.0, 2) if self.views else 0.0
        )
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "creatorId": self.creator_id,
            "revenue": round(self.revenue, 2),
            "sales": self.sales,
            "downloads": self.downloads,
            "views": self.views,
            "averageRating": avg,
            "reviewCount": self.review_count,
            "conversionRate": conversion,
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class CustomerMetricRecord:
    id: str
    organization_id: str
    customer_id: str
    total_spend: float = 0.0
    purchases: int = 0
    first_seen_at: datetime = field(default_factory=_now)
    last_seen_at: datetime = field(default_factory=_now)
    churned: bool = False

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "customerId": self.customer_id,
            "totalSpend": round(self.total_spend, 2),
            "purchases": self.purchases,
            "firstSeenAt": _iso(self.first_seen_at),
            "lastSeenAt": _iso(self.last_seen_at),
            "churned": self.churned,
        }


@dataclass
class RevenueForecastRecord:
    id: str
    organization_id: str
    horizon: str
    projected: list[float] = field(default_factory=list)
    baseline: float = 0.0
    growth_rate: float = 0.0
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "horizon": self.horizon,
            "projected": list(self.projected),
            "baseline": self.baseline,
            "growthRate": self.growth_rate,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class FinancialSummaryRecord:
    id: str
    organization_id: str
    period: str
    gross_revenue: float = 0.0
    refund_amount: float = 0.0
    net_revenue: float = 0.0
    subscription_revenue: float = 0.0
    marketplace_revenue: float = 0.0
    credit_sales_revenue: float = 0.0
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "period": self.period,
            "grossRevenue": round(self.gross_revenue, 2),
            "refundAmount": round(self.refund_amount, 2),
            "netRevenue": round(self.net_revenue, 2),
            "subscriptionRevenue": round(self.subscription_revenue, 2),
            "marketplaceRevenue": round(self.marketplace_revenue, 2),
            "creditSalesRevenue": round(self.credit_sales_revenue, 2),
            "createdAt": _iso(self.created_at),
        }
