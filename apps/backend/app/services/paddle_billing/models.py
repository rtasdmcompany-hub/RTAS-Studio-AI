"""Domain models for Paddle billing integration."""

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
class PaddleCustomer:
    id: str
    organization_id: str
    paddle_customer_id: str
    email: str = ""
    name: str = ""
    country_code: str = ""
    tax_identifier: str | None = None
    address_line1: str | None = None
    address_line2: str | None = None
    city: str | None = None
    region: str | None = None
    postal_code: str | None = None
    status: str = "active"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "paddleCustomerId": self.paddle_customer_id,
            "email": self.email,
            "name": self.name,
            "countryCode": self.country_code,
            "taxIdentifier": self.tax_identifier,
            "addressLine1": self.address_line1,
            "addressLine2": self.address_line2,
            "city": self.city,
            "region": self.region,
            "postalCode": self.postal_code,
            "status": self.status,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class PaddleSubscription:
    id: str
    organization_id: str
    paddle_subscription_id: str
    paddle_customer_id: str
    plan_key: str
    billing_cycle: str = "monthly"
    status: str = "active"
    price_id: str | None = None
    product_id: str | None = None
    cancel_at_period_end: bool = False
    current_period_start: datetime | None = None
    current_period_end: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "paddleSubscriptionId": self.paddle_subscription_id,
            "paddleCustomerId": self.paddle_customer_id,
            "planKey": self.plan_key,
            "billingCycle": self.billing_cycle,
            "status": self.status,
            "priceId": self.price_id,
            "productId": self.product_id,
            "cancelAtPeriodEnd": self.cancel_at_period_end,
            "currentPeriodStart": _iso(self.current_period_start),
            "currentPeriodEnd": _iso(self.current_period_end),
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class PaddleTransaction:
    id: str
    organization_id: str
    paddle_transaction_id: str
    paddle_subscription_id: str | None = None
    paddle_customer_id: str | None = None
    status: str = "completed"
    amount_usd: float = 0.0
    currency: str = "USD"
    event_type: str = "transaction.completed"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "paddleTransactionId": self.paddle_transaction_id,
            "paddleSubscriptionId": self.paddle_subscription_id,
            "paddleCustomerId": self.paddle_customer_id,
            "status": self.status,
            "amountUsd": self.amount_usd,
            "currency": self.currency,
            "eventType": self.event_type,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class PaddleWebhookLog:
    id: str
    event_id: str
    event_type: str
    signature_valid: bool
    processed: bool = False
    organization_id: str | None = None
    error: str | None = None
    payload: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "eventId": self.event_id,
            "eventType": self.event_type,
            "signatureValid": self.signature_valid,
            "processed": self.processed,
            "organizationId": self.organization_id,
            "error": self.error,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class BillingEvent:
    id: str
    organization_id: str
    event_type: str
    source: str = "paddle"
    actor_id: str | None = None
    detail: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "eventType": self.event_type,
            "source": self.source,
            "actorId": self.actor_id,
            "detail": self.detail,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class CheckoutSession:
    id: str
    organization_id: str
    plan_key: str
    billing_cycle: str
    price_id: str
    customer_id: str
    checkout_url: str
    status: str = "pending"
    actor_id: str | None = None
    success_url: str | None = None
    cancel_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "planKey": self.plan_key,
            "billingCycle": self.billing_cycle,
            "priceId": self.price_id,
            "customerId": self.customer_id,
            "checkoutUrl": self.checkout_url,
            "status": self.status,
            "actorId": self.actor_id,
            "successUrl": self.success_url,
            "cancelUrl": self.cancel_url,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }
