"""Domain models for the community platform & social collaboration engine."""

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
class UserProfile:
    id: str
    user_id: str
    organization_id: str
    display_name: str
    handle: str
    bio: str = ""
    avatar_uri: str = ""
    verified: bool = False
    verified_at: datetime | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "userId": self.user_id,
            "organizationId": self.organization_id,
            "displayName": self.display_name,
            "handle": self.handle,
            "bio": self.bio,
            "avatarUri": self.avatar_uri,
            "verified": self.verified,
            "verifiedAt": _iso(self.verified_at),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class FollowEdge:
    id: str
    organization_id: str
    follower_user_id: str
    target_user_id: str
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "followerUserId": self.follower_user_id,
            "targetUserId": self.target_user_id,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class Review:
    id: str
    organization_id: str
    asset_id: str
    author_user_id: str
    rating: int
    title: str = ""
    body: str = ""
    status: str = "visible"  # visible|flagged|removed
    asset_category: str = ""
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "assetId": self.asset_id,
            "authorUserId": self.author_user_id,
            "rating": self.rating,
            "title": self.title,
            "body": self.body,
            "status": self.status,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class RatingRecord:
    id: str
    organization_id: str
    asset_id: str
    user_id: str
    value: int
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "assetId": self.asset_id,
            "userId": self.user_id,
            "value": self.value,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class Comment:
    id: str
    organization_id: str
    subject_id: str  # e.g. asset id or creator id
    author_user_id: str
    body: str
    parent_id: str | None = None
    mentions: list[str] = field(default_factory=list)
    status: str = "visible"  # visible|flagged|removed
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "subjectId": self.subject_id,
            "authorUserId": self.author_user_id,
            "body": self.body if self.status != "removed" else "[removed]",
            "parentId": self.parent_id,
            "mentions": list(self.mentions),
            "status": self.status,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class Engagement:
    """Like / favorite / bookmark on an asset."""

    id: str
    organization_id: str
    asset_id: str
    user_id: str
    kind: str  # like|favorite|bookmark
    asset_category: str = ""
    asset_owner_user_id: str = ""
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "assetId": self.asset_id,
            "userId": self.user_id,
            "kind": self.kind,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class Notification:
    id: str
    organization_id: str
    recipient_user_id: str
    notification_type: str
    actor_user_id: str = ""
    subject_id: str = ""
    message: str = ""
    read: bool = False
    read_at: datetime | None = None
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "recipientUserId": self.recipient_user_id,
            "type": self.notification_type,
            "actorUserId": self.actor_user_id,
            "subjectId": self.subject_id,
            "message": self.message,
            "read": self.read,
            "readAt": _iso(self.read_at),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class ActivityEvent:
    id: str
    organization_id: str
    actor_user_id: str
    verb: str
    subject_id: str = ""
    detail: str = ""
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "actorUserId": self.actor_user_id,
            "verb": self.verb,
            "subjectId": self.subject_id,
            "detail": self.detail,
            "createdAt": _iso(self.created_at),
        }
