"""Plugin types, integrations, permissions, lifecycle hooks, and SDK policies."""

from __future__ import annotations

import hashlib
import hmac
import json
import re
from typing import Any, Final

PLUGIN_TYPES: Final[tuple[str, ...]] = (
    "ai_provider",
    "image_processing",
    "video_processing",
    "audio_processing",
    "automation",
    "storage",
    "analytics",
    "payment",
    "notification",
    "custom",
)

PLUGIN_STATUSES: Final[tuple[str, ...]] = ("registered", "published", "deprecated")

INSTALL_STATUSES: Final[tuple[str, ...]] = (
    "installed",
    "enabled",
    "disabled",
    "uninstalled",
)

INTEGRATION_PROVIDERS: Final[tuple[str, ...]] = (
    "google_drive",
    "dropbox",
    "onedrive",
    "github",
    "slack",
    "discord",
    "zapier",
    "make",
    "webhook",
    "custom",
)

INTEGRATION_STATUSES: Final[tuple[str, ...]] = (
    "connected",
    "disconnected",
    "error",
    "pending",
)

PERMISSION_SCOPES: Final[tuple[str, ...]] = ("organization", "workspace", "api")

DEFAULT_PLUGIN_PERMISSIONS: Final[tuple[str, ...]] = (
    "plugin.read",
    "plugin.write",
    "storage.read",
    "storage.write",
    "network.outbound",
    "events.publish",
    "events.subscribe",
    "config.read",
    "config.write",
)

LIFECYCLE_HOOKS: Final[tuple[str, ...]] = (
    "onInstall",
    "onEnable",
    "onDisable",
    "onUninstall",
    "onUpdate",
    "onConfigChange",
)

EVENT_BUS_CHANNELS: Final[tuple[str, ...]] = (
    "plugin.lifecycle",
    "plugin.config",
    "integration.connected",
    "integration.disconnected",
    "integration.event",
)

PLATFORM_VERSION: Final[str] = "1.0.0"
SIGNING_SECRET: Final[str] = "rtas-plugin-signing-v1"

_SEMVER_RE = re.compile(r"^\d+\.\d+\.\d+$")


def is_semver(value: str) -> bool:
    return bool(_SEMVER_RE.match(value or ""))


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", (value or "").lower()).strip("-")
    return slug or "plugin"


def canonical_manifest(manifest: dict[str, Any]) -> str:
    return json.dumps(manifest, sort_keys=True, separators=(",", ":"))


def compute_signature(manifest: dict[str, Any], publisher_key: str = "") -> str:
    from app.core.signing_secrets import plugin_signing_secret

    secret = plugin_signing_secret()
    payload = f"{canonical_manifest(manifest)}|{publisher_key or secret}"
    return hmac.new(
        secret.encode("utf-8"), payload.encode("utf-8"), hashlib.sha256
    ).hexdigest()


def verify_signature(
    manifest: dict[str, Any], signature: str, publisher_key: str = ""
) -> bool:
    if not signature:
        return False
    expected = compute_signature(manifest, publisher_key)
    return hmac.compare_digest(expected, signature)


def validate_manifest(manifest: dict[str, Any]) -> list[str]:
    """Return list of validation errors (empty = valid)."""
    errors: list[str] = []
    if not manifest.get("name"):
        errors.append("manifest.name is required")
    if not manifest.get("version"):
        errors.append("manifest.version is required")
    elif not is_semver(str(manifest["version"])):
        errors.append("manifest.version must be semver")
    plugin_type = manifest.get("pluginType") or manifest.get("type")
    if plugin_type and plugin_type not in PLUGIN_TYPES:
        errors.append(f"unknown plugin type: {plugin_type}")
    min_v = manifest.get("minPlatformVersion")
    if min_v and not is_semver(str(min_v)):
        errors.append("minPlatformVersion must be semver")
    perms = manifest.get("permissions") or []
    for p in perms:
        if str(p) not in DEFAULT_PLUGIN_PERMISSIONS:
            errors.append(f"unknown permission: {p}")
    return errors


def check_compatibility(
    manifest: dict[str, Any], platform_version: str = PLATFORM_VERSION
) -> tuple[bool, str]:
    min_v = str(manifest.get("minPlatformVersion") or "0.0.0")
    max_v = str(manifest.get("maxPlatformVersion") or "99.99.99")

    def _parse(v: str) -> tuple[int, ...]:
        return tuple(int(x) for x in v.split("."))

    plat = _parse(platform_version)
    if plat < _parse(min_v):
        return False, f"requires platform >= {min_v}"
    if plat > _parse(max_v):
        return False, f"requires platform <= {max_v}"
    return True, "compatible"
