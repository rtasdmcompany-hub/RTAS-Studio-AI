"""Domain models for plugins, installations, permissions, integrations, and events."""

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
class PluginRecord:
    id: str
    organization_id: str
    owner_user_id: str
    name: str
    slug: str
    plugin_type: str
    description: str = ""
    status: str = "registered"
    current_version: str = "1.0.0"
    manifest: dict[str, Any] = field(default_factory=dict)
    signature: str = ""
    publisher_key: str = ""
    min_platform_version: str = "1.0.0"
    max_platform_version: str = "99.99.99"
    sandbox_ready: bool = True
    created_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "ownerUserId": self.owner_user_id,
            "name": self.name,
            "slug": self.slug,
            "pluginType": self.plugin_type,
            "description": self.description,
            "status": self.status,
            "currentVersion": self.current_version,
            "manifest": dict(self.manifest),
            "signatureVerified": bool(self.signature),
            "minPlatformVersion": self.min_platform_version,
            "maxPlatformVersion": self.max_platform_version,
            "sandboxReady": self.sandbox_ready,
            "createdAt": _iso(self.created_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class PluginVersionRecord:
    id: str
    plugin_id: str
    version: str
    changelog: str = ""
    manifest: dict[str, Any] = field(default_factory=dict)
    signature: str = ""
    checksum: str = ""
    compatibility: dict[str, Any] = field(default_factory=dict)
    created_by: str = ""
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "pluginId": self.plugin_id,
            "version": self.version,
            "changelog": self.changelog,
            "manifest": dict(self.manifest),
            "signature": self.signature,
            "checksum": self.checksum,
            "compatibility": dict(self.compatibility),
            "createdBy": self.created_by,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class InstalledPluginRecord:
    id: str
    organization_id: str
    workspace_id: str | None
    plugin_id: str
    version: str
    status: str = "installed"
    installed_by: str = ""
    config_id: str | None = None
    installed_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "pluginId": self.plugin_id,
            "version": self.version,
            "status": self.status,
            "installedBy": self.installed_by,
            "configId": self.config_id,
            "installedAt": _iso(self.installed_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class PluginPermissionRecord:
    id: str
    plugin_id: str
    installed_id: str
    permission_key: str
    scope: str = "organization"
    granted: bool = True
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "pluginId": self.plugin_id,
            "installedId": self.installed_id,
            "permissionKey": self.permission_key,
            "scope": self.scope,
            "granted": self.granted,
            "createdAt": _iso(self.created_at),
        }


@dataclass
class PluginConfigurationRecord:
    id: str
    installed_id: str
    config: dict[str, Any] = field(default_factory=dict)
    secrets_ref: str = ""
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self, *, include_secrets: bool = False) -> dict[str, Any]:
        data = {
            "id": self.id,
            "installedId": self.installed_id,
            "config": dict(self.config),
            "updatedAt": _iso(self.updated_at),
        }
        if include_secrets:
            data["secretsRef"] = self.secrets_ref
        return data


@dataclass
class IntegrationConnectionRecord:
    id: str
    organization_id: str
    workspace_id: str | None
    provider: str
    status: str = "connected"
    display_name: str = ""
    credentials_ref: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)
    connected_by: str = ""
    connected_at: datetime = field(default_factory=_now)
    updated_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "workspaceId": self.workspace_id,
            "provider": self.provider,
            "status": self.status,
            "displayName": self.display_name,
            "metadata": dict(self.metadata),
            "connectedBy": self.connected_by,
            "connectedAt": _iso(self.connected_at),
            "updatedAt": _iso(self.updated_at),
        }


@dataclass
class IntegrationLogRecord:
    id: str
    connection_id: str
    event_type: str
    message: str = ""
    success: bool = True
    metadata: dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "connectionId": self.connection_id,
            "eventType": self.event_type,
            "message": self.message,
            "success": self.success,
            "metadata": dict(self.metadata),
            "createdAt": _iso(self.created_at),
        }


@dataclass
class PluginEventRecord:
    id: str
    organization_id: str
    plugin_id: str
    event_type: str
    channel: str = "plugin.lifecycle"
    payload: dict[str, Any] = field(default_factory=dict)
    actor_user_id: str = ""
    created_at: datetime = field(default_factory=_now)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "organizationId": self.organization_id,
            "pluginId": self.plugin_id,
            "eventType": self.event_type,
            "channel": self.channel,
            "payload": dict(self.payload),
            "actorUserId": self.actor_user_id,
            "createdAt": _iso(self.created_at),
        }
