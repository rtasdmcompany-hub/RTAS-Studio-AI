"""Domain models for billing & subscriptions."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
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
class SubscriptionPlan:
    id: str
    key: str
    name: str
    description: str = ""
    monthly_price_usd: float = 0.0
    yearly_price_usd: float = 0.0
    credits_monthly: int = 0
    credits_yearly: int = 0
    max_workspaces: int = 1
    max_teams: int = 1
    max_members: int = 3
    max_projects: int = 10
    ai_provider_limit: int = 1
    features: list[str] = field(default_factory=list)
    is_public: bool = True
    trial_days: int = 0
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "key": self.key,
            "name": self.name,
            "description": self.description,
            "monthlyPriceUsd": self.monthly_price_usd,
            "yearlyPriceUsd": self.yearly_price_usd,
            "creditsMonthly": self.credits_monthly,
            "creditsYearly": self.credits_yearly,
            "maxWorkspaces": self.max_workspaces,
            "maxTeams": self.max_teams,
            "maxMembers": self.max_members,
            "maxProjects": self.max_projects,
            "aiProviderLimit": self.ai_provider_limit,
            "features": list(self.features),
            "isPublic": self.is_public,
            "trialDays": self.trial_days,
            "status": self.status,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class OrganizationSubscription:
    id: str
    organization_id: str
    plan_key: str
    billing_cycle: str = "monthly"
    status: str = "active"
    owner_user_id: str | None = None
    seats: int = 1
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False
    external_subscription_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "planKey": self.plan_key,
            "billingCycle": self.billing_cycle,
            "status": self.status,
            "ownerUserId": self.owner_user_id,
            "seats": self.seats,
            "currentPeriodStart": _iso(self.current_period_start),
            "currentPeriodEnd": _iso(self.current_period_end),
            "cancelAtPeriodEnd": self.cancel_at_period_end,
            "externalSubscriptionId": self.external_subscription_id,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class UserSubscription:
    id: str
    user_id: str
    plan_key: str
    billing_cycle: str = "monthly"
    status: str = "active"
    organization_id: str | None = None
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    cancel_at_period_end: bool = False
    external_subscription_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "userId": self.user_id,
            "planKey": self.plan_key,
            "billingCycle": self.billing_cycle,
            "status": self.status,
            "organizationId": self.organization_id,
            "currentPeriodStart": _iso(self.current_period_start),
            "currentPeriodEnd": _iso(self.current_period_end),
            "cancelAtPeriodEnd": self.cancel_at_period_end,
            "externalSubscriptionId": self.external_subscription_id,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class CreditWallet:
    id: str
    organization_id: str
    workspace_id: str | None = None
    balance: int = 0
    reserved: int = 0
    lifetime_granted: int = 0
    lifetime_spent: int = 0
    currency: str = "credits"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "balance": self.balance,
            "reserved": self.reserved,
            "available": max(0, self.balance - self.reserved),
            "lifetimeGranted": self.lifetime_granted,
            "lifetimeSpent": self.lifetime_spent,
            "currency": self.currency,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class CreditTransaction:
    id: str
    wallet_id: str
    organization_id: str
    amount: int
    balance_after: int
    txn_type: str
    reason: str = ""
    actor_id: str | None = None
    workspace_id: str | None = None
    reference_type: str | None = None
    reference_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "walletId": self.wallet_id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "amount": self.amount,
            "balanceAfter": self.balance_after,
            "type": self.txn_type,
            "reason": self.reason,
            "actorId": self.actor_id,
            "referenceType": self.reference_type,
            "referenceId": self.reference_id,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class UsageRecord:
    id: str
    organization_id: str
    usage_type: str
    quantity: float = 1.0
    credits_consumed: int = 0
    workspace_id: str | None = None
    user_id: str | None = None
    provider: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    recorded_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "userId": self.user_id,
            "usageType": self.usage_type,
            "quantity": self.quantity,
            "creditsConsumed": self.credits_consumed,
            "provider": self.provider,
            "resourceType": self.resource_type,
            "resourceId": self.resource_id,
            "metadata": dict(self.metadata),
            "recordedAt": _iso(self.recorded_at),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class BillingProfile:
    id: str
    organization_id: str
    company_name: str = ""
    billing_email: str = ""
    country: str = ""
    tax_id: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    state: str | None = None
    postal_code: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "companyName": self.company_name,
            "billingEmail": self.billing_email,
            "country": self.country,
            "taxId": self.tax_id,
            "addressLine1": self.address_line1,
            "addressLine2": self.address_line2,
            "city": self.city,
            "state": self.state,
            "postalCode": self.postal_code,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
            "_raw": d,
        }


@dataclass
class Invoice:
    id: str
    organization_id: str
    subscription_id: str | None = None
    invoice_number: str = ""
    status: str = "draft"
    currency: str = "USD"
    subtotal_usd: float = 0.0
    tax_usd: float = 0.0
    total_usd: float = 0.0
    billing_cycle: str = "monthly"
    plan_key: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    issued_at: datetime | None = None
    due_at: datetime | None = None
    paid_at: datetime | None = None
    line_items: list[dict[str, Any]] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "subscriptionId": self.subscription_id,
            "invoiceNumber": self.invoice_number,
            "status": self.status,
            "currency": self.currency,
            "subtotalUsd": self.subtotal_usd,
            "taxUsd": self.tax_usd,
            "totalUsd": self.total_usd,
            "billingCycle": self.billing_cycle,
            "planKey": self.plan_key,
            "periodStart": _iso(self.period_start),
            "periodEnd": _iso(self.period_end),
            "issuedAt": _iso(self.issued_at),
            "dueAt": _iso(self.due_at),
            "paidAt": _iso(self.paid_at),
            "lineItems": list(self.line_items),
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }
