"""Domain models for creators, profiles, badges, followers, and publisher assets."""

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
class CreatorAccount:
    id: str
    user_id: str
    organization_id: str
    display_name: str
    status: str = "active"  # active|suspended
    verification_status: str = "unverified"  # unverified|pending|verified|rejected
    verified_at: datetime | None = None
    verification_note: str = ""
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    @property
    def verified(self) -> bool:
        return self.verification_status == "verified"

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "userId": self.user_id,
            "organizationId": self.organization_id,
            "displayName": self.display_name,
            "status": self.status,
            "verified": self.verified,
            "verificationStatus": self.verification_status,
            "verifiedAt": _iso(self.verified_at),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class CreatorProfile:
    id: str
    creator_id: str
    bio: str = ""
    avatar_uri: str = ""
    social_links: dict[str, str] = field(default_factory=dict)
    categories: list[str] = field(default_factory=list)
    portfolio: list[dict[str, Any]] = field(default_factory=list)
    featured_asset_ids: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "creatorId": self.creator_id,
            "bio": self.bio,
            "avatarUri": self.avatar_uri,
            "socialLinks": dict(self.social_links),
            "categories": list(self.categories),
            "portfolio": [dict(p) for p in self.portfolio],
            "featuredAssetIds": list(self.featured_asset_ids),
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class CreatorBadge:
    id: str
    creator_id: str
    badge_key: str
    label: str
    description: str = ""
    awarded_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "creatorId": self.creator_id,
            "badgeKey": self.badge_key,
            "label": self.label,
            "description": self.description,
            "awardedAt": _iso(self.awarded_at),
        }


@dataclass
class CreatorFollower:
    id: str
    creator_id: str
    follower_user_id: str
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "creatorId": self.creator_id,
            "followerUserId": self.follower_user_id,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class PublisherAsset:
    id: str
    organization_id: str
    creator_id: str
    owner_user_id: str
    name: str
    asset_type: str
    description: str = ""
    category: str = "other"
    tags: list[str] = field(default_factory=list)
    status: str = "draft"  # draft|scheduled|published|archived|deleted
    visibility: str = "public"  # public|organization|private
    current_version: str = "1.0.0"
    versions: list[dict[str, Any]] = field(default_factory=list)
    asset_uri: str = ""
    price_credits: float = 0.0
    publish_at: datetime | None = None
    published_at: datetime | None = None
    archived_at: datetime | None = None
    deleted_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self, *, include_asset_uri: bool = False) -> dict[str, Any]:
        data = {
            "id": self.id,
            "organizationId": self.organization_id,
            "creatorId": self.creator_id,
            "ownerUserId": self.owner_user_id,
            "name": self.name,
            "assetType": self.asset_type,
            "description": self.description,
            "category": self.category,
            "tags": list(self.tags),
            "status": self.status,
            "visibility": self.visibility,
            "currentVersion": self.current_version,
            "versions": [dict(v) for v in self.versions],
            "priceCredits": round(self.price_credits, 2),
            "publishAt": _iso(self.publish_at),
            "publishedAt": _iso(self.published_at),
            "archivedAt": _iso(self.archived_at),
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }
        if include_asset_uri:
            data["assetUri"] = self.asset_uri
        return data


@dataclass
class EngagementEvent:
    id: str
    creator_id: str
    event_type: str  # view|download|purchase|rating|review
    asset_id: str | None = None
    user_id: str | None = None
    amount_credits: float = 0.0
    rating: int = 0
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "creatorId": self.creator_id,
            "eventType": self.event_type,
            "assetId": self.asset_id,
            "userId": self.user_id,
            "amountCredits": round(self.amount_credits, 2),
            "rating": self.rating,
            "createdAt": _iso(self.created_at),
        }
