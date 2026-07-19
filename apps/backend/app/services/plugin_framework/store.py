"""Thread-safe in-memory store for the plugin framework & integration engine."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from app.services.plugin_framework.models import (
        InstalledPluginRecord,
        IntegrationConnectionRecord,
        IntegrationLogRecord,
        PluginConfigurationRecord,
        PluginEventRecord,
        PluginPermissionRecord,
        PluginRecord,
        PluginVersionRecord,
    )

_lock = threading.RLock()

_plugins: OrderedDict[str, "PluginRecord"] = OrderedDict()
_versions: OrderedDict[str, "PluginVersionRecord"] = OrderedDict()
_installed: OrderedDict[str, "InstalledPluginRecord"] = OrderedDict()
_install_keys: dict[tuple[str, str, str | None], str] = {}
_permissions: OrderedDict[str, "PluginPermissionRecord"] = OrderedDict()
_configs: dict[str, "PluginConfigurationRecord"] = {}
_connections: OrderedDict[str, "IntegrationConnectionRecord"] = OrderedDict()
_logs: OrderedDict[str, "IntegrationLogRecord"] = OrderedDict()
_events: OrderedDict[str, "PluginEventRecord"] = OrderedDict()

_op_timings: list[float] = []
_op_count = 0
_error_count = 0


def reset_store() -> None:
    global _op_count, _error_count
    with _lock:
        for coll in (
            _plugins, _versions, _installed, _install_keys, _permissions,
            _configs, _connections, _logs, _events,
        ):
            coll.clear()
        _op_timings.clear()
        _op_count = 0
        _error_count = 0


def record_error() -> None:
    global _error_count
    with _lock:
        _error_count += 1


@contextmanager
def timed_op() -> Iterator[None]:
    global _op_count
    start = time.perf_counter()
    try:
        yield
    except Exception:
        record_error()
        raise
    finally:
        ms = (time.perf_counter() - start) * 1000
        with _lock:
            _op_timings.append(ms)
            if len(_op_timings) > 500:
                del _op_timings[: len(_op_timings) - 500]
            _op_count += 1


def metrics() -> dict[str, Any]:
    with _lock:
        timings = list(_op_timings)
        avg = sum(timings) / len(timings) if timings else 0.0
        return {
            "opCount": _op_count,
            "errorCount": _error_count,
            "avgLatencyMs": round(avg, 3),
            "plugins": len(_plugins),
            "versions": len(_versions),
            "installed": len(_installed),
            "permissions": len(_permissions),
            "configurations": len(_configs),
            "connections": len(_connections),
            "integrationLogs": len(_logs),
            "pluginEvents": len(_events),
        }


# --- Plugins ---


def save_plugin(plugin: "PluginRecord") -> None:
    with _lock:
        _plugins[plugin.id] = plugin


def get_plugin(plugin_id: str) -> "PluginRecord | None":
    with _lock:
        return _plugins.get(plugin_id)


def list_plugins(
    *,
    organization_id: str | None = None,
    plugin_type: str | None = None,
    status: str | None = None,
) -> list["PluginRecord"]:
    with _lock:
        return [
            p
            for p in _plugins.values()
            if (organization_id is None or p.organization_id == organization_id)
            and (plugin_type is None or p.plugin_type == plugin_type)
            and (status is None or p.status == status)
        ]


# --- Versions ---


def save_version(version: "PluginVersionRecord") -> None:
    with _lock:
        _versions[version.id] = version


def list_versions(plugin_id: str) -> list["PluginVersionRecord"]:
    with _lock:
        items = [v for v in _versions.values() if v.plugin_id == plugin_id]
        items.sort(key=lambda x: x.created_at)
        return items


def get_version(plugin_id: str, version: str) -> "PluginVersionRecord | None":
    with _lock:
        for v in _versions.values():
            if v.plugin_id == plugin_id and v.version == version:
                return v
        return None


# --- Installations ---


def save_installation(record: "InstalledPluginRecord") -> None:
    with _lock:
        _installed[record.id] = record
        _install_keys[
            (record.organization_id, record.plugin_id, record.workspace_id)
        ] = record.id


def get_installation(install_id: str) -> "InstalledPluginRecord | None":
    with _lock:
        return _installed.get(install_id)


def get_installation_by_key(
    organization_id: str, plugin_id: str, workspace_id: str | None
) -> "InstalledPluginRecord | None":
    with _lock:
        iid = _install_keys.get((organization_id, plugin_id, workspace_id))
        return _installed.get(iid) if iid else None


def list_installations(
    *,
    organization_id: str | None = None,
    workspace_id: str | None = None,
    plugin_id: str | None = None,
    include_uninstalled: bool = False,
) -> list["InstalledPluginRecord"]:
    with _lock:
        return [
            i
            for i in _installed.values()
            if (organization_id is None or i.organization_id == organization_id)
            and (workspace_id is None or i.workspace_id == workspace_id)
            and (plugin_id is None or i.plugin_id == plugin_id)
            and (include_uninstalled or i.status != "uninstalled")
        ]


# --- Permissions ---


def save_permission(perm: "PluginPermissionRecord") -> None:
    with _lock:
        _permissions[perm.id] = perm


def list_permissions(
    *, installed_id: str | None = None, plugin_id: str | None = None
) -> list["PluginPermissionRecord"]:
    with _lock:
        return [
            p
            for p in _permissions.values()
            if (installed_id is None or p.installed_id == installed_id)
            and (plugin_id is None or p.plugin_id == plugin_id)
        ]


# --- Configurations ---


def save_config(config: "PluginConfigurationRecord") -> None:
    with _lock:
        _configs[config.id] = config


def get_config(config_id: str) -> "PluginConfigurationRecord | None":
    with _lock:
        return _configs.get(config_id)


# --- Integrations ---


def save_connection(conn: "IntegrationConnectionRecord") -> None:
    with _lock:
        _connections[conn.id] = conn


def get_connection(connection_id: str) -> "IntegrationConnectionRecord | None":
    with _lock:
        return _connections.get(connection_id)


def list_connections(
    *,
    organization_id: str | None = None,
    workspace_id: str | None = None,
    provider: str | None = None,
) -> list["IntegrationConnectionRecord"]:
    with _lock:
        return [
            c
            for c in _connections.values()
            if (organization_id is None or c.organization_id == organization_id)
            and (workspace_id is None or c.workspace_id == workspace_id)
            and (provider is None or c.provider == provider)
            and c.status != "disconnected"
        ]


def save_log(log: "IntegrationLogRecord") -> None:
    with _lock:
        _logs[log.id] = log
        if len(_logs) > 50_000:
            _logs.popitem(last=False)


def list_logs(connection_id: str, *, limit: int = 100) -> list["IntegrationLogRecord"]:
    with _lock:
        items = [l for l in _logs.values() if l.connection_id == connection_id]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


# --- Event bus ---


def save_event(event: "PluginEventRecord") -> None:
    with _lock:
        _events[event.id] = event
        if len(_events) > 100_000:
            _events.popitem(last=False)


def list_events(
    *,
    organization_id: str | None = None,
    plugin_id: str | None = None,
    channel: str | None = None,
    limit: int = 100,
) -> list["PluginEventRecord"]:
    with _lock:
        items = [
            e
            for e in _events.values()
            if (organization_id is None or e.organization_id == organization_id)
            and (plugin_id is None or e.plugin_id == plugin_id)
            and (channel is None or e.channel == channel)
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]
