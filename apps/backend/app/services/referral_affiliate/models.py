"""Domain models for referrals, affiliates, commissions, and payouts."""

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
class ReferralCode:
    id: str
    organization_id: str
    owner_user_id: str
    code: str
    link: str
    active: bool = True
    uses: int = 0
    max_uses: int = 0  # 0 = unlimited
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "ownerUserId": self.owner_user_id,
            "code": self.code,
            "link": self.link,
            "active": self.active,
            "uses": self.uses,
            "maxUses": self.max_uses,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class Referral:
    id: str
    organization_id: str
    referral_code_id: str
    code: str
    referrer_user_id: str
    referred_email: str = ""
    referred_user_id: str | None = None
    status: str = "invited"  # invited|signed_up|converted|rewarded
    reward_credits: int = 0
    referred_bonus_credits: int = 0
    invited_at: datetime = field(default_factory=_now)
    signed_up_at: datetime | None = None
    converted_at: datetime | None = None
    rewarded_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "referralCodeId": self.referral_code_id,
            "code": self.code,
            "referrerUserId": self.referrer_user_id,
            "referredEmail": self.referred_email,
            "referredUserId": self.referred_user_id,
            "status": self.status,
            "rewardCredits": self.reward_credits,
            "referredBonusCredits": self.referred_bonus_credits,
            "invitedAt": _iso(self.invited_at),
            "signedUpAt": _iso(self.signed_up_at),
            "convertedAt": _iso(self.converted_at),
            "rewardedAt": _iso(self.rewarded_at),
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class Affiliate:
    id: str
    organization_id: str
    user_id: str
    name: str = ""
    email: str = ""
    status: str = "active"  # pending|active|suspended|rejected
    commission_type: str = "percentage"
    commission_rate: float = 20.0  # pct for percentage, USD for fixed
    recurring_rate_pct: float = 10.0
    payout_method: str = "paypal"
    parent_affiliate_id: str | None = None  # multi-level ready
    pending_usd: float = 0.0
    approved_usd: float = 0.0
    paid_usd: float = 0.0
    lifetime_usd: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "userId": self.user_id,
            "name": self.name,
            "email": self.email,
            "status": self.status,
            "commissionType": self.commission_type,
            "commissionRate": self.commission_rate,
            "recurringRatePct": self.recurring_rate_pct,
            "payoutMethod": self.payout_method,
            "parentAffiliateId": self.parent_affiliate_id,
            "pendingUsd": round(self.pending_usd, 4),
            "approvedUsd": round(self.approved_usd, 4),
            "paidUsd": round(self.paid_usd, 4),
            "lifetimeUsd": round(self.lifetime_usd, 4),
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class AffiliateCampaign:
    id: str
    affiliate_id: str
    organization_id: str
    name: str
    slug: str
    link: str
    active: bool = True
    clicks: int = 0
    conversions: int = 0
    revenue_usd: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "affiliateId": self.affiliate_id,
            "organizationId": self.organization_id,
            "name": self.name,
            "slug": self.slug,
            "link": self.link,
            "active": self.active,
            "clicks": self.clicks,
            "conversions": self.conversions,
            "revenueUsd": round(self.revenue_usd, 4),
            "conversionRatePct": round(
                (self.conversions / self.clicks * 100.0) if self.clicks else 0.0, 2
            ),
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class AffiliateClick:
    id: str
    affiliate_id: str
    organization_id: str
    campaign_id: str | None = None
    source: str = ""
    referrer_url: str = ""
    ip_hash: str = ""
    user_agent: str = ""
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "affiliateId": self.affiliate_id,
            "organizationId": self.organization_id,
            "campaignId": self.campaign_id,
            "source": self.source,
            "referrerUrl": self.referrer_url,
            "ipHash": self.ip_hash,
            "userAgent": self.user_agent,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class AffiliateConversion:
    id: str
    affiliate_id: str
    organization_id: str
    campaign_id: str | None = None
    order_ref: str = ""
    kind: str = "one_time"  # one_time|recurring
    amount_usd: float = 0.0
    commission_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "affiliateId": self.affiliate_id,
            "organizationId": self.organization_id,
            "campaignId": self.campaign_id,
            "orderRef": self.order_ref,
            "kind": self.kind,
            "amountUsd": round(self.amount_usd, 4),
            "commissionIds": list(self.commission_ids),
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class Commission:
    id: str
    affiliate_id: str
    organization_id: str
    conversion_id: str | None = None
    level: int = 1
    commission_type: str = "percentage"
    kind: str = "one_time"  # one_time|recurring
    base_amount_usd: float = 0.0
    rate: float = 0.0
    amount_usd: float = 0.0
    status: str = "pending"  # pending|approved|paid|rejected
    payout_id: str | None = None
    approved_at: datetime | None = None
    paid_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "affiliateId": self.affiliate_id,
            "organizationId": self.organization_id,
            "conversionId": self.conversion_id,
            "level": self.level,
            "commissionType": self.commission_type,
            "kind": self.kind,
            "baseAmountUsd": round(self.base_amount_usd, 4),
            "rate": self.rate,
            "amountUsd": round(self.amount_usd, 4),
            "status": self.status,
            "payoutId": self.payout_id,
            "approvedAt": _iso(self.approved_at),
            "paidAt": _iso(self.paid_at),
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class PayoutRequest:
    id: str
    affiliate_id: str
    organization_id: str
    amount_usd: float
    status: str = "requested"  # requested|approved|rejected|paid
    method: str = "paypal"
    note: str = ""
    commission_ids: list[str] = field(default_factory=list)
    requested_at: datetime = field(default_factory=_now)
    processed_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "affiliateId": self.affiliate_id,
            "organizationId": self.organization_id,
            "amountUsd": round(self.amount_usd, 4),
            "status": self.status,
            "method": self.method,
            "note": self.note,
            "commissionIds": list(self.commission_ids),
            "requestedAt": _iso(self.requested_at),
            "processedAt": _iso(self.processed_at),
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class PayoutHistoryEntry:
    id: str
    payout_id: str
    affiliate_id: str
    organization_id: str
    action: str  # requested|approved|rejected|paid
    amount_usd: float = 0.0
    detail: str = ""
    actor_id: str | None = None
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "payoutId": self.payout_id,
            "affiliateId": self.affiliate_id,
            "organizationId": self.organization_id,
            "action": self.action,
            "amountUsd": round(self.amount_usd, 4),
            "detail": self.detail,
            "actorId": self.actor_id,
            "createdAt": _iso(self.created_at),
        }
