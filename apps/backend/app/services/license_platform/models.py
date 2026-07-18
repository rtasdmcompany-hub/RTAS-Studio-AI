"""Domain models for licenses, API keys, tokens, rate limits, and webhooks."""

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
class License:
    id: str
    organization_id: str
    license_key: str
    tier: str = "free"
    status: str = "active"  # active|expired|suspended|revoked
    activated_at: datetime | None = None
    expires_at: datetime | None = None
    suspended_at: datetime | None = None
    revoked_at: datetime | None = None
    activated_by: str | None = None
    seats: int = 1
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self, *, mask_key: bool = True) -> dict[str, Any]:
        key = self.license_key
        if mask_key and len(key) > 9:
            key = f"{key[:9]}****-****-{key[-4:]}"
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "licenseKey": key,
            "tier": self.tier,
            "status": self.status,
            "activatedAt": _iso(self.activated_at),
            "expiresAt": _iso(self.expires_at),
            "suspendedAt": _iso(self.suspended_at),
            "revokedAt": _iso(self.revoked_at),
            "activatedBy": self.activated_by,
            "seats": self.seats,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class LicenseHistoryEntry:
    id: str
    license_id: str
    organization_id: str
    action: str  # activated|renewed|expired|suspended|resumed|revoked
    tier: str = ""
    detail: str = ""
    actor_id: str | None = None
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "licenseId": self.license_id,
            "organizationId": self.organization_id,
            "action": self.action,
            "tier": self.tier,
            "detail": self.detail,
            "actorId": self.actor_id,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class ApiKey:
    id: str
    organization_id: str
    key_type: str  # personal|organization|workspace
    access: str  # read_only|full_access|scoped
    name: str = ""
    key_prefix: str = ""
    key_hash: str = ""  # sha256 of the secret; plaintext never stored
    scopes: list[str] = field(default_factory=list)
    owner_user_id: str | None = None
    workspace_id: str | None = None
    active: bool = True
    last_used_at: datetime | None = None
    rotated_at: datetime | None = None
    revoked_at: datetime | None = None
    expires_at: datetime | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "keyType": self.key_type,
            "access": self.access,
            "name": self.name,
            "keyPrefix": self.key_prefix,
            "scopes": list(self.scopes),
            "ownerUserId": self.owner_user_id,
            "workspaceId": self.workspace_id,
            "active": self.active,
            "lastUsedAt": _iso(self.last_used_at),
            "rotatedAt": _iso(self.rotated_at),
            "revokedAt": _iso(self.revoked_at),
            "expiresAt": _iso(self.expires_at),
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class PersonalAccessToken:
    id: str
    user_id: str
    organization_id: str
    name: str = ""
    token_prefix: str = ""
    token_hash: str = ""
    scopes: list[str] = field(default_factory=list)
    active: bool = True
    last_used_at: datetime | None = None
    revoked_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "userId": self.user_id,
            "organizationId": self.organization_id,
            "name": self.name,
            "tokenPrefix": self.token_prefix,
            "scopes": list(self.scopes),
            "active": self.active,
            "lastUsedAt": _iso(self.last_used_at),
            "revokedAt": _iso(self.revoked_at),
            "expiresAt": _iso(self.expires_at),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class ApiUsageRecord:
    id: str
    organization_id: str
    api_key_id: str | None = None
    workspace_id: str | None = None
    endpoint: str = ""
    method: str = "GET"
    status_code: int = 200
    latency_ms: float = 0.0
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "apiKeyId": self.api_key_id,
            "workspaceId": self.workspace_id,
            "endpoint": self.endpoint,
            "method": self.method,
            "statusCode": self.status_code,
            "latencyMs": round(self.latency_ms, 3),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class RateLimitState:
    id: str
    organization_id: str
    scope: str  # organization|workspace|key
    scope_id: str
    tier: str = "free"
    per_minute: int = 0
    per_hour: int = 0
    per_day: int = 0
    minute_window: str = ""
    minute_count: int = 0
    hour_window: str = ""
    hour_count: int = 0
    day_window: str = ""
    day_count: int = 0
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "scope": self.scope,
            "scopeId": self.scope_id,
            "tier": self.tier,
            "limits": {
                "perMinute": self.per_minute,
                "perHour": self.per_hour,
                "perDay": self.per_day,
            },
            "usage": {
                "minute": self.minute_count,
                "hour": self.hour_count,
                "day": self.day_count,
            },
            "unlimited": self.per_minute == 0 and self.per_hour == 0 and self.per_day == 0,
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class Webhook:
    id: str
    organization_id: str
    url: str
    events: list[str] = field(default_factory=list)
    secret_hash: str = ""
    secret_prefix: str = ""
    active: bool = True
    created_by: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "url": self.url,
            "events": list(self.events),
            "secretPrefix": self.secret_prefix,
            "active": self.active,
            "createdBy": self.created_by,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class WebhookDelivery:
    id: str
    webhook_id: str
    organization_id: str
    event_type: str
    payload: dict[str, Any] = field(default_factory=dict)
    status: str = "pending"  # pending|delivered|failed|exhausted
    attempts: int = 0
    last_error: str = ""
    next_retry_at: datetime | None = None
    delivered_at: datetime | None = None
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "webhookId": self.webhook_id,
            "organizationId": self.organization_id,
            "eventType": self.event_type,
            "payload": dict(self.payload),
            "status": self.status,
            "attempts": self.attempts,
            "lastError": self.last_error,
            "nextRetryAt": _iso(self.next_retry_at),
            "deliveredAt": _iso(self.delivered_at),
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }
