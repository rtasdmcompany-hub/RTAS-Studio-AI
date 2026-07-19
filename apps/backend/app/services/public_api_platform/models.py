"""Domain models for the public API platform & developer ecosystem."""

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
class DeveloperAccountRecord:
    id: str
    user_id: str
    organization_id: str
    display_name: str
    email: str = ""
    status: str = "active"
    company: str = ""
    website: str = ""
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "userId": self.user_id,
            "organizationId": self.organization_id,
            "displayName": self.display_name,
            "email": self.email,
            "status": self.status,
            "company": self.company,
            "website": self.website,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class ApiApplicationRecord:
    id: str
    developer_id: str
    organization_id: str
    name: str
    slug: str
    description: str = ""
    status: str = "active"
    homepage_url: str = ""
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "developerId": self.developer_id,
            "organizationId": self.organization_id,
            "name": self.name,
            "slug": self.slug,
            "description": self.description,
            "status": self.status,
            "homepageUrl": self.homepage_url,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class OAuthClientRecord:
    id: str
    developer_id: str
    application_id: str
    organization_id: str
    client_id: str
    client_secret_hash: str
    name: str
    redirect_uris: list[str] = field(default_factory=list)
    grant_types: list[str] = field(default_factory=list)
    scopes: list[str] = field(default_factory=list)
    status: str = "active"
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self, *, include_secret: bool = False, secret: str = "") -> dict[str, Any]:
        data = {
            "id": self.id,
            "developerId": self.developer_id,
            "applicationId": self.application_id,
            "organizationId": self.organization_id,
            "clientId": self.client_id,
            "name": self.name,
            "redirectUris": list(self.redirect_uris),
            "grantTypes": list(self.grant_types),
            "scopes": list(self.scopes),
            "status": self.status,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }
        if include_secret and secret:
            data["clientSecret"] = secret
        return data


@dataclass
class ApiTokenRecord:
    id: str
    developer_id: str
    organization_id: str
    application_id: str | None
    workspace_id: str | None
    name: str
    token_prefix: str
    token_hash: str
    scopes: list[str] = field(default_factory=list)
    status: str = "active"
    rate_limit_per_minute: int = 120
    last_used_at: datetime | None = None
    expires_at: datetime | None = None
    created_at: datetime = field(default_factory=_now)
    revoked_at: datetime | None = None

    def to_dict(self, *, include_token: bool = False, token: str = "") -> dict[str, Any]:
        data = {
            "id": self.id,
            "developerId": self.developer_id,
            "organizationId": self.organization_id,
            "applicationId": self.application_id,
            "workspaceId": self.workspace_id,
            "name": self.name,
            "tokenPrefix": self.token_prefix,
            "scopes": list(self.scopes),
            "status": self.status,
            "rateLimitPerMinute": self.rate_limit_per_minute,
            "lastUsedAt": _iso(self.last_used_at),
            "expiresAt": _iso(self.expires_at),
            "createdAt": _iso(self.created_at),
            "revokedAt": _iso(self.revoked_at),
        }
        if include_token and token:
            data["token"] = token
            data["tokenMasked"] = f"{token[:12]}…"
        return data


@dataclass
class ApiVersionRecord:
    id: str
    version: str
    status: str = "active"
    changelog: str = ""
    deprecated_at: datetime | None = None
    sunset_at: datetime | None = None
    compatibility: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "version": self.version,
            "status": self.status,
            "changelog": self.changelog,
            "deprecatedAt": _iso(self.deprecated_at),
            "sunsetAt": _iso(self.sunset_at),
            "compatibility": dict(self.compatibility),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class ApiUsageLogRecord:
    id: str
    developer_id: str
    organization_id: str
    token_id: str | None
    client_id: str | None
    surface: str
    method: str
    path: str
    status_code: int = 200
    latency_ms: float = 0.0
    version: str = "v1"
    workspace_id: str | None = None
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "developerId": self.developer_id,
            "organizationId": self.organization_id,
            "tokenId": self.token_id,
            "clientId": self.client_id,
            "surface": self.surface,
            "method": self.method,
            "path": self.path,
            "statusCode": self.status_code,
            "latencyMs": self.latency_ms,
            "version": self.version,
            "workspaceId": self.workspace_id,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class SdkReleaseRecord:
    id: str
    language: str
    version: str
    package_name: str
    download_url: str = ""
    checksum: str = ""
    changelog: str = ""
    status: str = "published"
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "language": self.language,
            "version": self.version,
            "packageName": self.package_name,
            "downloadUrl": self.download_url,
            "checksum": self.checksum,
            "changelog": self.changelog,
            "status": self.status,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class WebhookSubscriptionRecord:
    id: str
    developer_id: str
    organization_id: str
    application_id: str | None
    target_url: str
    events: list[str] = field(default_factory=list)
    secret_hash: str = ""
    status: str = "active"
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "developerId": self.developer_id,
            "organizationId": self.organization_id,
            "applicationId": self.application_id,
            "targetUrl": self.target_url,
            "events": list(self.events),
            "status": self.status,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }
