"""Domain models for PayPal payments and credit wallet."""

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
class WalletAccount:
    id: str
    organization_id: str
    balance: int = 0
    reserved: int = 0
    bonus_balance: int = 0
    trial_balance: int = 0
    promo_balance: int = 0
    lifetime_purchased: int = 0
    lifetime_consumed: int = 0
    lifetime_refunded: int = 0
    lifetime_awarded: int = 0
    expires_at: datetime | None = None
    currency: str = "credits"
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def available(self) -> int:
        return max(0, self.balance - self.reserved)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "balance": self.balance,
            "reserved": self.reserved,
            "available": self.available,
            "bonusBalance": self.bonus_balance,
            "trialBalance": self.trial_balance,
            "promoBalance": self.promo_balance,
            "lifetimePurchased": self.lifetime_purchased,
            "lifetimeConsumed": self.lifetime_consumed,
            "lifetimeRefunded": self.lifetime_refunded,
            "lifetimeAwarded": self.lifetime_awarded,
            "expiresAt": _iso(self.expires_at),
            "currency": self.currency,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class WalletTransaction:
    id: str
    wallet_id: str
    organization_id: str
    amount: int
    balance_after: int
    txn_type: str
    credit_category: str = "purchased"  # purchased|bonus|trial|promo|subscription
    reason: str = ""
    actor_id: str | None = None
    reference_type: str | None = None
    reference_id: str | None = None
    expires_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "walletId": self.wallet_id,
            "organizationId": self.organization_id,
            "amount": self.amount,
            "balanceAfter": self.balance_after,
            "type": self.txn_type,
            "creditCategory": self.credit_category,
            "reason": self.reason,
            "actorId": self.actor_id,
            "referenceType": self.reference_type,
            "referenceId": self.reference_id,
            "expiresAt": _iso(self.expires_at),
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class PayPalPayment:
    id: str
    organization_id: str
    paypal_order_id: str
    status: str = "CREATED"
    intent: str = "CAPTURE"
    amount_usd: float = 0.0
    currency: str = "USD"
    pack_key: str | None = None
    credits: int = 0
    bonus_credits: int = 0
    paypal_capture_id: str | None = None
    payer_email: str | None = None
    actor_id: str | None = None
    verified: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "paypalOrderId": self.paypal_order_id,
            "paypalCaptureId": self.paypal_capture_id,
            "status": self.status,
            "intent": self.intent,
            "amountUsd": self.amount_usd,
            "currency": self.currency,
            "packKey": self.pack_key,
            "credits": self.credits,
            "bonusCredits": self.bonus_credits,
            "payerEmail": self.payer_email,
            "actorId": self.actor_id,
            "verified": self.verified,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class PaymentHistoryEntry:
    id: str
    organization_id: str
    payment_id: str
    provider: str = "paypal"
    action: str = "created"
    status: str = ""
    amount_usd: float = 0.0
    detail: str = ""
    actor_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "paymentId": self.payment_id,
            "provider": self.provider,
            "action": self.action,
            "status": self.status,
            "amountUsd": self.amount_usd,
            "detail": self.detail,
            "actorId": self.actor_id,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class RefundRequest:
    id: str
    organization_id: str
    payment_id: str | None = None
    wallet_txn_id: str | None = None
    status: str = "pending"
    credits: int = 0
    amount_usd: float = 0.0
    reason: str = ""
    actor_id: str | None = None
    reviewer_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "paymentId": self.payment_id,
            "walletTxnId": self.wallet_txn_id,
            "status": self.status,
            "credits": self.credits,
            "amountUsd": self.amount_usd,
            "reason": self.reason,
            "actorId": self.actor_id,
            "reviewerId": self.reviewer_id,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class RefundHistoryEntry:
    id: str
    organization_id: str
    refund_request_id: str
    action: str
    status: str
    detail: str = ""
    actor_id: str | None = None
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "refundRequestId": self.refund_request_id,
            "action": self.action,
            "status": self.status,
            "detail": self.detail,
            "actorId": self.actor_id,
            "createdAt": _iso(self.created_at),
        }
