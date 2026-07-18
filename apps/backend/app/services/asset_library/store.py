"""Thread-safe in-memory store for asset library."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import TYPE_CHECKING, Any

from app.services.asset_library.version import MAX_ACTIVITY

if TYPE_CHECKING:
    from app.services.asset_library.models import (
        AssetActivity,
        AssetCollection,
        AssetPermission,
        AssetVersion,
        LibraryAsset,
    )

_lock = threading.RLock()
_assets: OrderedDict[str, "LibraryAsset"] = OrderedDict()
_versions: OrderedDict[str, "AssetVersion"] = OrderedDict()
_permissions: OrderedDict[str, "AssetPermission"] = OrderedDict()
_activity: OrderedDict[str, "AssetActivity"] = OrderedDict()
_collections: OrderedDict[str, "AssetCollection"] = OrderedDict()
_slug_index: dict[tuple[str, str], str] = {}
_perm_key: dict[tuple[str, str, str], str] = {}

_upload_ok = 0
_download_ok = 0
_search_timings: list[float] = []
_api_timings: list[float] = []
_api_count = 0
_error_count = 0


def reset_store() -> None:
    global _upload_ok, _download_ok, _api_count, _error_count
    with _lock:
        _assets.clear()
        _versions.clear()
        _permissions.clear()
        _activity.clear()
        _collections.clear()
        _slug_index.clear()
        _perm_key.clear()
        _search_timings.clear()
        _api_timings.clear()
        _upload_ok = 0
        _download_ok = 0
        _api_count = 0
        _error_count = 0


def save_asset(a: "LibraryAsset") -> "LibraryAsset":
    with _lock:
        _assets[a.id] = a
        _slug_index[(a.organization_id, a.slug)] = a.id
        return a


def get_asset(asset_id: str) -> "LibraryAsset | None":
    with _lock:
        return _assets.get(asset_id)


def get_by_slug(org_id: str, slug: str) -> "LibraryAsset | None":
    with _lock:
        aid = _slug_index.get((org_id, slug))
        return _assets.get(aid) if aid else None


def list_assets(
    *,
    organization_id: str | None = None,
    workspace_id: str | None = None,
    owner_id: str | None = None,
    asset_type: str | None = None,
    category: str | None = None,
    status: str | None = None,
    favorite_only: bool = False,
    include_deleted: bool = False,
) -> list["LibraryAsset"]:
    with _lock:
        items = list(_assets.values())
    if not include_deleted:
        items = [a for a in items if a.status != "deleted" and a.deleted_at is None]
    if organization_id:
        items = [a for a in items if a.organization_id == organization_id]
    if workspace_id:
        items = [a for a in items if a.workspace_id == workspace_id]
    if owner_id:
        items = [a for a in items if a.owner_id == owner_id]
    if asset_type:
        items = [a for a in items if a.asset_type == asset_type]
    if category:
        items = [a for a in items if a.category == category]
    if status:
        items = [a for a in items if a.status == status]
    if favorite_only:
        items = [a for a in items if a.is_favorite]
    return items


def delete_slug(org_id: str, slug: str) -> None:
    with _lock:
        _slug_index.pop((org_id, slug), None)


def save_version(v: "AssetVersion") -> "AssetVersion":
    with _lock:
        _versions[v.id] = v
        return v


def list_versions(asset_id: str) -> list["AssetVersion"]:
    with _lock:
        items = [v for v in _versions.values() if v.asset_id == asset_id]
    return sorted(items, key=lambda x: x.version, reverse=True)


def save_permission(p: "AssetPermission") -> "AssetPermission":
    with _lock:
        _permissions[p.id] = p
        _perm_key[(p.asset_id, p.subject_type, p.subject_id)] = p.id
        return p


def get_permission(
    asset_id: str, subject_type: str, subject_id: str
) -> "AssetPermission | None":
    with _lock:
        pid = _perm_key.get((asset_id, subject_type, subject_id))
        return _permissions.get(pid) if pid else None


def list_permissions(asset_id: str) -> list["AssetPermission"]:
    with _lock:
        return [p for p in _permissions.values() if p.asset_id == asset_id]


def add_activity(a: "AssetActivity") -> "AssetActivity":
    with _lock:
        _activity[a.id] = a
        while len(_activity) > MAX_ACTIVITY:
            _activity.popitem(last=False)
        return a


def list_activity(asset_id: str, *, limit: int = 50) -> list["AssetActivity"]:
    with _lock:
        items = [a for a in _activity.values() if a.asset_id == asset_id]
    items.reverse()
    return items[: max(1, min(limit, 500))]


def save_collection(c: "AssetCollection") -> "AssetCollection":
    with _lock:
        _collections[c.id] = c
        return c


def get_collection(collection_id: str) -> "AssetCollection | None":
    with _lock:
        return _collections.get(collection_id)


def list_collections(organization_id: str) -> list["AssetCollection"]:
    with _lock:
        return [c for c in _collections.values() if c.organization_id == organization_id]


def record_upload() -> None:
    global _upload_ok
    with _lock:
        _upload_ok += 1


def record_download() -> None:
    global _download_ok
    with _lock:
        _download_ok += 1


def record_search(ms: float) -> None:
    with _lock:
        _search_timings.append(ms)
        if len(_search_timings) > 1000:
            del _search_timings[:200]


def record_api(ms: float, *, error: bool = False) -> None:
    global _api_count, _error_count
    with _lock:
        _api_count += 1
        _api_timings.append(ms)
        if len(_api_timings) > 1000:
            del _api_timings[:200]
        if error:
            _error_count += 1


def metrics() -> dict[str, Any]:
    with _lock:
        assets = list(_assets.values())
        storage = sum(a.size_bytes for a in assets if a.status != "deleted")
        search = list(_search_timings)
        api = list(_api_timings)
        avg_search = sum(search) / len(search) if search else 0.0
        avg_api = sum(api) / len(api) if api else 0.0
        return {
            "totalAssets": sum(1 for a in assets if a.status != "deleted"),
            "storageUsageBytes": storage,
            "uploadSuccess": _upload_ok,
            "downloadSuccess": _download_ok,
            "versionCount": len(_versions),
            "activityEvents": len(_activity),
            "searchAvgMs": round(avg_search, 2),
            "apiCalls": _api_count,
            "avgLatencyMs": round(avg_api, 2),
            "errors": _error_count,
        }


class timed_op:
    def __enter__(self) -> "timed_op":
        self._start = time.perf_counter()
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        record_api((time.perf_counter() - self._start) * 1000, error=bool(exc_type))
        return False
