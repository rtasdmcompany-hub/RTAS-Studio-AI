"""Enterprise Plugin Framework, Extension SDK & Third-Party Integration Engine — Phase 9 Sprint 5."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any

from app.services.plugin_framework import store
from app.services.plugin_framework.catalog import (
    DEFAULT_PLUGIN_PERMISSIONS,
    EVENT_BUS_CHANNELS,
    INTEGRATION_PROVIDERS,
    INTEGRATION_STATUSES,
    LIFECYCLE_HOOKS,
    PERMISSION_SCOPES,
    PLATFORM_VERSION,
    PLUGIN_STATUSES,
    PLUGIN_TYPES,
    check_compatibility,
    compute_signature,
    slugify,
    validate_manifest,
    verify_signature,
)
from app.services.plugin_framework.models import (
    InstalledPluginRecord,
    IntegrationConnectionRecord,
    IntegrationLogRecord,
    PluginConfigurationRecord,
    PluginEventRecord,
    PluginPermissionRecord,
    PluginRecord,
    PluginVersionRecord,
    new_id,
)
from app.services.plugin_framework.version import (
    ENGINE_LABEL,
    ENGINE_NAME,
    ENGINE_VERSION,
    PHASE,
    SPRINT,
)


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _validation():
    from app.services.multi_tenant.validation import ValidationError, require_non_empty

    return ValidationError, require_non_empty


def _auth_errors():
    from app.services.enterprise_auth.errors import ForbiddenError, NotFoundError

    return ForbiddenError, NotFoundError


def _require_access(**kwargs: Any) -> None:
    from app.services.enterprise_auth.middleware import require_access

    require_access(**kwargs)


def _audit(action: str, actor_id: str, detail: str | None = None, **meta: Any) -> None:
    from app.services.enterprise_auth.audit import log_auth_event

    log_auth_event(
        action, actor_id=actor_id, success=True, detail=detail or action, metadata=meta
    )


def _require_member(*, actor_id: str, organization_id: str) -> None:
    _require_access(
        user_id=actor_id, organization_id=organization_id, permission="org.read"
    )


def _require_manager(*, actor_id: str, organization_id: str) -> None:
    _require_access(
        user_id=actor_id, organization_id=organization_id, permission="org.update"
    )


def _emit_event(
    *,
    organization_id: str,
    plugin_id: str,
    event_type: str,
    actor: str = "",
    channel: str = "plugin.lifecycle",
    payload: dict[str, Any] | None = None,
) -> PluginEventRecord:
    event = PluginEventRecord(
        id=new_id("pev_"),
        organization_id=organization_id,
        plugin_id=plugin_id,
        event_type=event_type,
        channel=channel,
        payload=dict(payload or {}),
        actor_user_id=actor,
    )
    store.save_event(event)
    return event


class ExtensionSDKEngine:
    """SDK metadata, manifest validation, lifecycle hooks, event bus, configuration."""

    def sdk_metadata(self) -> dict[str, Any]:
        return {
            "sdkVersion": "1.0.0",
            "platformVersion": PLATFORM_VERSION,
            "pluginTypes": list(PLUGIN_TYPES),
            "permissions": list(DEFAULT_PLUGIN_PERMISSIONS),
            "lifecycleHooks": list(LIFECYCLE_HOOKS),
            "eventChannels": list(EVENT_BUS_CHANNELS),
            "sandboxReady": True,
            "manifestSchema": {
                "required": ["name", "version", "pluginType"],
                "optional": [
                    "description",
                    "permissions",
                    "minPlatformVersion",
                    "maxPlatformVersion",
                    "hooks",
                    "configSchema",
                ],
            },
        }

    def validate_manifest(self, manifest: dict[str, Any]) -> dict[str, Any]:
        errors = validate_manifest(manifest)
        compatible, reason = check_compatibility(manifest)
        return {
            "ok": len(errors) == 0,
            "valid": len(errors) == 0,
            "errors": errors,
            "compatible": compatible,
            "compatibilityReason": reason,
        }

    def verify_signature(
        self, manifest: dict[str, Any], signature: str, publisher_key: str = ""
    ) -> dict[str, Any]:
        valid = verify_signature(manifest, signature, publisher_key)
        return {"ok": True, "valid": valid, "expected": compute_signature(manifest, publisher_key)}

    def publish_event(
        self,
        payload: dict[str, Any],
        *,
        actor_id: str,
    ) -> dict[str, Any]:
        ValidationError, require_non_empty = _validation()
        org_id = str(require_non_empty(payload.get("organizationId"), "organizationId"))
        plugin_id = str(require_non_empty(payload.get("pluginId"), "pluginId"))
        _require_member(actor_id=actor_id, organization_id=org_id)
        channel = str(payload.get("channel") or "plugin.lifecycle")
        if channel not in EVENT_BUS_CHANNELS:
            raise ValidationError(f"unknown event channel: {channel}")
        event = _emit_event(
            organization_id=org_id,
            plugin_id=plugin_id,
            event_type=str(payload.get("eventType") or "custom"),
            actor=actor_id,
            channel=channel,
            payload=payload.get("payload") or {},
        )
        return {"ok": True, "event": event.to_dict()}

    def list_events(
        self,
        *,
        actor_id: str,
        organization_id: str,
        plugin_id: str | None = None,
        channel: str | None = None,
        limit: int = 50,
    ) -> dict[str, Any]:
        _require_member(actor_id=actor_id, organization_id=organization_id)
        events = store.list_events(
            organization_id=organization_id,
            plugin_id=plugin_id,
            channel=channel,
            limit=limit,
        )
        return {"ok": True, "count": len(events), "events": [e.to_dict() for e in events]}


class PluginPermissionEngine:
    """Plugin permission grants and isolation checks."""

    def grant_from_manifest(
        self,
        plugin: PluginRecord,
        installed: InstalledPluginRecord,
        *,
        scope: str = "organization",
    ) -> list[PluginPermissionRecord]:
        ValidationError, _ = _validation()
        if scope not in PERMISSION_SCOPES:
            raise ValidationError(f"unknown permission scope: {scope}")
        perms = plugin.manifest.get("permissions") or []
        granted: list[PluginPermissionRecord] = []
        for key in perms:
            if key not in DEFAULT_PLUGIN_PERMISSIONS:
                continue
            record = PluginPermissionRecord(
                id=new_id("ppr_"),
                plugin_id=plugin.id,
                installed_id=installed.id,
                permission_key=str(key),
                scope=scope,
            )
            store.save_permission(record)
            granted.append(record)
        return granted

    def list_for_installation(self, installed_id: str, *, actor_id: str) -> dict[str, Any]:
        installed = store.get_installation(installed_id)
        _, NotFoundError = _auth_errors()
        if installed is None:
            raise NotFoundError("installation not found")
        _require_member(
            actor_id=actor_id, organization_id=installed.organization_id
        )
        perms = store.list_permissions(installed_id=installed_id)
        return {
            "ok": True,
            "installedId": installed_id,
            "permissions": [p.to_dict() for p in perms],
        }

    def check(
        self,
        installed_id: str,
        permission_key: str,
        *,
        actor_id: str,
    ) -> dict[str, Any]:
        installed = store.get_installation(installed_id)
        _, NotFoundError = _auth_errors()
        if installed is None or installed.status == "uninstalled":
            raise NotFoundError("installation not found")
        _require_member(
            actor_id=actor_id, organization_id=installed.organization_id
        )
        perms = store.list_permissions(installed_id=installed_id)
        allowed = any(p.permission_key == permission_key and p.granted for p in perms)
        return {"ok": True, "allowed": allowed, "permissionKey": permission_key}


class PluginFrameworkEngine:
    """Plugin registration, update, delete, enable/disable, versioning."""

    def __init__(self) -> None:
        self.sdk = ExtensionSDKEngine()
        self.permissions = PluginPermissionEngine()

    def _get_for_write(self, plugin_id: str, *, actor_id: str) -> PluginRecord:
        ForbiddenError, NotFoundError = _auth_errors()
        plugin = store.get_plugin(plugin_id)
        if plugin is None:
            raise NotFoundError("plugin not found")
        if plugin.owner_user_id != actor_id:
            try:
                _require_manager(
                    actor_id=actor_id, organization_id=plugin.organization_id
                )
            except Exception:
                raise ForbiddenError("only the plugin owner can perform this action")
        return plugin

    def register(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            manifest = dict(payload.get("manifest") or {})
            validation = self.sdk.validate_manifest(manifest)
            if not validation["valid"]:
                raise ValidationError(
                    "; ".join(validation["errors"]) or "invalid manifest"
                )
            if not validation["compatible"]:
                raise ValidationError(validation["compatibilityReason"])
            signature = str(payload.get("signature") or "")
            publisher_key = str(payload.get("publisherKey") or "")
            if signature and not verify_signature(manifest, signature, publisher_key):
                raise ValidationError("plugin signature validation failed")
            if not signature:
                signature = compute_signature(manifest, publisher_key)
            name = str(manifest.get("name") or payload.get("name") or "")
            if not name:
                raise ValidationError("plugin name is required")
            plugin_type = str(
                manifest.get("pluginType") or manifest.get("type") or "custom"
            )
            if plugin_type not in PLUGIN_TYPES:
                raise ValidationError(f"unknown plugin type: {plugin_type}")
            version = str(manifest.get("version") or "1.0.0")
            plugin = PluginRecord(
                id=new_id("plg_"),
                organization_id=org_id,
                owner_user_id=actor_id,
                name=name,
                slug=slugify(name),
                plugin_type=plugin_type,
                description=str(
                    manifest.get("description") or payload.get("description") or ""
                ),
                status="registered",
                current_version=version,
                manifest=manifest,
                signature=signature,
                publisher_key=publisher_key,
                min_platform_version=str(
                    manifest.get("minPlatformVersion") or "1.0.0"
                ),
                max_platform_version=str(
                    manifest.get("maxPlatformVersion") or "99.99.99"
                ),
            )
            store.save_plugin(plugin)
            checksum = hashlib.sha256(
                f"{plugin.id}|{version}|{signature}".encode()
            ).hexdigest()
            store.save_version(
                PluginVersionRecord(
                    id=new_id("plv_"),
                    plugin_id=plugin.id,
                    version=version,
                    changelog="Initial release",
                    manifest=manifest,
                    signature=signature,
                    checksum=checksum,
                    compatibility={"platform": PLATFORM_VERSION, "compatible": True},
                    created_by=actor_id,
                )
            )
            _emit_event(
                organization_id=org_id,
                plugin_id=plugin.id,
                event_type="registered",
                actor=actor_id,
            )
            _audit("plugin_framework.registered", actor_id, name)
            return {"ok": True, "plugin": plugin.to_dict()}

    def get(self, plugin_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            _, NotFoundError = _auth_errors()
            plugin = store.get_plugin(plugin_id)
            if plugin is None:
                raise NotFoundError("plugin not found")
            _require_member(
                actor_id=actor_id, organization_id=plugin.organization_id
            )
            return {
                "ok": True,
                "plugin": plugin.to_dict(),
                "versions": [v.to_dict() for v in store.list_versions(plugin_id)],
            }

    def update(
        self, plugin_id: str, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, _ = _validation()
            plugin = self._get_for_write(plugin_id, actor_id=actor_id)
            if "description" in payload and payload["description"] is not None:
                plugin.description = str(payload["description"])
            if "status" in payload and payload["status"] is not None:
                status = str(payload["status"])
                if status not in PLUGIN_STATUSES:
                    raise ValidationError(f"unknown status: {status}")
                plugin.status = status
            if payload.get("manifest"):
                manifest = dict(payload["manifest"])
                validation = self.sdk.validate_manifest(manifest)
                if not validation["valid"]:
                    raise ValidationError(
                        "; ".join(validation["errors"]) or "invalid manifest"
                    )
                sig = str(payload.get("signature") or plugin.signature)
                if sig and not verify_signature(manifest, sig, plugin.publisher_key):
                    raise ValidationError("plugin signature validation failed")
                plugin.manifest = manifest
                plugin.signature = sig or compute_signature(manifest, plugin.publisher_key)
            plugin.updated_at = _now()
            store.save_plugin(plugin)
            _audit("plugin_framework.updated", actor_id, plugin.name)
            return {"ok": True, "plugin": plugin.to_dict()}

    def delete(self, plugin_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            plugin = self._get_for_write(plugin_id, actor_id=actor_id)
            active = store.list_installations(plugin_id=plugin_id)
            if any(i.status in ("installed", "enabled", "disabled") for i in active):
                ValidationError, _ = _validation()
                raise ValidationError(
                    "cannot delete plugin with active installations; uninstall first"
                )
            plugin.status = "deprecated"
            plugin.updated_at = _now()
            store.save_plugin(plugin)
            _audit("plugin_framework.deleted", actor_id, plugin.name)
            return {"ok": True, "pluginId": plugin_id, "status": "deprecated"}

    def publish_version(
        self, plugin_id: str, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            plugin = self._get_for_write(plugin_id, actor_id=actor_id)
            version = str(require_non_empty(payload.get("version"), "version"))
            from app.services.plugin_framework.catalog import is_semver

            if not is_semver(version):
                raise ValidationError("version must be semver")
            if store.get_version(plugin_id, version) is not None:
                raise ValidationError(f"version {version} already exists")
            manifest = dict(payload.get("manifest") or plugin.manifest)
            validation = self.sdk.validate_manifest(manifest)
            if not validation["valid"]:
                raise ValidationError("; ".join(validation["errors"]))
            sig = str(payload.get("signature") or compute_signature(manifest, plugin.publisher_key))
            if not verify_signature(manifest, sig, plugin.publisher_key):
                raise ValidationError("plugin signature validation failed")
            record = PluginVersionRecord(
                id=new_id("plv_"),
                plugin_id=plugin_id,
                version=version,
                changelog=str(payload.get("changelog") or ""),
                manifest=manifest,
                signature=sig,
                checksum=hashlib.sha256(f"{plugin_id}|{version}|{sig}".encode()).hexdigest(),
                compatibility={"platform": PLATFORM_VERSION},
                created_by=actor_id,
            )
            store.save_version(record)
            plugin.current_version = version
            plugin.manifest = manifest
            plugin.signature = sig
            plugin.updated_at = _now()
            store.save_plugin(plugin)
            _emit_event(
                organization_id=plugin.organization_id,
                plugin_id=plugin_id,
                event_type="version_published",
                actor=actor_id,
                payload={"version": version},
            )
            _audit("plugin_framework.version_published", actor_id, version)
            return {"ok": True, "version": record.to_dict()}


class PluginRegistryEngine:
    """Plugin catalog listing and discovery."""

    def list(
        self,
        *,
        actor_id: str,
        organization_id: str,
        plugin_type: str | None = None,
        status: str | None = None,
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            items = store.list_plugins(
                organization_id=organization_id,
                plugin_type=plugin_type,
                status=status,
            )
            items.sort(key=lambda p: p.created_at, reverse=True)
            return {
                "ok": True,
                "count": len(items),
                "plugins": [p.to_dict() for p in items],
            }


class PluginInstallationEngine:
    """Install, uninstall, enable, disable, update installed plugins."""

    def __init__(self, framework: PluginFrameworkEngine) -> None:
        self._framework = framework

    def install(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            plugin_id = str(require_non_empty(payload.get("pluginId"), "pluginId"))
            workspace_id = payload.get("workspaceId")
            ws_id = str(workspace_id) if workspace_id else None
            plugin = store.get_plugin(plugin_id)
            _, NotFoundError = _auth_errors()
            if plugin is None or plugin.status == "deprecated":
                raise NotFoundError("plugin not found")
            if plugin.organization_id != org_id:
                ForbiddenError, _ = _auth_errors()
                raise ForbiddenError("plugin belongs to a different organization")
            version = str(payload.get("version") or plugin.current_version)
            ver_record = store.get_version(plugin_id, version)
            if ver_record is None:
                raise ValidationError(f"version not found: {version}")
            compatible, reason = check_compatibility(plugin.manifest)
            if not compatible:
                raise ValidationError(reason)
            existing = store.get_installation_by_key(org_id, plugin_id, ws_id)
            if existing and existing.status != "uninstalled":
                raise ValidationError("plugin already installed for this scope")
            config = PluginConfigurationRecord(
                id=new_id("pcf_"),
                installed_id="",
                config=dict(payload.get("config") or {}),
                secrets_ref=str(payload.get("secretsRef") or ""),
            )
            installed = InstalledPluginRecord(
                id=new_id("ins_"),
                organization_id=org_id,
                workspace_id=ws_id,
                plugin_id=plugin_id,
                version=version,
                status="enabled",
                installed_by=actor_id,
                config_id=config.id,
            )
            config.installed_id = installed.id
            store.save_config(config)
            store.save_installation(installed)
            self._framework.permissions.grant_from_manifest(
                plugin,
                installed,
                scope="workspace" if ws_id else "organization",
            )
            _emit_event(
                organization_id=org_id,
                plugin_id=plugin_id,
                event_type="installed",
                actor=actor_id,
                payload={"version": version, "workspaceId": ws_id},
            )
            _audit("plugin_framework.installed", actor_id, plugin.name)
            return {"ok": True, "installation": installed.to_dict()}

    def uninstall(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            plugin_id = str(require_non_empty(payload.get("pluginId"), "pluginId"))
            ws_id = payload.get("workspaceId")
            workspace_id = str(ws_id) if ws_id else None
            installed = store.get_installation_by_key(org_id, plugin_id, workspace_id)
            if installed is None or installed.status == "uninstalled":
                raise ValidationError("plugin is not installed")
            installed.status = "uninstalled"
            installed.updated_at = _now()
            store.save_installation(installed)
            plugin = store.get_plugin(plugin_id)
            _emit_event(
                organization_id=org_id,
                plugin_id=plugin_id,
                event_type="uninstalled",
                actor=actor_id,
            )
            _audit(
                "plugin_framework.uninstalled",
                actor_id,
                plugin.name if plugin else plugin_id,
            )
            return {"ok": True, "installation": installed.to_dict()}

    def enable(self, install_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            installed = self._get_installation(install_id, actor_id=actor_id)
            installed.status = "enabled"
            installed.updated_at = _now()
            store.save_installation(installed)
            _emit_event(
                organization_id=installed.organization_id,
                plugin_id=installed.plugin_id,
                event_type="enabled",
                actor=actor_id,
            )
            return {"ok": True, "installation": installed.to_dict()}

    def disable(self, install_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            installed = self._get_installation(install_id, actor_id=actor_id)
            installed.status = "disabled"
            installed.updated_at = _now()
            store.save_installation(installed)
            _emit_event(
                organization_id=installed.organization_id,
                plugin_id=installed.plugin_id,
                event_type="disabled",
                actor=actor_id,
            )
            return {"ok": True, "installation": installed.to_dict()}

    def update_config(
        self, install_id: str, payload: dict[str, Any], *, actor_id: str
    ) -> dict[str, Any]:
        with store.timed_op():
            installed = self._get_installation(install_id, actor_id=actor_id)
            if not installed.config_id:
                ValidationError, _ = _validation()
                raise ValidationError("installation has no configuration")
            config = store.get_config(installed.config_id)
            assert config is not None
            config.config = dict(payload.get("config") or config.config)
            if "secretsRef" in payload:
                config.secrets_ref = str(payload.get("secretsRef") or "")
            config.updated_at = _now()
            store.save_config(config)
            _emit_event(
                organization_id=installed.organization_id,
                plugin_id=installed.plugin_id,
                event_type="config_changed",
                actor=actor_id,
                channel="plugin.config",
            )
            return {"ok": True, "configuration": config.to_dict()}

    def list_installed(
        self, *, actor_id: str, organization_id: str, workspace_id: str | None = None
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            items = store.list_installations(
                organization_id=organization_id, workspace_id=workspace_id
            )
            return {
                "ok": True,
                "count": len(items),
                "installations": [i.to_dict() for i in items],
            }

    def _get_installation(self, install_id: str, *, actor_id: str) -> InstalledPluginRecord:
        _, NotFoundError = _auth_errors()
        installed = store.get_installation(install_id)
        if installed is None or installed.status == "uninstalled":
            raise NotFoundError("installation not found")
        _require_member(
            actor_id=actor_id, organization_id=installed.organization_id
        )
        return installed


class ThirdPartyIntegrationEngine:
    """Third-party integration connections, logs, and webhooks."""

    def connect(self, payload: dict[str, Any], *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            ValidationError, require_non_empty = _validation()
            org_id = str(
                require_non_empty(payload.get("organizationId"), "organizationId")
            )
            _require_member(actor_id=actor_id, organization_id=org_id)
            provider = str(require_non_empty(payload.get("provider"), "provider"))
            if provider not in INTEGRATION_PROVIDERS:
                raise ValidationError(f"unknown integration provider: {provider}")
            ws_id = payload.get("workspaceId")
            workspace_id = str(ws_id) if ws_id else None
            display_name = str(payload.get("displayName") or provider.replace("_", " ").title())
            credentials_ref = str(payload.get("credentialsRef") or payload.get("accessTokenRef") or "")
            if not credentials_ref:
                raise ValidationError("credentialsRef is required for secure connection")
            conn = IntegrationConnectionRecord(
                id=new_id("int_"),
                organization_id=org_id,
                workspace_id=workspace_id,
                provider=provider,
                status="connected",
                display_name=display_name,
                credentials_ref=credentials_ref,
                metadata=dict(payload.get("metadata") or {}),
                connected_by=actor_id,
            )
            store.save_connection(conn)
            log = IntegrationLogRecord(
                id=new_id("ilog_"),
                connection_id=conn.id,
                event_type="connected",
                message=f"Connected to {provider}",
                success=True,
            )
            store.save_log(log)
            _emit_event(
                organization_id=org_id,
                plugin_id=conn.id,
                event_type="integration_connected",
                actor=actor_id,
                channel="integration.connected",
                payload={"provider": provider},
            )
            _audit("plugin_framework.integration_connected", actor_id, provider)
            return {"ok": True, "connection": conn.to_dict()}

    def list(
        self,
        *,
        actor_id: str,
        organization_id: str,
        workspace_id: str | None = None,
        provider: str | None = None,
    ) -> dict[str, Any]:
        with store.timed_op():
            _require_member(actor_id=actor_id, organization_id=organization_id)
            items = store.list_connections(
                organization_id=organization_id,
                workspace_id=workspace_id,
                provider=provider,
            )
            return {
                "ok": True,
                "count": len(items),
                "integrations": [c.to_dict() for c in items],
            }

    def disconnect(self, connection_id: str, *, actor_id: str) -> dict[str, Any]:
        with store.timed_op():
            conn = self._get_connection(connection_id, actor_id=actor_id)
            conn.status = "disconnected"
            conn.updated_at = _now()
            store.save_connection(conn)
            store.save_log(
                IntegrationLogRecord(
                    id=new_id("ilog_"),
                    connection_id=conn.id,
                    event_type="disconnected",
                    message=f"Disconnected from {conn.provider}",
                    success=True,
                )
            )
            _audit("plugin_framework.integration_disconnected", actor_id, conn.provider)
            return {"ok": True, "connectionId": connection_id, "status": "disconnected"}

    def logs(
        self, connection_id: str, *, actor_id: str, limit: int = 50
    ) -> dict[str, Any]:
        with store.timed_op():
            self._get_connection(connection_id, actor_id=actor_id)
            items = store.list_logs(connection_id, limit=limit)
            return {"ok": True, "count": len(items), "logs": [l.to_dict() for l in items]}

    def _get_connection(
        self, connection_id: str, *, actor_id: str
    ) -> IntegrationConnectionRecord:
        _, NotFoundError = _auth_errors()
        conn = store.get_connection(connection_id)
        if conn is None:
            raise NotFoundError("integration connection not found")
        _require_member(actor_id=actor_id, organization_id=conn.organization_id)
        return conn


class PluginFrameworkFacade:
    """Facade combining all plugin framework engines."""

    def __init__(self) -> None:
        self.framework = PluginFrameworkEngine()
        self.sdk = self.framework.sdk
        self.registry = PluginRegistryEngine()
        self.installation = PluginInstallationEngine(self.framework)
        self.permissions = self.framework.permissions
        self.integrations = ThirdPartyIntegrationEngine()

    def status(self) -> dict[str, Any]:
        return {
            "ok": True,
            "engine": ENGINE_NAME,
            "version": ENGINE_VERSION,
            "label": ENGINE_LABEL,
            "phase": PHASE,
            "sprint": SPRINT,
            "engines": {
                "pluginFramework": "ready",
                "extensionSdk": "ready",
                "pluginRegistry": "ready",
                "pluginInstallation": "ready",
                "pluginPermission": "ready",
                "thirdPartyIntegration": "ready",
            },
            "pluginTypes": list(PLUGIN_TYPES),
            "integrationProviders": list(INTEGRATION_PROVIDERS),
            "sdk": self.sdk.sdk_metadata(),
            "stats": store.metrics(),
        }


_service: PluginFrameworkFacade | None = None


def get_plugin_framework_service() -> PluginFrameworkFacade:
    global _service
    if _service is None:
        _service = PluginFrameworkFacade()
    return _service


def reset_engine() -> None:
    global _service
    store.reset_store()
    _service = None


get_engine = get_plugin_framework_service
