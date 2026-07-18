"""Domain models for enterprise notifications, comments & activity."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _iso(dt: datetime | None) -> str | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def new_id(prefix: str = "") -> str:
    return f"{prefix}{uuid4()}" if prefix else str(uuid4())


@dataclass
class Notification:
    id: str
    organization_id: str
    recipient_id: str
    type: str
    title: str
    body: str | None = None
    workspace_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    actor_id: str | None = None
    is_read: bool = False
    read_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "recipientId": self.recipient_id,
            "type": self.type,
            "title": self.title,
            "body": self.body,
            "resourceType": self.resource_type,
            "resourceId": self.resource_id,
            "actorId": self.actor_id,
            "isRead": self.is_read,
            "readAt": _iso(self.read_at),
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class NotificationPreference:
    id: str
    user_id: str
    organization_id: str | None = None
    channel_email: bool = True
    channel_in_app: bool = True
    muted_types: list[str] = field(default_factory=list)
    digests_enabled: bool = False
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "userId": self.user_id,
            "organizationId": self.organization_id,
            "channelEmail": self.channel_email,
            "channelInApp": self.channel_in_app,
            "mutedTypes": list(self.muted_types),
            "digestsEnabled": self.digests_enabled,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class Comment:
    id: str
    organization_id: str
    author_id: str
    resource_type: str
    resource_id: str
    body: str
    workspace_id: str | None = None
    is_pinned: bool = False
    is_resolved: bool = False
    reactions: dict[str, list[str]] = field(default_factory=dict)
    deleted_at: datetime | None = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "authorId": self.author_id,
            "resourceType": self.resource_type,
            "resourceId": self.resource_id,
            "body": self.body,
            "isPinned": self.is_pinned,
            "isResolved": self.is_resolved,
            "reactions": {k: list(v) for k, v in self.reactions.items()},
            "deletedAt": _iso(self.deleted_at),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class CommentReply:
    id: str
    comment_id: str
    author_id: str
    body: str
    deleted_at: datetime | None = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "commentId": self.comment_id,
            "authorId": self.author_id,
            "body": self.body,
            "deletedAt": _iso(self.deleted_at),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class Mention:
    id: str
    organization_id: str
    actor_id: str
    subject_type: str
    subject_id: str
    comment_id: str | None = None
    target_user_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "commentId": self.comment_id,
            "organizationId": self.organization_id,
            "actorId": self.actor_id,
            "subjectType": self.subject_type,
            "subjectId": self.subject_id,
            "targetUserId": self.target_user_id,
            "resourceType": self.resource_type,
            "resourceId": self.resource_id,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class ActivityEvent:
    id: str
    organization_id: str
    category: str
    action: str
    summary: str
    workspace_id: str | None = None
    actor_id: str | None = None
    resource_type: str | None = None
    resource_id: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "actorId": self.actor_id,
            "category": self.category,
            "action": self.action,
            "summary": self.summary,
            "resourceType": self.resource_type,
            "resourceId": self.resource_id,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class Announcement:
    id: str
    organization_id: str
    author_id: str
    title: str
    body: str
    workspace_id: str | None = None
    scope: str = "organization"
    is_pinned: bool = False
    published_at: datetime = field(default_factory=_utcnow)
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=_utcnow)
    updated_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "authorId": self.author_id,
            "title": self.title,
            "body": self.body,
            "scope": self.scope,
            "isPinned": self.is_pinned,
            "publishedAt": _iso(self.published_at),
            "expiresAt": _iso(self.expires_at),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class UserActivityLog:
    id: str
    user_id: str
    action: str
    organization_id: str | None = None
    workspace_id: str | None = None
    detail: str | None = None
    ip_hash: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "userId": self.user_id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "action": self.action,
            "detail": self.detail,
            "ipHash": self.ip_hash,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }
