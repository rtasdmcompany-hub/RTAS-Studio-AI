"""Domain models for marketplace products, purchases, licenses, and reviews."""

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
class ProductVersion:
    id: str
    product_id: str
    version: str
    changelog: str = ""
    asset_uri: str = ""
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "productId": self.product_id,
            "version": self.version,
            "changelog": self.changelog,
            "assetUri": self.asset_uri,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class MarketplaceProduct:
    id: str
    organization_id: str
    seller_user_id: str
    name: str
    product_type: str
    description: str = ""
    category: str = "other"
    tags: list[str] = field(default_factory=list)
    status: str = "draft"  # draft|published|archived|deleted
    pricing_model: str = "free"  # free|premium
    price_credits: float = 0.0
    license_type: str = "personal"
    featured: bool = False
    workspace_id: str | None = None
    current_version: str = "1.0.0"
    asset_uri: str = ""
    views: int = 0
    downloads: int = 0
    purchases: int = 0
    refunds: int = 0
    revenue_credits: float = 0.0
    rating_sum: int = 0
    rating_count: int = 0
    metadata: dict[str, Any] = field(default_factory=dict)
    published_at: datetime | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    @property
    def avg_rating(self) -> float:
        return self.rating_sum / self.rating_count if self.rating_count else 0.0

    def to_dict(self, *, include_asset: bool = False) -> dict[str, Any]:
        data = {
            "id": self.id,
            "organizationId": self.organization_id,
            "sellerUserId": self.seller_user_id,
            "name": self.name,
            "productType": self.product_type,
            "description": self.description,
            "category": self.category,
            "tags": list(self.tags),
            "status": self.status,
            "pricingModel": self.pricing_model,
            "priceCredits": round(self.price_credits, 2),
            "licenseType": self.license_type,
            "featured": self.featured,
            "workspaceId": self.workspace_id,
            "currentVersion": self.current_version,
            "stats": {
                "views": self.views,
                "downloads": self.downloads,
                "purchases": self.purchases,
                "refunds": self.refunds,
                "revenueCredits": round(self.revenue_credits, 2),
                "avgRating": round(self.avg_rating, 2),
                "ratingCount": self.rating_count,
            },
            "metadata": dict(self.metadata),
            "publishedAt": _iso(self.published_at),
            "archivedAt": _iso(self.archived_at),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }
        if include_asset:
            data["assetUri"] = self.asset_uri
        return data


@dataclass
class Purchase:
    id: str
    product_id: str
    product_name: str
    buyer_user_id: str
    organization_id: str
    workspace_id: str | None = None
    price_credits: float = 0.0
    status: str = "completed"  # completed|refunded
    license_id: str = ""
    refunded_at: datetime | None = None
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "productId": self.product_id,
            "productName": self.product_name,
            "buyerUserId": self.buyer_user_id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "priceCredits": round(self.price_credits, 2),
            "status": self.status,
            "licenseId": self.license_id,
            "refundedAt": _iso(self.refunded_at),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class ProductLicense:
    id: str
    product_id: str
    purchase_id: str
    organization_id: str
    holder_user_id: str
    license_key: str
    license_type: str = "personal"
    status: str = "active"  # active|revoked
    workspace_id: str | None = None
    revoked_at: datetime | None = None
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "productId": self.product_id,
            "purchaseId": self.purchase_id,
            "organizationId": self.organization_id,
            "holderUserId": self.holder_user_id,
            "licenseKey": self.license_key,
            "licenseType": self.license_type,
            "status": self.status,
            "workspaceId": self.workspace_id,
            "revokedAt": _iso(self.revoked_at),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class DownloadGrant:
    token: str
    product_id: str
    license_id: str
    user_id: str
    expires_at: datetime
    used: bool = False
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "token": self.token,
            "productId": self.product_id,
            "licenseId": self.license_id,
            "userId": self.user_id,
            "expiresAt": _iso(self.expires_at),
            "used": self.used,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class ProductReview:
    id: str
    product_id: str
    reviewer_user_id: str
    organization_id: str
    rating: int
    title: str = ""
    body: str = ""
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "productId": self.product_id,
            "reviewerUserId": self.reviewer_user_id,
            "organizationId": self.organization_id,
            "rating": self.rating,
            "title": self.title,
            "body": self.body,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class AnalyticsEvent:
    id: str
    product_id: str
    event_type: str  # view|download|purchase|refund
    user_id: str | None = None
    organization_id: str | None = None
    amount_credits: float = 0.0
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "productId": self.product_id,
            "eventType": self.event_type,
            "userId": self.user_id,
            "organizationId": self.organization_id,
            "amountCredits": round(self.amount_credits, 2),
            "createdAt": _iso(self.created_at),
        }
