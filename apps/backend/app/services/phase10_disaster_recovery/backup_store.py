"""In-memory backup snapshots for DR simulation & restore readiness."""

from __future__ import annotations

import copy
import threading
import time
from collections import OrderedDict
from typing import Any

_lock = threading.Lock()
_SNAPSHOTS: OrderedDict[str, dict[str, Any]] = OrderedDict()
_MAX = 100


def create_snapshot(
    category: str,
    payload: dict[str, Any],
    *,
    integrity: str = "ok",
) -> dict[str, Any]:
    snap_id = f"bak_{int(time.time() * 1000)}_{category[:12]}"
    entry = {
        "snapshotId": snap_id,
        "category": category,
        "createdAt": time.time(),
        "integrity": integrity,
        "payload": copy.deepcopy(payload),
        "bytesApprox": len(str(payload)),
    }
    with _lock:
        _SNAPSHOTS[snap_id] = entry
        while len(_SNAPSHOTS) > _MAX:
            _SNAPSHOTS.popitem(last=False)
    return entry


def list_snapshots(limit: int = 50) -> list[dict[str, Any]]:
    with _lock:
        items = list(_SNAPSHOTS.values())[-max(1, min(100, limit)) :]
        return [
            {
                "snapshotId": e["snapshotId"],
                "category": e["category"],
                "createdAt": e["createdAt"],
                "integrity": e["integrity"],
                "bytesApprox": e["bytesApprox"],
            }
            for e in reversed(items)
        ]


def get_snapshot(snapshot_id: str) -> dict[str, Any] | None:
    with _lock:
        return copy.deepcopy(_SNAPSHOTS.get(snapshot_id))


def restore_snapshot(snapshot_id: str) -> dict[str, Any]:
    snap = get_snapshot(snapshot_id)
    if not snap:
        raise ValueError(f"snapshot not found: {snapshot_id}")
    if snap.get("integrity") != "ok":
        raise ValueError(f"snapshot integrity failed: {snapshot_id}")
    return {
        "ok": True,
        "snapshotId": snapshot_id,
        "category": snap["category"],
        "restoredAt": time.time(),
        "payloadKeys": list((snap.get("payload") or {}).keys()),
    }


def verify_integrity() -> dict[str, Any]:
    with _lock:
        total = len(_SNAPSHOTS)
        ok = sum(1 for e in _SNAPSHOTS.values() if e.get("integrity") == "ok")
    return {
        "ok": total == 0 or ok == total,
        "total": total,
        "integrityOk": ok,
        "integrityFailed": total - ok,
    }


def clear() -> None:
    with _lock:
        _SNAPSHOTS.clear()


def statistics() -> dict[str, Any]:
    with _lock:
        by_cat: dict[str, int] = {}
        for e in _SNAPSHOTS.values():
            by_cat[e["category"]] = by_cat.get(e["category"], 0) + 1
        total = len(_SNAPSHOTS)
        ok = sum(1 for e in _SNAPSHOTS.values() if e.get("integrity") == "ok")
        return {
            "snapshotCount": total,
            "maxSnapshots": _MAX,
            "byCategory": by_cat,
            "ok": total == 0 or ok == total,
            "total": total,
            "integrityOk": ok,
            "integrityFailed": total - ok,
        }
