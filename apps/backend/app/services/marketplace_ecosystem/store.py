"""Thread-safe in-memory store for the marketplace ecosystem foundation."""

from __future__ import annotations

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from typing import TYPE_CHECKING, Any, Iterator

if TYPE_CHECKING:
    from app.services.marketplace_ecosystem.models import (
        AssetCollection,
        AssetVersion,
        Creator,
        EcosystemAsset,
    )

_lock = threading.RLock()

_creators: OrderedDict[str, "Creator"] = OrderedDict()
_creator_by_user: dict[tuple[str, str], str] = {}
_assets: OrderedDict[str, "EcosystemAsset"] = OrderedDict()
_versions: OrderedDict[str, "AssetVersion"] = OrderedDict()
_collections: OrderedDict[str, "AssetCollection"] = OrderedDict()

_op_timings: list[float] = []
_op_count = 0
_error_count = 0


def reset_store() -> None:
    global _op_count, _error_count
    with _lock:
        _creators.clear()
        _creator_by_user.clear()
        _assets.clear()
        _versions.clear()
        _collections.clear()
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
            "creators": len(_creators),
            "assets": len(_assets),
            "versions": len(_versions),
            "collections": len(_collections),
        }


# --- Creators ---


def save_creator(creator: "Creator") -> None:
    with _lock:
        _creators[creator.id] = creator
        _creator_by_user[(creator.organization_id, creator.user_id)] = creator.id


def get_creator(creator_id: str) -> "Creator | None":
    with _lock:
        return _creators.get(creator_id)


def get_creator_by_user(organization_id: str, user_id: str) -> "Creator | None":
    with _lock:
        cid = _creator_by_user.get((organization_id, user_id))
        return _creators.get(cid) if cid else None


def list_creators(*, organization_id: str | None = None) -> list["Creator"]:
    with _lock:
        items = [
            c
            for c in _creators.values()
            if organization_id is None or c.organization_id == organization_id
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items


# --- Assets ---


def save_asset(asset: "EcosystemAsset") -> None:
    with _lock:
        _assets[asset.id] = asset


def get_asset(asset_id: str) -> "EcosystemAsset | None":
    with _lock:
        return _assets.get(asset_id)


def list_assets(
    *,
    organization_id: str | None = None,
    creator_id: str | None = None,
    status: str | None = None,
    asset_type: str | None = None,
    category: str | None = None,
    include_deleted: bool = False,
    limit: int = 10_000,
) -> list["EcosystemAsset"]:
    with _lock:
        items = [
            a
            for a in _assets.values()
            if (organization_id is None or a.organization_id == organization_id)
            and (creator_id is None or a.creator_id == creator_id)
            and (status is None or a.status == status)
            and (asset_type is None or a.asset_type == asset_type)
            and (category is None or a.category == category)
            and (include_deleted or a.status != "deleted")
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items[:limit]


# --- Versions ---


def save_version(version: "AssetVersion") -> None:
    with _lock:
        _versions[version.id] = version


def list_versions(asset_id: str) -> list["AssetVersion"]:
    with _lock:
        items = [v for v in _versions.values() if v.asset_id == asset_id]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items


# --- Collections ---


def save_collection(collection: "AssetCollection") -> None:
    with _lock:
        _collections[collection.id] = collection


def get_collection(collection_id: str) -> "AssetCollection | None":
    with _lock:
        return _collections.get(collection_id)


def list_collections(*, organization_id: str | None = None) -> list["AssetCollection"]:
    with _lock:
        items = [
            c
            for c in _collections.values()
            if organization_id is None or c.organization_id == organization_id
        ]
        items.sort(key=lambda x: x.created_at, reverse=True)
        return items
