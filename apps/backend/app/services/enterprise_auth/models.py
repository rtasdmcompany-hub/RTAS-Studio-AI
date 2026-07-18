"""Domain models for enterprise authentication & access control."""

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
    uid = str(uuid4())
    return f"{prefix}{uid}" if prefix else uid


@dataclass
class Session:
    id: str
    user_id: str
    organization_id: str | None = None
    workspace_id: str | None = None
    team_id: str | None = None
    role_key: str | None = None
    token: str = ""
    auth_provider: str = "credentials"  # credentials | sso | api_key
    sso_provider: str | None = None
    status: str = "active"
    expires_at: datetime = field(default_factory=_utcnow)
    created_at: datetime = field(default_factory=_utcnow)
    last_seen_at: datetime = field(default_factory=_utcnow)
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "userId": self.user_id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "teamId": self.team_id,
            "roleKey": self.role_key,
            "token": self.token,
            "authProvider": self.auth_provider,
            "ssoProvider": self.sso_provider,
            "status": self.status,
            "expiresAt": _iso(self.expires_at),
            "createdAt": _iso(self.created_at),
            "lastSeenAt": _iso(self.last_seen_at),
            "metadata": dict(self.metadata),
        }


@dataclass
class AccessContext:
    user_id: str
    organization_id: str
    role_key: str
    session_id: str | None = None
    workspace_id: str | None = None
    team_id: str | None = None
    permissions: list[str] = field(default_factory=list)
    is_owner: bool = False
    auth_provider: str = "credentials"

    def to_dict(self) -> dict[str, Any]:
        return {
            "userId": self.user_id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "teamId": self.team_id,
            "roleKey": self.role_key,
            "sessionId": self.session_id,
            "permissions": list(self.permissions),
            "isOwner": self.is_owner,
            "authProvider": self.auth_provider,
        }


@dataclass
class AuthAuditEvent:
    id: str
    event_type: str
    actor_id: str
    organization_id: str | None = None
    workspace_id: str | None = None
    success: bool = True
    detail: str = ""
    ip: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_utcnow)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "eventType": self.event_type,
            "actorId": self.actor_id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "success": self.success,
            "detail": self.detail,
            "ip": self.ip,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class SSOProviderConfig:
    key: str
    name: str
    enabled: bool = False
    protocol: str = "oidc"  # oidc | saml
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "enabled": self.enabled,
            "protocol": self.protocol,
            "metadata": dict(self.metadata),
            "ready": True,
        }
