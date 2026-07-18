"""Domain models for invoicing, tax, coupons, and billing automation."""

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
class InvoiceRecord:
    id: str
    organization_id: str
    invoice_number: str
    status: str = "pending"
    currency: str = "USD"
    subtotal_usd: float = 0.0
    discount_usd: float = 0.0
    tax_usd: float = 0.0
    total_usd: float = 0.0
    tax_type: str = "none"
    tax_rate: float = 0.0
    country: str = "US"
    plan_key: str | None = None
    billing_cycle: str = "monthly"
    coupon_code: str | None = None
    pdf_metadata: dict[str, Any] = field(default_factory=dict)
    receipt_number: str | None = None
    actor_id: str | None = None
    period_start: datetime | None = None
    period_end: datetime | None = None
    issued_at: datetime | None = None
    due_at: datetime | None = None
    paid_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "invoiceNumber": self.invoice_number,
            "status": self.status,
            "currency": self.currency,
            "subtotalUsd": round(self.subtotal_usd, 2),
            "discountUsd": round(self.discount_usd, 2),
            "taxUsd": round(self.tax_usd, 2),
            "totalUsd": round(self.total_usd, 2),
            "taxType": self.tax_type,
            "taxRate": self.tax_rate,
            "country": self.country,
            "planKey": self.plan_key,
            "billingCycle": self.billing_cycle,
            "couponCode": self.coupon_code,
            "pdfMetadata": dict(self.pdf_metadata),
            "receiptNumber": self.receipt_number,
            "actorId": self.actor_id,
            "periodStart": _iso(self.period_start),
            "periodEnd": _iso(self.period_end),
            "issuedAt": _iso(self.issued_at),
            "dueAt": _iso(self.due_at),
            "paidAt": _iso(self.paid_at),
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class InvoiceItem:
    id: str
    invoice_id: str
    organization_id: str
    description: str
    quantity: float = 1.0
    unit_price_usd: float = 0.0
    amount_usd: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "invoiceId": self.invoice_id,
            "organizationId": self.organization_id,
            "description": self.description,
            "quantity": self.quantity,
            "unitPriceUsd": round(self.unit_price_usd, 2),
            "amountUsd": round(self.amount_usd, 2),
            "metadata": dict(self.metadata),
        }


@dataclass
class TaxRecord:
    id: str
    organization_id: str
    invoice_id: str | None
    country: str
    tax_type: str
    rate: float
    taxable_usd: float
    tax_usd: float
    exempt: bool = False
    exemption_reason: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "invoiceId": self.invoice_id,
            "country": self.country,
            "taxType": self.tax_type,
            "rate": self.rate,
            "taxableUsd": round(self.taxable_usd, 2),
            "taxUsd": round(self.tax_usd, 2),
            "exempt": self.exempt,
            "exemptionReason": self.exemption_reason,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class Coupon:
    id: str
    code: str
    coupon_type: str
    percent_off: float = 0.0
    amount_off_usd: float = 0.0
    category: str = "promotional"
    max_redemptions: int = 100
    redemption_count: int = 0
    per_org_limit: int = 1
    trial_days: int = 0
    active: bool = True
    expires_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "code": self.code,
            "couponType": self.coupon_type,
            "percentOff": self.percent_off,
            "amountOffUsd": self.amount_off_usd,
            "category": self.category,
            "maxRedemptions": self.max_redemptions,
            "redemptionCount": self.redemption_count,
            "perOrgLimit": self.per_org_limit,
            "trialDays": self.trial_days,
            "active": self.active,
            "expiresAt": _iso(self.expires_at),
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class CouponUsage:
    id: str
    coupon_id: str
    coupon_code: str
    organization_id: str
    actor_id: str | None
    discount_usd: float = 0.0
    invoice_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "couponId": self.coupon_id,
            "couponCode": self.coupon_code,
            "organizationId": self.organization_id,
            "actorId": self.actor_id,
            "discountUsd": round(self.discount_usd, 2),
            "invoiceId": self.invoice_id,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class DiscountRecord:
    id: str
    organization_id: str
    discount_type: str
    amount_usd: float
    percent_off: float = 0.0
    coupon_code: str | None = None
    invoice_id: str | None = None
    reason: str = ""
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "discountType": self.discount_type,
            "amountUsd": round(self.amount_usd, 2),
            "percentOff": self.percent_off,
            "couponCode": self.coupon_code,
            "invoiceId": self.invoice_id,
            "reason": self.reason,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class AutomationBillingEvent:
    id: str
    organization_id: str
    event_type: str
    detail: str = ""
    actor_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "eventType": self.event_type,
            "detail": self.detail,
            "actorId": self.actor_id,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class PaymentRetry:
    id: str
    organization_id: str
    invoice_id: str
    attempt: int = 0
    max_attempts: int = 3
    status: str = "scheduled"  # scheduled|processing|succeeded|failed|exhausted
    next_retry_at: datetime | None = None
    last_error: str = ""
    actor_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "invoiceId": self.invoice_id,
            "attempt": self.attempt,
            "maxAttempts": self.max_attempts,
            "status": self.status,
            "nextRetryAt": _iso(self.next_retry_at),
            "lastError": self.last_error,
            "actorId": self.actor_id,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }
