"""In-memory store for settings, activity logs, and management metrics."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import TYPE_CHECKING, Any

from app.services.org_management.version import MAX_ACTIVITY_LOGS

if TYPE_CHECKING:
    from app.services.org_management.models import (
        ActivityLog,
        OrganizationSettings,
        WorkspaceSettings,
    )

_lock = threading.RLock()
_org_settings: dict[str, "OrganizationSettings"] = {}
_ws_settings: dict[str, "WorkspaceSettings"] = {}
_activity: OrderedDict[str, "ActivityLog"] = OrderedDict()
_api_timings_ms: list[float] = []
_error_count = 0
_api_count = 0


def reset_store() -> None:
    global _error_count, _api_count
    with _lock:
        _org_settings.clear()
        _ws_settings.clear()
        _activity.clear()
        _api_timings_ms.clear()
        _error_count = 0
        _api_count = 0


def save_org_settings(settings: "OrganizationSettings") -> "OrganizationSettings":
    with _lock:
        _org_settings[settings.organization_id] = settings
        return settings


def get_org_settings(organization_id: str) -> "OrganizationSettings | None":
    with _lock:
        return _org_settings.get(organization_id)


def delete_org_settings(organization_id: str) -> None:
    with _lock:
        _org_settings.pop(organization_id, None)


def save_ws_settings(settings: "WorkspaceSettings") -> "WorkspaceSettings":
    with _lock:
        _ws_settings[settings.workspace_id] = settings
        return settings


def get_ws_settings(workspace_id: str) -> "WorkspaceSettings | None":
    with _lock:
        return _ws_settings.get(workspace_id)


def delete_ws_settings(workspace_id: str) -> None:
    with _lock:
        _ws_settings.pop(workspace_id, None)


def add_activity(log: "ActivityLog") -> "ActivityLog":
    with _lock:
        _activity[log.id] = log
        while len(_activity) > MAX_ACTIVITY_LOGS:
            _activity.popitem(last=False)
        return log


def list_activity(
    *,
    organization_id: str | None = None,
    workspace_id: str | None = None,
    team_id: str | None = None,
    limit: int = 50,
) -> list["ActivityLog"]:
    with _lock:
        items = list(_activity.values())
    items.reverse()
    if organization_id:
        items = [a for a in items if a.organization_id == organization_id]
    if workspace_id:
        items = [a for a in items if a.workspace_id == workspace_id]
    if team_id:
        items = [a for a in items if a.team_id == team_id]
    return items[: max(1, min(limit, 500))]


def record_api(duration_ms: float, *, error: bool = False) -> None:
    global _error_count, _api_count
    with _lock:
        _api_count += 1
        _api_timings_ms.append(duration_ms)
        if len(_api_timings_ms) > 1000:
            del _api_timings_ms[:200]
        if error:
            _error_count += 1


def metrics() -> dict[str, Any]:
    with _lock:
        timings = list(_api_timings_ms)
        avg = sum(timings) / len(timings) if timings else 0.0
        return {
            "apiCalls": _api_count,
            "errors": _error_count,
            "avgLatencyMs": round(avg, 2),
            "p95LatencyMs": round(sorted(timings)[int(len(timings) * 0.95)] if timings else 0.0, 2),
            "activityLogs": len(_activity),
            "orgSettings": len(_org_settings),
            "workspaceSettings": len(_ws_settings),
        }


class timed_op:
    """Context manager for API performance tracking."""

    def __init__(self) -> None:
        self._start = 0.0
        self.error = False

    def __enter__(self) -> "timed_op":
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        ms = (time.perf_counter() - self._start) * 1000
        record_api(ms, error=bool(exc_type) or self.error)
        return False
