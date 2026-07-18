"""Thread-safe in-memory store for platform operations."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

from app.services.platform_ops.version import (
    DEFAULT_SUPER_ADMINS,
    MAX_ACTIVITY,
    MAX_LOGS,
    MAX_OPS_HISTORY,
)

if TYPE_CHECKING:
    from app.services.platform_ops.models import (
        AdminActivity,
        FeatureFlag,
        MaintenanceEvent,
        OperationsHistory,
        PlatformSetting,
        ScheduledTask,
        SystemConfiguration,
        SystemLog,
    )

_lock = threading.RLock()
_settings: OrderedDict[str, "PlatformSetting"] = OrderedDict()
_settings_by_key: dict[str, str] = {}
_configs: OrderedDict[str, "SystemConfiguration"] = OrderedDict()
_configs_by_ns: dict[str, str] = {}
_flags: OrderedDict[str, "FeatureFlag"] = OrderedDict()
_flags_by_key: dict[str, str] = {}
_maintenance: OrderedDict[str, "MaintenanceEvent"] = OrderedDict()
_activity: OrderedDict[str, "AdminActivity"] = OrderedDict()
_logs: OrderedDict[str, "SystemLog"] = OrderedDict()
_tasks: OrderedDict[str, "ScheduledTask"] = OrderedDict()
_tasks_by_name: dict[str, str] = {}
_ops: OrderedDict[str, "OperationsHistory"] = OrderedDict()
_super_admins: set[str] = set(DEFAULT_SUPER_ADMINS)
_cache: dict[str, Any] = {}
_services_status: dict[str, str] = {
    "api": "healthy",
    "workers": "healthy",
    "scheduler": "healthy",
    "cache": "healthy",
}

_api_timings: list[float] = []
_api_count = 0
_error_count = 0
_ops_events = 0
_seeded = False


def reset_store() -> None:
    global _api_count, _error_count, _ops_events, _seeded
    with _lock:
        _settings.clear()
        _settings_by_key.clear()
        _configs.clear()
        _configs_by_ns.clear()
        _flags.clear()
        _flags_by_key.clear()
        _maintenance.clear()
        _activity.clear()
        _logs.clear()
        _tasks.clear()
        _tasks_by_name.clear()
        _ops.clear()
        _super_admins.clear()
        _super_admins.update(DEFAULT_SUPER_ADMINS)
        _cache.clear()
        _services_status.update(
            {
                "api": "healthy",
                "workers": "healthy",
                "scheduler": "healthy",
                "cache": "healthy",
            }
        )
        _api_timings.clear()
        _api_count = 0
        _error_count = 0
        _ops_events = 0
        _seeded = False


@contextmanager
def timed_op() -> Iterator[None]:
    global _api_count
    start = time.perf_counter()
    try:
        yield
    except Exception:
        record_error()
        raise
    finally:
        ms = (time.perf_counter() - start) * 1000
        with _lock:
            _api_timings.append(ms)
            if len(_api_timings) > 500:
                del _api_timings[: len(_api_timings) - 500]
            _api_count += 1


def record_error() -> None:
    global _error_count
    with _lock:
        _error_count += 1


def mark_seeded() -> None:
    global _seeded
    with _lock:
        _seeded = True


def is_seeded() -> bool:
    with _lock:
        return _seeded


def add_super_admin(user_id: str) -> None:
    with _lock:
        _super_admins.add(user_id)


def is_super_admin(user_id: str) -> bool:
    with _lock:
        return user_id in _super_admins


def list_super_admins() -> list[str]:
    with _lock:
        return sorted(_super_admins)


def save_setting(s: "PlatformSetting") -> "PlatformSetting":
    with _lock:
        _settings[s.id] = s
        _settings_by_key[s.key] = s.id
        return s


def get_setting(key: str) -> "PlatformSetting | None":
    with _lock:
        sid = _settings_by_key.get(key)
        return _settings.get(sid) if sid else None


def list_settings() -> list["PlatformSetting"]:
    with _lock:
        return list(_settings.values())


def save_config(c: "SystemConfiguration") -> "SystemConfiguration":
    with _lock:
        _configs[c.id] = c
        _configs_by_ns[c.namespace] = c.id
        return c


def get_config(namespace: str) -> "SystemConfiguration | None":
    with _lock:
        cid = _configs_by_ns.get(namespace)
        return _configs.get(cid) if cid else None


def list_configs() -> list["SystemConfiguration"]:
    with _lock:
        return list(_configs.values())


def save_flag(f: "FeatureFlag") -> "FeatureFlag":
    with _lock:
        _flags[f.id] = f
        _flags_by_key[f.key] = f.id
        return f


def get_flag(key: str) -> "FeatureFlag | None":
    with _lock:
        fid = _flags_by_key.get(key)
        return _flags.get(fid) if fid else None


def list_flags() -> list["FeatureFlag"]:
    with _lock:
        return list(_flags.values())


def save_maintenance(m: "MaintenanceEvent") -> "MaintenanceEvent":
    with _lock:
        _maintenance[m.id] = m
        return m


def list_maintenance() -> list["MaintenanceEvent"]:
    with _lock:
        items = list(_maintenance.values())
    items.sort(key=lambda m: m.created_at, reverse=True)
    return items


def active_maintenance() -> "MaintenanceEvent | None":
    for m in list_maintenance():
        if m.status == "active":
            return m
    return None


def save_activity(a: "AdminActivity") -> "AdminActivity":
    with _lock:
        _activity[a.id] = a
        while len(_activity) > MAX_ACTIVITY:
            _activity.popitem(last=False)
        return a


def list_activity(limit: int = 100) -> list["AdminActivity"]:
    with _lock:
        items = list(_activity.values())
    items.sort(key=lambda a: a.created_at, reverse=True)
    return items[:limit]


def save_log(log: "SystemLog") -> "SystemLog":
    with _lock:
        _logs[log.id] = log
        while len(_logs) > MAX_LOGS:
            _logs.popitem(last=False)
        return log


def list_logs(*, level: str | None = None, limit: int = 100) -> list["SystemLog"]:
    with _lock:
        items = list(_logs.values())
    if level:
        items = [l for l in items if l.level == level]
    items.sort(key=lambda l: l.created_at, reverse=True)
    return items[:limit]


def save_task(t: "ScheduledTask") -> "ScheduledTask":
    with _lock:
        _tasks[t.id] = t
        _tasks_by_name[t.name] = t.id
        return t


def list_tasks() -> list["ScheduledTask"]:
    with _lock:
        return list(_tasks.values())


def save_ops(o: "OperationsHistory") -> "OperationsHistory":
    global _ops_events
    with _lock:
        _ops[o.id] = o
        _ops_events += 1
        while len(_ops) > MAX_OPS_HISTORY:
            _ops.popitem(last=False)
        return o


def list_ops(limit: int = 100) -> list["OperationsHistory"]:
    with _lock:
        items = list(_ops.values())
    items.sort(key=lambda o: o.created_at, reverse=True)
    return items[:limit]


def cache_set(key: str, value: Any) -> None:
    with _lock:
        _cache[key] = value


def cache_clear() -> int:
    with _lock:
        n = len(_cache)
        _cache.clear()
        return n


def cache_size() -> int:
    with _lock:
        return len(_cache)


def services_status() -> dict[str, str]:
    with _lock:
        return dict(_services_status)


def set_service_status(name: str, status: str) -> None:
    with _lock:
        _services_status[name] = status


def metrics() -> dict:
    with _lock:
        avg = sum(_api_timings) / len(_api_timings) if _api_timings else 0.0
        return {
            "apiCalls": _api_count,
            "avgLatencyMs": round(avg, 2),
            "errors": _error_count,
            "errorRate": round(_error_count / max(_api_count, 1), 4),
            "operationsEvents": _ops_events,
            "logCount": len(_logs),
            "flagCount": len(_flags),
            "settingCount": len(_settings),
            "cacheSize": len(_cache),
            "superAdminCount": len(_super_admins),
        }
